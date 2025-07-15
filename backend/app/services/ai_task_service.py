import logging
from datetime import datetime, timedelta
from typing import List
from zoneinfo import ZoneInfo

from app.models.google_mail import DraftModel
from app.repositories.task_source import create_task_source, get_task_source_by_uuid
from app.repositories.tasks import create_task
from app.schema import SourceType, TaskSource, User
from app.services.ai.spokes.google_calendar.spoke import GoogleCalendarSpoke
from app.services.gmail_service import get_authenticated_gmail_service
from app.utils.llm import llm_chat_completions_perse
from pydantic import BaseModel
from sqlmodel import Session


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


class EmailReplyDraftResponse(BaseModel):
    """LLMからのメール返信下書きレスポンス"""

    subject: str
    body: str


class AvailableTimeSlot(BaseModel):
    """利用可能な時間スロット"""

    start_time: datetime
    end_time: datetime
    duration_minutes: int


class CalendarFreeTimeResponse(BaseModel):
    """カレンダー空き時間情報"""

    available_slots: List[AvailableTimeSlot]
    search_period: str
    total_free_hours: float


class ScheduleJudgment(BaseModel):
    """スケジュール調整の必要性を判断するレスポンス"""

    needs_scheduling: bool


class AiTaskService:

    def __init__(self, session: Session, user_id: int):
        self.session = session
        self.user_id = user_id
        self.logger = logging.getLogger(__name__)

    async def generate_tasks_from_new_emails(
        self, user: User, max_emails: int = 10
    ) -> List[dict]:
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
            async with get_authenticated_gmail_service(
                user, self.session
            ) as gmail_service:
                new_emails = await gmail_service.get_new_emails(max_results=max_emails)

            if not new_emails:
                self.logger.info("新着メールが見つかりませんでした")
                return []

            generated_tasks = []

            for email in new_emails:
                try:
                    # メール内容を詳細取得
                    email_content = await self._get_email_detail(user, email["id"])

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
                        )

                        # TaskSourceを作成（メール情報と直接リンクを保存）
                        gmail_url = self._generate_gmail_url(email["id"])
                        create_task_source(
                            session=self.session,
                            task_id=task.id,
                            source_type=SourceType.EMAIL,
                            source_id=email["id"],
                            title=email_content.get("subject", ""),
                            content=email_content.get("body", ""),
                            source_url=gmail_url,
                            extra_data=None,
                        )

                        generated_tasks.append(
                            {
                                "uuid": str(task.uuid),
                                "title": task.title,
                                "description": task.description,
                                "expires_at": task.expires_at,
                                "source_email_id": email["id"],
                            }
                        )

                        self.logger.info(f"タスクを生成しました: {task.title}")

                except Exception as e:
                    self.logger.error(
                        f"メール {email['id']} からのタスク生成に失敗: {str(e)}"
                    )
                    continue

            return generated_tasks

        except Exception as e:
            self.logger.error(f"新着メールからのタスク生成に失敗: {str(e)}")
            raise

    def _generate_gmail_url(self, email_id: str) -> str:
        """GmailメールIDから直接リンクURLを生成"""
        return f"https://mail.google.com/mail/u/0/#inbox/{email_id}"

    async def _get_email_detail(self, user: User, email_id: str) -> dict:
        """メールの詳細情報を取得"""
        async with get_authenticated_gmail_service(user, self.session) as gmail_service:
            return await gmail_service.get_email_content(email_id)

    async def _generate_task_from_email(
        self, email_content: dict
    ) -> TaskGenerationResponse | None:
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

expires_at は UNIX タイムスタンプで返してください。期限が明確でない場合は null を返してください。""",
                },
                {
                    "role": "user",
                    "content": f"""以下のメール内容を分析してタスクを生成してください：

件名: {subject}
送信者: {sender}
日時: {date}
本文: {body}

適切なタスクのタイトル、説明、期限を生成してください。""",
                },
            ]

            # LLMでタスクを生成
            response = llm_chat_completions_perse(
                prompts=prompts,
                response_format=TaskGenerationResponse,
                temperature=0.3,
                max_tokens=500,
            )

            # タスクに適さない場合（titleが空）は None を返す
            if not response.title.strip():
                return None

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

    async def generate_email_reply_draft(
        self, task_source_uuid: str, user: User
    ) -> DraftModel | None:
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
                self.logger.error(
                    f"TaskSource is not email type: {task_source.source_type}"
                )
                return None

            # メールIDがない場合はエラー
            if not task_source.source_id:
                self.logger.error(f"Email source_id is missing: {task_source_uuid}")
                return None

            # 元のメール内容を取得
            email_content = await self._get_email_detail(user, task_source.source_id)

            # LLMで返信下書きを生成
            reply_draft = await self._generate_reply_draft_from_email(
                email_content, task_source
            )

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
            schedule_context = await self._determine_schedule_context(
                email_content, task_source
            )

            # 返信下書きを生成
            reply_draft = await self._generate_reply_with_context(
                email_info, task_info, schedule_context
            )

            # 件名を調整
            reply_draft.subject = self._format_reply_subject(
                email_info["subject"], reply_draft.subject
            )

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
            # 元のメールの送信者情報を取得
            original_sender = original_email.get("from", "")
            original_email_id = original_email.get("id", "")

            # Gmail返信下書きを作成（スレッドに紐づけ）
            async with get_authenticated_gmail_service(
                user, self.session
            ) as gmail_service:
                draft_result = await gmail_service.create_reply_draft(
                    original_email_id=original_email_id,
                    to=original_sender,
                    subject=reply_draft.subject,
                    body=reply_draft.body,
                )

            self.logger.info(
                f"Gmail返信下書きを作成しました: {draft_result.get('id', 'unknown')}, スレッドID: {draft_result.get('threadId', 'unknown')}"
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

    async def _get_calendar_free_time(
        self, user: User, days_ahead: int = 7
    ) -> CalendarFreeTimeResponse | None:
        """
        ユーザーのGoogle Calendarから空き時間を取得する

        Args:
            user: ユーザー情報
            days_ahead: 検索する日数（デフォルト7日）

        Returns:
            空き時間情報、または None（取得失敗）
        """
        try:
            # Google Calendarスポークを初期化
            calendar_spoke = GoogleCalendarSpoke(
                session=self.session, current_user=user
            )

            # 検索期間を設定（現在時刻から指定日数後まで）
            jst = ZoneInfo("Asia/Tokyo")
            now = datetime.now(jst)
            start_date = now.replace(
                hour=9, minute=0, second=0, microsecond=0
            )  # 9時から開始
            end_date = (now + timedelta(days=days_ahead)).replace(
                hour=18, minute=0, second=0, microsecond=0
            )  # 18時まで

            # カレンダーイベントを取得
            response = await calendar_spoke.action_get_calendar_events(
                {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "max_results": 100,
                }
            )

            if not response.success:
                error_message = f"Google Calendar取得エラー: {response.error}"
                if hasattr(response, "metadata") and response.metadata:
                    error_message += f" (詳細: {response.metadata})"
                self.logger.error(error_message)
                return None

            # 既存のイベントを解析
            events = response.data or []
            occupied_slots = []

            for event in events:
                if event.get("start_time") and event.get("end_time"):
                    start = event["start_time"]
                    end = event["end_time"]

                    # datetime オブジェクトでない場合は変換
                    if isinstance(start, str):
                        start = datetime.fromisoformat(start.replace("Z", "+00:00"))
                    if isinstance(end, str):
                        end = datetime.fromisoformat(end.replace("Z", "+00:00"))

                    occupied_slots.append((start, end))

            # 空き時間スロットを計算
            available_slots = self._calculate_free_time_slots(
                start_date, end_date, occupied_slots
            )

            # 合計空き時間を計算
            total_free_hours = (
                sum(slot.duration_minutes for slot in available_slots) / 60.0
            )

            return CalendarFreeTimeResponse(
                available_slots=available_slots,
                search_period=f"{start_date.strftime('%Y-%m-%d')} から {end_date.strftime('%Y-%m-%d')}",
                total_free_hours=total_free_hours,
            )

        except Exception as e:
            self.logger.error(f"Google Calendar空き時間取得に失敗: {str(e)}")
            return None

    def _calculate_free_time_slots(
        self,
        start_date: datetime,
        end_date: datetime,
        occupied_slots: List[tuple],
        min_slot_minutes: int = 30,
        work_start_hour: int = 9,
        work_end_hour: int = 18,
    ) -> List[AvailableTimeSlot]:
        """
        空き時間スロットを計算する

        Args:
            start_date: 検索開始日時
            end_date: 検索終了日時
            occupied_slots: 既存の予定のタイムスロット
            min_slot_minutes: 最小スロット時間（分）
            work_start_hour: 業務開始時間
            work_end_hour: 業務終了時間

        Returns:
            利用可能な時間スロットのリスト
        """

        available_slots = []
        current_date = start_date.date()
        end_date_only = end_date.date()

        # タイムゾーンを統一（JSTを使用）
        jst = ZoneInfo("Asia/Tokyo")

        while current_date <= end_date_only:
            # 平日のみ対象（土日は除外）
            if current_date.weekday() < 5:  # 0-4が月-金
                day_start = datetime.combine(
                    current_date, datetime.min.time().replace(hour=work_start_hour)
                ).replace(tzinfo=jst)
                day_end = datetime.combine(
                    current_date, datetime.min.time().replace(hour=work_end_hour)
                ).replace(tzinfo=jst)

                # その日の予定を取得（タイムゾーンを統一）
                day_occupied = []
                for start, end in occupied_slots:
                    # タイムゾーン情報がない場合はJSTとして扱う
                    if start.tzinfo is None:
                        start = start.replace(tzinfo=jst)
                    if end.tzinfo is None:
                        end = end.replace(tzinfo=jst)

                    # その日の範囲内の予定のみを対象とする
                    if (
                        start.date() == current_date
                        and end > day_start
                        and start < day_end
                    ):
                        day_occupied.append((max(start, day_start), min(end, day_end)))

                # 予定を時間順にソート
                day_occupied.sort(key=lambda x: x[0])

                # 空き時間を計算
                current_time = day_start
                for occupied_start, occupied_end in day_occupied:
                    # 空き時間があるかチェック
                    if current_time < occupied_start:
                        slot_duration = (
                            occupied_start - current_time
                        ).total_seconds() / 60
                        if slot_duration >= min_slot_minutes:
                            available_slots.append(
                                AvailableTimeSlot(
                                    start_time=current_time,
                                    end_time=occupied_start,
                                    duration_minutes=int(slot_duration),
                                )
                            )
                    current_time = max(current_time, occupied_end)

                # 最後の予定から終業時間までの空き時間
                if current_time < day_end:
                    slot_duration = (day_end - current_time).total_seconds() / 60
                    if slot_duration >= min_slot_minutes:
                        available_slots.append(
                            AvailableTimeSlot(
                                start_time=current_time,
                                end_time=day_end,
                                duration_minutes=int(slot_duration),
                            )
                        )

            current_date += timedelta(days=1)

        return available_slots

    def _format_available_times_for_prompt(
        self, free_time_response: CalendarFreeTimeResponse
    ) -> str:
        """
        空き時間情報をプロンプト用にフォーマットする

        Args:
            free_time_response: 空き時間情報

        Returns:
            プロンプト用にフォーマットされた文字列
        """
        if not free_time_response.available_slots:
            return (
                "申し訳ございませんが、現在の予定では空き時間が見つかりませんでした。"
            )

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
{''.join(formatted_slots)}

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

    async def _determine_schedule_context(
        self, email_content: dict, task_source: TaskSource
    ) -> dict:
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
            needs_scheduling = await self._check_scheduling_need(
                email_content, task_source
            )

            context = {
                "needs_scheduling": needs_scheduling,
                "available_times": None,
                "calendar_error": None,
            }

            # 会議調整が必要な場合のみ、空き時間を取得
            if needs_scheduling:
                self.logger.info(
                    "会議調整が必要。Google Calendarから空き時間を取得中..."
                )
                context = await self._add_calendar_availability(
                    context, task_source.task.user
                )

            return context

        except Exception as e:
            self.logger.error(f"スケジュール判定エラー: {str(e)}")
            return {
                "needs_scheduling": False,
                "available_times": None,
                "calendar_error": str(e),
            }

    async def _check_scheduling_need(
        self, email_content: dict, task_source: TaskSource
    ) -> bool:
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
件名: {email_info['subject']}
送信者: {email_info['sender']}
本文: {email_info['body']}

【タスク情報】
タイトル: {task_info['title']}
内容: {task_info['content']}

会議時間の調整が必要ですか？ true または false で回答してください。""",
                },
            ]

            response = llm_chat_completions_perse(
                prompts=prompts,
                response_format=ScheduleJudgment,
                temperature=0.1,
                max_tokens=50,
            )

            self.logger.info(
                f"LLMによる会議時間調整判定結果: {response.needs_scheduling}"
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
                context["available_times"] = self._format_available_times_for_prompt(
                    free_time_response
                )
                self.logger.info(
                    f"空き時間を取得成功: {len(free_time_response.available_slots)}件のスロット"
                )
            else:
                self.logger.warning("空き時間が見つかりませんでした")
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

    def _build_user_prompt(
        self, email_info: dict, task_info: dict, schedule_context: dict
    ) -> str:
        """ユーザープロンプトを構築"""
        prompt = f"""以下の情報を基に返信メールの下書きを作成してください：

【元のメール情報】
件名: {email_info['subject']}
送信者: {email_info['sender']}
日時: {email_info['date']}
本文: {email_info['body']}

【関連タスク情報】
タスクタイトル: {task_info['title']}
タスク内容: {task_info['content']}"""

        # スケジュール調整が必要な場合の追加情報
        if schedule_context["needs_scheduling"]:
            if schedule_context["available_times"]:
                prompt += f"""

【私の空き時間情報】
{schedule_context['available_times']}

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

    def _format_reply_subject(
        self, original_subject: str, generated_subject: str
    ) -> str:
        """返信件名をフォーマット"""
        # 生成された件名にRe:がない場合は追加
        if generated_subject and not generated_subject.startswith("Re:"):
            if original_subject.startswith("Re:"):
                return original_subject
            else:
                return f"Re: {original_subject}"
        return generated_subject
