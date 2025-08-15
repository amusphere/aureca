import logging
import re
from datetime import datetime, timedelta

from pydantic import BaseModel
from sqlmodel import Session

from app.models.google_mail import DraftModel
from app.repositories.task_source import (
    create_task_source,
    get_task_source_by_source_id,
    get_task_source_by_uuid,
)
from app.repositories.tasks import create_task
from app.schema import SourceType, TaskPriority, TaskSource, User
from app.services.gmail_service import get_authenticated_gmail_service
from app.services.google_calendar_service import (
    CalendarFreeTimeResponse,
    get_authenticated_google_calendar_service,
)
from app.utils.llm import llm_chat_completions_perse


class TaskGenerationRequest(BaseModel):
    """LLMに送信するタスク生成リクエスト"""

    title: str
    description: str
    expires_at: float | None = None


class TaskGenerationResponse(BaseModel):
    """LLMからのタスク生成レスポンス"""

    title: str
    description: str
    expires_at: float | None = None
    priority: TaskPriority | None = None


class EmailReplyDraftResponse(BaseModel):
    """LLMからのメール返信下書きレスポンス"""

    subject: str
    body: str


class ScheduleJudgment(BaseModel):
    """スケジュール調整の必要性を判断するレスポンス"""

    needs_scheduling: bool


class AiTaskService:
    def __init__(self, session: Session, user_id: int):
        self.session = session
        self.user_id = user_id
        self.logger = logging.getLogger(__name__)

    async def generate_tasks_from_all_sources(self, user: User) -> dict:
        """
        全ての情報源からタスクを生成してデータベースに保存する

        Args:
            user: ユーザー情報

        Returns:
            サービス別の生成されたタスクの辞書
        """
        try:
            # メールからタスクを生成
            email_tasks = await self.generate_tasks_from_new_emails(user)

            # カレンダーからタスクを生成
            calendar_tasks = await self.generate_tasks_from_calendar_events(user)

            # サービス別にタスクを整理
            tasks_by_source = {"Gmail": email_tasks, "GoogleCalendar": calendar_tasks}

            return tasks_by_source

        except Exception as e:
            self.logger.error(f"全ての情報源からのタスク生成に失敗: {str(e)}")
            raise

    async def generate_tasks_from_new_emails(self, user: User, max_emails: int = 10) -> list[dict]:
        """
        新着メールを取得し、LLMでタスクを生成してデータベースに保存する

        Args:
            user: ユーザー情報
            max_emails: 取得する最大メール数

        Returns:
            生成されたタスクのリスト
        """
        try:
            # Gmailから新着メールを取得
            async with get_authenticated_gmail_service(user, self.session) as gmail_service:
                new_emails = await gmail_service.get_new_emails(max_results=max_emails)

            if not new_emails:
                self.logger.info("新着メールが見つかりませんでした")
                return []

            generated_tasks = []

            for email in new_emails:
                try:
                    email_id = email["id"]

                    # 既に同じsource_idでタスクが存在するかチェック
                    existing_task_source = get_task_source_by_source_id(
                        session=self.session,
                        source_id=email_id,
                        source_type=SourceType.EMAIL,
                    )

                    if existing_task_source:
                        self.logger.info(f"メール {email_id} は既にタスクが生成済みです。スキップします。")
                        continue

                    # メール内容を詳細取得
                    email_content = await self._get_email_detail(user, email_id)

                    # LLMでタスクを生成
                    task_data = await self._generate_task_from_email(email_content)

                    if task_data:
                        # データベースに保存
                        task = create_task(
                            session=self.session,
                            user_id=user.id,
                            title=task_data.title,
                            description=task_data.description,
                            expires_at=task_data.expires_at,
                            priority=task_data.priority,
                        )

                        # TaskSourceを作成（メール情報と直接リンクを保存）
                        gmail_url = self._generate_gmail_url(email_id)
                        create_task_source(
                            session=self.session,
                            task_id=task.id,
                            source_type=SourceType.EMAIL,
                            source_id=email_id,
                            title=email_content.get("subject", ""),
                            content=email_content.get("body", ""),
                            source_url=gmail_url,
                            extra_data=None,
                        )

                        generated_tasks.append(
                            {
                                "uuid": task.uuid,
                                "title": task.title,
                                "description": task.description,
                                "completed": task.completed,
                                "expires_at": task.expires_at,
                            }
                        )

                        self.logger.info(f"タスクを生成しました: {task.title}")

                except Exception as e:
                    self.logger.error(f"メール {email['id']} からのタスク生成に失敗: {str(e)}")
                    continue

            return generated_tasks

        except Exception as e:
            self.logger.error(f"新着メールからのタスク生成に失敗: {str(e)}")
            raise

    async def generate_tasks_from_calendar_events(
        self, user: User, days_ahead: int = 7, max_events: int = 20
    ) -> list[dict]:
        """
        カレンダーイベントからタスクを生成してデータベースに保存する

        Args:
            user: ユーザー情報
            days_ahead: 未来何日間のイベントを対象にするか
            max_events: 取得する最大イベント数

        Returns:
            生成されたタスクのリスト
        """
        try:
            # カレンダーから今後のイベントを取得
            async with get_authenticated_google_calendar_service(user, self.session) as calendar_service:
                # 現在から指定日数後までのイベントを取得
                start_date = datetime.now()
                end_date = start_date + timedelta(days=days_ahead)

                events = await calendar_service.get_events(
                    start_date=start_date,
                    end_date=end_date,
                    max_results=max_events,
                )

            if not events:
                self.logger.info("対象期間内にカレンダーイベントが見つかりませんでした")
                return []

            generated_tasks = []

            for event in events:
                try:
                    event_id = event.get("id", "")

                    # 既に同じsource_idでタスクが存在するかチェック
                    existing_task_source = get_task_source_by_source_id(
                        session=self.session,
                        source_id=event_id,
                        source_type=SourceType.CALENDAR,
                    )

                    if existing_task_source:
                        self.logger.info(f"カレンダーイベント {event_id} は既にタスクが生成済みです。スキップします。")
                        continue

                    # イベント内容からタスクを生成
                    task_data = await self._generate_task_from_calendar_event(event)

                    if task_data:
                        # データベースに保存
                        task = create_task(
                            session=self.session,
                            user_id=user.id,
                            title=task_data.title,
                            description=task_data.description,
                            expires_at=task_data.expires_at,
                            priority=task_data.priority,
                        )

                        # TaskSourceを作成（カレンダーイベント情報を保存）
                        html_link = event.get("htmlLink", "")  # Google Calendar APIの正式フィールド名

                        event_url = self._generate_calendar_event_url(event_id, html_link)

                        create_task_source(
                            session=self.session,
                            task_id=task.id,
                            source_type=SourceType.CALENDAR,
                            source_id=event_id,
                            title=event.get("summary", ""),
                            content=event.get("description", ""),
                            source_url=event_url,
                            extra_data=None,
                        )

                        generated_tasks.append(
                            {
                                "uuid": task.uuid,
                                "title": task.title,
                                "description": task.description,
                                "completed": task.completed,
                                "expires_at": task.expires_at,
                            }
                        )

                        self.logger.info(f"カレンダーイベントからタスクを生成しました: {task.title}")

                except Exception as e:
                    self.logger.error(
                        f"カレンダーイベント {event.get('id', 'unknown')} からのタスク生成に失敗: {str(e)}"
                    )
                    continue

            return generated_tasks

        except Exception as e:
            self.logger.error(f"カレンダーイベントからのタスク生成に失敗: {str(e)}")
            raise

    def _generate_gmail_url(self, email_id: str) -> str:
        """GmailメールIDから直接リンクURLを生成"""
        try:
            if not email_id or not email_id.strip():
                self.logger.warning("Empty email_id provided, using fallback URL")
                return "https://mail.google.com/mail/u/0/#inbox"

            # Gmail の新しいURL形式を使用
            gmail_url = f"https://mail.google.com/mail/u/0/#inbox/{email_id}"
            return gmail_url

        except Exception as e:
            self.logger.error(f"Error generating Gmail URL: {str(e)}")
            return "https://mail.google.com/mail/u/0/#inbox"

    async def _get_email_detail(self, user: User, email_id: str) -> dict:
        """メールの詳細情報を取得"""
        async with get_authenticated_gmail_service(user, self.session) as gmail_service:
            return await gmail_service.get_email_content(email_id)

    async def _generate_task_from_email(self, email_content: dict) -> TaskGenerationResponse | None:
        """
        メール内容からLLMを使ってタスクを生成

        Args:
            email_content: メールの詳細内容

        Returns:
            生成されたタスク情報、または None（タスクに適さない場合）
        """
        try:
            # メール情報を整理
            subject = email_content.get("subject", "")
            body = email_content.get("body", "")
            sender = email_content.get("from", "")
            date = email_content.get("date", "")

            # LLMへのプロンプトを作成
            prompts = [
                {
                    "role": "system",
                    "content": """あなたはメール内容を分析してタスクを生成するアシスタントです。
メール内容を分析し、以下の条件に当てはまる場合のみタスクを生成してください：

1. 具体的なアクション（返信、参加、提出、確認など）が必要
2. 期限がある、または緊急性がある
3. ユーザーが何かしらの行動を取る必要がある

タスクに適さない場合（単なる情報共有、広告、自動通知など）は、title を空文字列で返してください。

expires_at は UNIX タイムスタンプで返してください。期限が明確でない場合は null を返してください。

優先度判定基準（改良版）：
以下のキーワードや文脈を総合的に分析して優先度を判定してください：

【High優先度】- 即座に対応が必要
- 緊急時間表現: 今日中、今日まで、明日まで、24時間以内、数時間以内、午前中まで、夕方まで
- 緊急キーワード: 緊急、至急、急ぎ、ASAP、urgent、急いで、すぐに、即座に、クリティカル、critical
- 重要なビジネス: 重要な会議、重要な打ち合わせ、面接、プレゼンテーション、発表、締切、deadline、提出期限
- 業務への影響: 顧客対応、クライアント対応、トラブル対応、エスカレーション、問題解決、障害対応
- 権威・地位: 役員、部長、社長、CEO、重要な取引先、VIP、お客様からの、クライアントからの

【Middle優先度】- 計画的な対応が必要
- 期限のある業務: 今週中、来週まで、月末まで、数日以内、1週間以内
- 重要度キーワード: 重要、大切、確認してください、対応をお願いします、検討してください、準備してください
- 定例・継続業務: 会議、ミーティング、打ち合わせ、研修、セミナー、レビュー、報告書、企画、調査

【Low優先度】- 余裕をもって対応可能
- ゆとりある期限: 時間があるときに、いつでも結構です、お時間のあるときに、来月、将来的に
- 情報共有系: 参考まで、FYI、情報共有、連絡まで、お知らせ、ご報告、周知
- 任意性: ご都合の良いときに、可能であれば、もしよろしければ、お手すきの際に

【null優先度】- 判断材料不足または対応不要
- 単純な情報提供のみ、広告、自動通知、システム送信メール
- 緊急性・重要性を示すキーワードが一切含まれていない場合
- アクションが不明確または不要な場合

判定時は送信者の重要度、内容の緊急性、ビジネスへの影響度を総合的に考慮してください。
迷った場合は、より保守的（低い）優先度を選択してください。""",
                },
                {
                    "role": "system",
                    "content": """【出力仕様 / 制約 (EMAIL)】\n1. 出力は JSON（Pydantic Model TaskGenerationResponse）準拠: {\"title\": str, \"description\": str, \"expires_at\": number|null, \"priority\": 1|2|3|null } のみ。余計なキー・テキストを追加しない。\n2. priority 数値マッピング: High=1 / Middle=2 / Low=3 / 不要または判断不能=null。\n3. title: 具体的な行動を50文字以内。文末の句点は不要。抽象語(\"対応\"だけ等)を避ける。\n4. description: 120文字以内。何を・いつまでに・どうするか。元メールの本文全貼りや挨拶文は不要。\n5. expires_at: \n   - メール内に日時/期限表現があればそれを最も早い実行締切として UNIX秒 (UTC ではなくメールヘッダ上のタイムゾーンを優先し不明なら Asia/Tokyo) で設定。\n   - 相対表現（例: \"明日中\"）は: 現在日時を基準に具体化（明日 23:59:59 ローカル, 午前/午後指定あれば 09:00/15:00 など常識的補完）。\n   - 締切が複数ある場合: 最初に到来する実行必須のもの。\n   - 不明確 / 行動継続 / ルーチン / 期限未指定: null。推測で未来日時を捏造しない。\n6. タスクが複数必要そうでも 1件のみ: 最も緊急/重要かつユーザーアクションが明確なもの。\n7. 個人情報や機密らしき文言はそのまま再掲せず、必要なら抽象化（例: \"顧客A社資料\"→\"顧客資料\"）。\n8. ハルシネーション禁止: メールに無い日付・依頼者・URL・金額を作らない。\n9. 優先度判断は数値で返し、説明文中に High/Middle などのラベルを追加しない。\n10. 全フィールドは日本語。英語メールでも日本語要約で。\n""",
                },
                {
                    "role": "user",
                    "content": f"""以下のメール内容を分析してタスクを生成してください：

件名: {subject}
送信者: {sender}
日時: {date}
本文: {body}

適切なタスクのタイトル、説明、期限、優先度を生成してください。
優先度は緊急性や重要性のキーワードに基づいて判定してください。""",
                },
            ]

            # LLMでタスクを生成
            response = llm_chat_completions_perse(
                prompts=prompts,
                response_format=TaskGenerationResponse,
                temperature=0.2,  # 優先度判定の一貫性向上
                max_tokens=500,
            )

            # タスクに適さない場合（titleが空）は None を返す
            if not response.title.strip():
                return None

            # 優先度判定結果をログ出力
            self.logger.info(
                f"Generated task from email - Title: {response.title[:50]}..., Priority: {response.priority}"
            )

            return response

        except Exception as e:
            self.logger.error(f"LLMでのタスク生成に失敗: {str(e)}")
            return None

    def _parse_date_to_timestamp(self, date_str: str) -> float | None:
        """日付文字列をタイムスタンプに変換"""
        try:
            # 一般的な日付形式を解析
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%Y/%m/%d %H:%M:%S",
                "%Y/%m/%d",
                "%m/%d/%Y",
                "%d/%m/%Y",
            ]

            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.timestamp()
                except ValueError:
                    continue

            return None

        except Exception:
            return None

    async def _generate_task_from_calendar_event(self, event: dict) -> TaskGenerationResponse | None:
        """
        カレンダーイベント内容からLLMを使ってタスクを生成

        Args:
            event: カレンダーイベントの詳細内容

        Returns:
            生成されたタスク情報、または None（タスクに適さない場合）
        """
        try:
            # イベント情報を整理
            summary = event.get("summary", "")
            description = event.get("description", "")
            location = event.get("location", "")
            start_time = event.get("start", {})
            end_time = event.get("end", {})

            # 開始時刻と終了時刻の文字列を取得
            start_str = start_time.get("dateTime", start_time.get("date", ""))
            end_str = end_time.get("dateTime", end_time.get("date", ""))

            # LLMへのプロンプトを作成
            prompts = [
                {
                    "role": "system",
                    "content": """あなたはカレンダーイベントを分析してタスクを生成するアシスタントです。
カレンダーイベントを分析し、基本的にすべての予定からタスクを生成してください。

以下のようなイベントからタスクを生成してください：
1. 会議・MTG・ミーティング・打ち合わせ（事前確認や参加準備のため）
2. プレゼンテーション・発表（資料作成や準備のため）
3. 面接・面談（事前準備のため）
4. セミナー・研修・勉強会（事前学習や準備のため）
5. イベント・パーティー（準備や確認のため）
6. フライト・電車・交通機関（チェックイン、荷物準備、交通手段確認のため）
7. 旅行・出張（準備、持ち物確認、予約確認のため）
8. 医療予約・健康診断（必要書類準備、事前準備のため）
9. 重要な個人イベント（誕生日、記念日の準備など）
10. スポーツ・フィットネス（装備準備、場所確認のため）
11. 学習・試験（事前勉強、準備のため）
12. アポイントメント全般（事前確認や準備のため）

以下の場合のみ、title を空文字列で返してください：
- 明らかにブロック用途の予定（「busy」「ブロック」「Block」「時間確保」など）
- 単なる作業時間の確保（「作業時間」「開発時間」「集中時間」など）
- 食事のみの予定（「ランチ」「昼食」「夕食」のみで詳細がない場合）
- 明らかに個人的な休憩時間（「休憩」「Break」のみ）
- 重複や自動生成された無意味なイベント

タスクのタイトルは具体的な行動を示してください：
- 「〜の準備」「〜への参加準備」「〜の事前確認」
- 「〜のチェックイン」「〜の荷物準備」「〜の予約確認」
- 「〜の持ち物確認」「〜の資料準備」

【重要: expires_at（期限）生成ルール】
必ず expires_at（UNIXタイムスタンプ, 秒）を設定してください（除外条件で title を空にする場合のみ null 可）。

1. 会議/ミーティング/打ち合わせ/MTG/1on1/定例/レビュー など一般的なミーティング系イベント:
    - 期限 = イベント開始時刻（オフセットを付けない）

2. 明確に事前準備・移動が必要なイベントのみ前倒し（準備が曖昧なら前倒ししない）:
    - フライト/長距離移動/国際線/出張/flight: 開始120分前
    - 面接/面談/インタビュー/プレゼン/発表/登壇/試験/資格/重要プレゼン: 開始60分前
    - ワークショップ/研修/トレーニング/勉強会/セミナー（資料や環境準備が暗示される場合）: 開始30分前

3. 終日 (all-day, date フィールド) イベント:
    - 期限 = 当日 09:00（特別な準備語が含まれていて前日準備が必須と明確な場合のみ前日18:00 を選択可）

4. 前倒し計算の結果が現在時刻より過去になる場合: 期限 = 開始時刻

5. どの前倒し条件にも自信が持てない場合: 期限 = 開始時刻（不要な推測で早めすぎない）

これらのルールを守り、不要に早すぎる期限を設定しないでください。

優先度判定基準（改良版）：
イベントの種類、重要性、参加者、ビジネス影響度を総合的に分析して優先度を決定してください：

【High優先度】- 重要度・緊急度が極めて高いイベント
- 重要なビジネス: 重要な会議、役員会議、取締役会、株主総会、重要な打ち合わせ、クライアント会議、プレゼンテーション
- キャリア関連: 面接、面談、評価面談、人事面談、昇進面談、転職関連面談
- 公的・発表系: 重要な発表、講演、デモンストレーション、重要な報告会、記者会見
- 期限・締切: 提出期限、納期、契約期限、重要なdeadline関連イベント
- 交通・移動: フライト、新幹線、重要な移動、国際線、重要な出張
- 医療・健康: 医療予約、手術、重要な健康診断、緊急診察、専門医診察
- 試験・資格: 重要な試験、資格試験、認定試験、入学試験、昇進試験

【Middle優先度】- 標準的な重要度のイベント
- 日常業務: 一般的な会議、定例会議、ミーティング、チーム会議、進捗会議、1on1
- 学習・研修: セミナー、研修、勉強会、ワークショップ、講習会、トレーニング
- 一般出張・移動: 通常の出張、移動、交通機関利用、営業訪問
- 運動・健康: ジム、フィットネス、スポーツ、運動、トレーニング、定期検診
- イベント参加: 展示会、カンファレンス、説明会、見学会、ネットワーキング
- 個人的重要: 家族イベント、記念日、誕生日、結婚式、お祝い事

【Low優先度】- 軽度の重要度・任意性の高いイベント
- 個人的時間: 個人的な食事、友人との食事、カジュアルな集まり、趣味の時間
- 定期・ルーチン: 定期検診、日常の買い物、散髪、美容院、メンテナンス
- 余暇・娯楽: 映画鑑賞、読書時間、休憩時間、エンターテイメント、趣味活動
- 非必須参加: 任意参加のイベント、オプショナルな集まり、懇親会

【null優先度】- 判断不可能またはタスク生成対象外
- ブロック用途: 「busy」「ブロック」「Block」「時間確保」「予約ブロック」
- 作業専用時間: 「作業時間」「開発時間」「集中時間」「コーディング時間」のみ
- 詳細情報不足: 情報が不十分で判断できない、内容が不明確
- システム生成: 自動生成された予定、重複、無意味な予定

判定時は以下を重視してください：
1. ビジネスへの影響度と重要度
2. 参加者の地位・権威性
3. イベントの緊急性・期限性
4. 準備の必要性と複雑さ
5. 失敗時のリスクの大きさ

企業環境では business context を最優先し、判断に迷った場合は middle を選択してください。

【出力フォーマット注意】
JSON構造に strict 準拠し、"expires_at" には秒単位のUNIXエポック(小数可)を設定。生成不能な場合のみ null。""",
                },
                {
                    "role": "system",
                    "content": """【出力仕様 / 制約 (CALENDAR)】\n1. 出力は JSON（TaskGenerationResponse）: {title, description, expires_at, priority} のみ。追加テキスト禁止。\n2. priority 数値マッピング: High=1 / Middle=2 / Low=3 / 判断不能=null。\n3. title: 50文字以内で行動指向。イベント名の単純コピーを避け、準備/確認/参加など動詞を含める。\n4. description: 120文字以内。準備物 / 確認事項 / ゴール を簡潔に。長いイベント説明丸写し禁止。\n5. expires_at: 直前ルール（既述）に従い UNIX秒 (startがタイムゾーン付きISOならそのTZ、無ければイベントのローカルを Asia/Tokyo と仮定)。\n6. all-day の場合: 09:00 (前日準備明確なら前日18:00)。過度な前倒し禁止。\n7. イベントが完了後フォローアップを明確に要求する (例: \"議事録送付\") 以外は事前準備タスクに限定。\n8. ハルシネーション禁止: イベントに存在しない URL / 参加者 / ロケーション / 時刻を創作しない。\n9. 複合イベントでも 1タスク。最も事前準備価値の高いアクションを選ぶ。\n10. 優先度はイベントのビジネス影響 > 緊急性 > 準備複雑度の順で総合。迷えば2。\n""",
                },
                {
                    "role": "user",
                    "content": f"""以下のカレンダーイベントを分析してタスクを生成してください：

イベント名: {summary}
説明: {description}
場所: {location}
開始時刻: {start_str}
終了時刻: {end_str}

このイベントに関連して、事前準備やフォローアップのための適切なタスクのタイトル、説明、期限、優先度を生成してください。
優先度はイベントの種類と重要性に基づいて判定してください。""",
                },
            ]

            # LLMでタスクを生成
            response = llm_chat_completions_perse(
                prompts=prompts,
                response_format=TaskGenerationResponse,
                temperature=0.2,  # 優先度判定の一貫性向上
                max_tokens=500,
            )

            # タスクに適さない場合（titleが空）は None を返す
            if not response.title.strip():
                return None

            # 期限が未設定の場合はフォールバックで算出
            if response.expires_at is None:
                fallback_due = self._fallback_calendar_due(summary, start_str)
                if fallback_due:
                    self.logger.info(
                        "LLM未提供のためカレンダーイベント期限をフォールバック設定: %s -> %s",
                        summary,
                        datetime.fromtimestamp(fallback_due).isoformat(),
                    )
                    response.expires_at = fallback_due

            # 優先度判定結果をログ出力
            self.logger.info(
                f"Generated task from calendar event - Title: {response.title[:50]}..., Priority: {response.priority}"
            )

            return response

        except Exception as e:
            self.logger.error(f"LLMでのカレンダータスク生成に失敗: {str(e)}")
            return None

    def _fallback_calendar_due(self, summary: str, start_str: str) -> float | None:
        """LLM が期限を返さなかった際にイベント開始時刻から期限を推定して返す。

        ルール:
        - start_str が ISO8601 datetime の場合: 種類により 30〜120 分前
        - フライト/飛行機/新幹線/出張/flight: 120 分前
        - 面接/面談/インタビュー/プレゼン/発表/試験/試験/資格/登壇: 60 分前
        - 会議/mtg/meeting/ミーティング/打ち合わせ/1on1/レビュー/勉強会/研修: 30 分前
        - その他: 30 分前
        - all-day(date のみ) は その日 09:00 ローカル (タイムゾーン情報無しならシステムローカル) を期限
        - 計算した期限が現在時刻より過去の場合は start 時刻を期限にする
        """
        if not start_str:
            return None

        try:
            dt: datetime | None = None
            if len(start_str) == 10 and start_str.count("-") == 2:  # YYYY-MM-DD (all-day)
                # All-day event: set due at 09:00 local time
                try:
                    base = datetime.fromisoformat(start_str)
                except ValueError:
                    return None
                dt = base.replace(hour=9, minute=0, second=0, microsecond=0)
            else:
                # datetime with time / timezone
                try:
                    dt = datetime.fromisoformat(start_str)
                except ValueError:
                    return None

            if dt is None:
                return None

            summary_lower = summary.lower()
            offset_minutes = 30
            keywords_120 = ["flight", "フライト", "飛行機", "新幹線", "出張", "shinkansen"]
            keywords_60 = [
                "面接",
                "面談",
                "interview",
                "インタビュー",
                "プレゼン",
                "presentation",
                "発表",
                "登壇",
                "試験",
                "exam",
                "資格",
                "試験",
            ]
            # 30分前準備が適切になり得るイベント（資料準備などが暗示されるケース）
            keywords_30 = [
                "ワークショップ",
                "workshop",
                "研修",
                "トレーニング",
                "勉強会",
                "セミナー",
            ]
            # オフセットを付けず開始時刻そのままを期限にするイベント（一般会議等）
            keywords_0 = [
                "会議",
                "打ち合わせ",
                "mtg",
                "meeting",
                "ミーティング",
                "1on1",
                "レビュー",
            ]

            if any(k in summary_lower for k in keywords_120):
                offset_minutes = 120
            elif any(k in summary_lower for k in keywords_60):
                offset_minutes = 60
            elif any(k in summary_lower for k in keywords_30):
                offset_minutes = 30
            elif any(k in summary_lower for k in keywords_0):
                offset_minutes = 0
            else:
                # その他は開始時刻をデフォルト（準備が必要そうなら 30分前だが明確でないため0）
                offset_minutes = 0

            due_dt = dt - timedelta(minutes=offset_minutes)
            now = datetime.utcnow().timestamp()
            if due_dt.timestamp() < now:
                # If preparation time already passed, fall back to event start
                due_dt = dt
            return due_dt.timestamp()
        except Exception:
            return None

    def _generate_calendar_event_url(self, event_id: str, html_link: str) -> str:
        """カレンダーイベントIDから直接リンクURLを生成"""
        try:
            # Google Calendar APIのhtmlLinkフィールドが正しいWebリンクを提供する
            if html_link and html_link.startswith("https://"):
                return html_link

            # event_idが利用可能な場合、Google Calendar URLを生成
            if event_id and event_id.strip():
                # Google Calendar の標準URL形式を使用
                # 参考: https://developers.google.com/calendar/api/guides/web-ui-links
                event_url = f"https://calendar.google.com/calendar/event?eid={event_id}"
                return event_url

            # フォールバックとして基本的なカレンダーURLを返す
            self.logger.warning("No valid event link found, using fallback URL")
            return "https://calendar.google.com/calendar"

        except Exception as e:
            self.logger.error(f"Error generating calendar event URL: {str(e)}")
            return "https://calendar.google.com/calendar"

    async def generate_email_reply_draft(self, task_source_uuid: str, user: User) -> DraftModel | None:
        """
        タスクソースからメールの返信下書きを生成する

        Args:
            task_source_uuid: タスクソースのUUID
            user: ユーザー情報
            create_gmail_draft: Trueの場合、Gmailに下書きを作成する

        Returns:
            生成された返信下書き、または None（エラーまたはメール以外のソース）
        """
        try:
            # タスクソースを取得
            task_source = get_task_source_by_uuid(self.session, task_source_uuid)

            if not task_source or task_source.task.user_id != user.id:
                self.logger.error(f"TaskSource not found: {task_source_uuid}")
                return None

            # メールソースでない場合はエラー
            if task_source.source_type != SourceType.EMAIL:
                self.logger.error(f"TaskSource is not email type: {task_source.source_type}")
                return None

            # メールIDがない場合はエラー
            if not task_source.source_id:
                self.logger.error(f"Email source_id is missing: {task_source_uuid}")
                return None

            # 元のメール内容を取得
            email_content = await self._get_email_detail(user, task_source.source_id)

            # LLMで返信下書きを生成
            reply_draft = await self._generate_reply_draft_from_email(email_content, task_source)

            # Gmailに下書きを作成
            draft = await self._create_gmail_draft(user, email_content, reply_draft)

            return draft

        except Exception as e:
            self.logger.error(f"メール返信下書き生成に失敗: {str(e)}")
            return None

    async def _generate_reply_draft_from_email(
        self, email_content: dict, task_source: TaskSource
    ) -> EmailReplyDraftResponse | None:
        """
        メール内容とタスク情報から返信下書きを生成

        Args:
            email_content: 元のメール内容
            task_source: タスクソース情報

        Returns:
            生成された返信下書き、または None（生成失敗）
        """
        try:
            # メール情報を整理
            email_info = self._extract_email_info(email_content)
            task_info = self._extract_task_info(task_source)

            # 会議調整が必要かLLMに判定させる
            schedule_context = await self._determine_schedule_context(email_content, task_source)

            # 返信下書きを生成
            reply_draft = await self._generate_reply_with_context(email_info, task_info, schedule_context)

            # 件名を調整
            reply_draft.subject = self._format_reply_subject(email_info["subject"], reply_draft.subject)

            return reply_draft

        except Exception as e:
            self.logger.error(f"LLMでの返信下書き生成に失敗: {str(e)}")
            return None

    async def _create_gmail_draft(
        self, user: User, original_email: dict, reply_draft: EmailReplyDraftResponse
    ) -> DraftModel | None:
        """
        生成した返信下書きをGmailに作成する

        Args:
            user: ユーザー情報
            original_email: 元のメール情報
            reply_draft: 生成された返信下書き

        Returns:
            Gmail下書き作成結果、または None（エラー）
        """
        try:
            # 元のメールの送信者情報を取得・正規化
            original_sender = self._extract_email_address(original_email.get("from", ""))
            original_email_id = original_email.get("id", "")

            if not original_sender:
                self.logger.error("送信者のメールアドレスが取得できませんでした")
                return None

            # Gmail返信下書きを作成（スレッドに紐づけ）
            async with get_authenticated_gmail_service(user, self.session) as gmail_service:
                draft_result = await gmail_service.create_reply_draft(
                    original_email_id=original_email_id,
                    to=original_sender,
                    subject=reply_draft.subject,
                    body=reply_draft.body,
                )

            # DraftModelに変換して返す
            return DraftModel(
                id=draft_result.get("id", ""),
                subject=reply_draft.subject,
                body=reply_draft.body,
                to=original_sender,
                thread_id=draft_result.get("threadId"),
                snippet=draft_result.get("message", {}).get("snippet"),
            )

        except Exception as e:
            self.logger.error(f"Gmail返信下書き作成に失敗: {str(e)}")
            return None

    async def _get_calendar_free_time(self, user: User, days_ahead: int = 7) -> CalendarFreeTimeResponse | None:
        """
        ユーザーのGoogle Calendarから空き時間を取得する

        Args:
            user: ユーザー情報
            days_ahead: 検索する日数（デフォルト7日）

        Returns:
            空き時間情報、または None（取得失敗）
        """
        try:
            # Google Calendarサービスを使用して空き時間を取得
            async with get_authenticated_google_calendar_service(user, self.session) as calendar_service:
                return await calendar_service.get_free_time(days_ahead=days_ahead)

        except Exception as e:
            self.logger.error(f"Google Calendar空き時間取得に失敗: {str(e)}")
            return None

    def _format_available_times_for_prompt(self, free_time_response: CalendarFreeTimeResponse) -> str:
        """
        空き時間情報をプロンプト用にフォーマットする

        Args:
            free_time_response: 空き時間情報

        Returns:
            プロンプト用にフォーマットされた文字列
        """
        # GoogleCalendarServiceのロジックをここに移行
        if not free_time_response.available_slots:
            return "申し訳ございませんが、現在の予定では空き時間が見つかりませんでした。"

        formatted_slots = []
        current_date = None

        for slot in free_time_response.available_slots:
            slot_date = slot.start_time.strftime("%Y年%m月%d日")
            slot_weekday = self._get_weekday_japanese(slot.start_time)
            slot_time = f"{slot.start_time.strftime('%H:%M')}～{slot.end_time.strftime('%H:%M')}"
            slot_duration = f"({slot.duration_minutes}分)"

            if current_date != slot_date:
                formatted_slots.append(f"\n■ {slot_date}({slot_weekday})")
                current_date = slot_date

            formatted_slots.append(f"  • {slot_time} {slot_duration}")

        return f"""空いている時間は以下の通りです：
{"".join(formatted_slots)}

検索期間: {free_time_response.search_period}
合計空き時間: {free_time_response.total_free_hours:.1f}時間

※上記の時間帯から、会議に適した時間帯（30分〜2時間程度）を選んで具体的に提案してください。"""

    def _get_weekday_japanese(self, date: datetime) -> str:
        """日本語の曜日を取得"""
        weekdays = ["月", "火", "水", "木", "金", "土", "日"]
        return weekdays[date.weekday()]

    def _extract_email_info(self, email_content: dict) -> dict:
        """メール情報を抽出・整理"""
        return {
            "subject": email_content.get("subject", ""),
            "body": email_content.get("body", ""),
            "sender": email_content.get("from", ""),
            "date": email_content.get("date", ""),
        }

    def _extract_task_info(self, task_source: TaskSource) -> dict:
        """タスク情報を抽出・整理"""
        return {
            "title": task_source.title or "",
            "content": task_source.content or "",
        }

    def _extract_email_address(self, email_field: str) -> str:
        """
        メールフィールドからメールアドレスのみを抽出

        Args:
            email_field: "Name <email@example.com>" 形式の文字列

        Returns:
            抽出されたメールアドレス
        """
        if not email_field:
            return ""

        # <email@example.com> 形式からメールアドレスを抽出
        angle_bracket_match = re.search(r"<([^>]+)>", email_field)
        if angle_bracket_match:
            return angle_bracket_match.group(1).strip()

        # 単純なメールアドレス形式の場合
        email_match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", email_field)
        if email_match:
            return email_match.group(0).strip()

        # そのまま返す（既に正しい形式の場合）
        return email_field.strip()

    async def _determine_schedule_context(self, email_content: dict, task_source: TaskSource) -> dict:
        """
        会議スケジュール調整の必要性を判定し、必要に応じて空き時間情報を取得

        Returns:
            {
                "needs_scheduling": bool,
                "available_times": str or None,
                "calendar_error": str or None
            }
        """
        try:
            # LLMで会議調整の必要性を判定
            needs_scheduling = await self._check_scheduling_need(email_content, task_source)

            context = {
                "needs_scheduling": needs_scheduling,
                "available_times": None,
                "calendar_error": None,
            }

            # 会議調整が必要な場合のみ、空き時間を取得
            if needs_scheduling:
                context = await self._add_calendar_availability(context, task_source.task.user)

            return context

        except Exception as e:
            self.logger.error(f"スケジュール判定エラー: {str(e)}")
            return {
                "needs_scheduling": False,
                "available_times": None,
                "calendar_error": str(e),
            }

    async def _check_scheduling_need(self, email_content: dict, task_source: TaskSource) -> bool:
        """
        LLMを使用してメール内容から会議時間の調整が必要かどうかを判定
        """
        try:
            email_info = self._extract_email_info(email_content)
            task_info = self._extract_task_info(task_source)

            prompts = [
                {
                    "role": "system",
                    "content": """あなたはメール内容を分析して、会議やミーティングの時間調整が必要かどうかを判定するアシスタントです。

以下の条件をすべて満たす場合のみ、会議時間調整が必要と判定してください：

1. 会議・ミーティング・打ち合わせ・面談・商談・相談等の対面またはオンラインでの会話が予定されている
2. 具体的な日時が決まっておらず、スケジュール調整が必要
3. 相手が時間の提案や調整を求めている、または調整が必要な状況

以下の場合は会議時間調整不要と判定してください：
- 単なる情報共有、報告、確認、連絡
- 資料やファイルの送付・確認・レビュー
- すでに日時が確定している会議の案内
- 議事録や会議結果の共有
- 一方的な通知や案内
- 質問への回答や説明のみ
- 承認や確認のみの依頼

判定結果は true（調整必要）または false（調整不要）で返してください。""",
                },
                {
                    "role": "user",
                    "content": f"""以下のメール内容とタスク情報を分析して、会議時間の調整が必要かどうかを判定してください：

【メール情報】
件名: {email_info["subject"]}
送信者: {email_info["sender"]}
本文: {email_info["body"]}

【タスク情報】
タイトル: {task_info["title"]}
内容: {task_info["content"]}

会議時間の調整が必要ですか？ true または false で回答してください。""",
                },
            ]

            response = llm_chat_completions_perse(
                prompts=prompts,
                response_format=ScheduleJudgment,
                temperature=0.1,
                max_tokens=50,
            )

            return response.needs_scheduling

        except Exception as e:
            self.logger.error(f"LLMによるスケジュール判定に失敗: {str(e)}")
            # エラー時は安全側に倒して false を返す
            return False

    async def _add_calendar_availability(self, context: dict, user: User) -> dict:
        """空き時間情報をコンテキストに追加"""
        try:
            free_time_response = await self._get_calendar_free_time(user, days_ahead=7)
            if free_time_response and free_time_response.available_slots:
                context["available_times"] = self._format_available_times_for_prompt(free_time_response)
        except Exception as calendar_error:
            self.logger.warning(f"Google Calendar取得中にエラー: {str(calendar_error)}")
            context["calendar_error"] = str(calendar_error)
        return context

    async def _generate_reply_with_context(
        self, email_info: dict, task_info: dict, schedule_context: dict
    ) -> EmailReplyDraftResponse:
        """
        整理された情報を使用してLLMで返信下書きを生成
        """
        # システムプロンプトを構築
        system_prompt = self._build_system_prompt(schedule_context)

        # ユーザープロンプトを構築
        user_prompt = self._build_user_prompt(email_info, task_info, schedule_context)

        prompts = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # LLMで返信下書きを生成
        response = llm_chat_completions_perse(
            prompts=prompts,
            response_format=EmailReplyDraftResponse,
            temperature=0.3,
            max_tokens=800,
        )

        return response

    def _build_system_prompt(self, schedule_context: dict) -> str:
        """スケジュール文脈に応じてシステムプロンプトを構築"""
        base_prompt = """あなたは丁寧で効率的なメール返信を作成するアシスタントです。
以下のガイドラインに従って返信メールを作成してください：

1. 丁寧で適切なビジネスメールの形式を使用する
2. 元のメール内容を適切に参照する
3. 関連するタスク情報があれば適切に組み込む
4. 簡潔で明確な文章を心がける
5. 日本語で作成する

返信の構成：
- 適切な挨拶
- 元のメールへの応答
- 必要に応じてタスクに関する情報"""

        if schedule_context["needs_scheduling"] and schedule_context["available_times"]:
            return (
                base_prompt
                + """
- 【重要】提供された空き時間情報から、具体的な日時（3つ程度）を選んで候補として提案してください
- 例：「以下の日程でご都合はいかがでしょうか？」
  ・〇月〇日（〇）〇:〇〇-〇:〇〇
  ・〇月〇日（〇）〇:〇〇-〇:〇〇
  ・〇月〇日（〇）〇:〇〇-〇:〇〇
- 「数日お時間をいただき」のような曖昧な表現は避け、具体的な提案を行う
- 適切な結び

件名は「Re:」で始まる適切な件名を返してください。"""
            )
        elif schedule_context["needs_scheduling"]:
            return (
                base_prompt
                + """
- 会議時間の調整について一般的な提案を行う（後日調整等）
- カレンダー確認に時間がかかる旨を丁寧に説明
- 適切な結び

件名は「Re:」で始まる適切な件名を返してください。"""
            )
        else:
            return (
                base_prompt
                + """
- 必要に応じて今後の対応についての提案
- 適切な結び

件名は「Re:」で始まる適切な件名を返してください。"""
            )

    def _build_user_prompt(self, email_info: dict, task_info: dict, schedule_context: dict) -> str:
        """ユーザープロンプトを構築"""
        prompt = f"""以下の情報を基に返信メールの下書きを作成してください：

【元のメール情報】
件名: {email_info["subject"]}
送信者: {email_info["sender"]}
日時: {email_info["date"]}
本文: {email_info["body"]}

【関連タスク情報】
タスクタイトル: {task_info["title"]}
タスク内容: {task_info["content"]}"""

        # スケジュール調整が必要な場合の追加情報
        if schedule_context["needs_scheduling"]:
            if schedule_context["available_times"]:
                prompt += f"""

【私の空き時間情報】
{schedule_context["available_times"]}

【重要】上記の空き時間情報を活用して、具体的な日時候補を3つ選んで提案してください。
曖昧な表現（「数日お時間をいただき」等）は避け、実際の日時を明記してください。
例：「以下の日程でご都合はいかがでしょうか？
・〇月〇日（〇）〇:〇〇-〇:〇〇
・〇月〇日（〇）〇:〇〇-〇:〇〇
・〇月〇日（〇）〇:〇〇-〇:〇〇」"""
            else:
                prompt += """

※会議時間の調整が必要と思われますが、現在カレンダー情報を取得できていません。
スケジュール確認に時間がかかる旨を丁寧に説明し、後日連絡する旨を伝えてください。"""

        prompt += "\n\n適切な返信メールの件名と本文を作成してください。"
        return prompt

    def _format_reply_subject(self, original_subject: str, generated_subject: str) -> str:
        """返信件名をフォーマット"""
        # 生成された件名にRe:がない場合は追加
        if generated_subject and not generated_subject.startswith("Re:"):
            if original_subject.startswith("Re:"):
                return original_subject
            else:
                return f"Re: {original_subject}"
        return generated_subject
