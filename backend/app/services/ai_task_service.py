import logging
import re
from datetime import datetime, timedelta
from typing import List

from app.models.google_mail import DraftModel
from app.repositories.task_source import create_task_source, get_task_source_by_uuid
from app.repositories.tasks import create_task
from app.schema import SourceType, TaskSource, User
from app.services.gmail_service import get_authenticated_gmail_service
from app.services.google_calendar_service import (
    CalendarFreeTimeResponse,
    get_authenticated_google_calendar_service,
)
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
                                "uuid": task.uuid,
                                "title": task.title,
                                "description": task.description,
                                "completed": task.completed,
                                "expires_at": task.expires_at,
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

    async def generate_tasks_from_calendar_events(
        self, user: User, days_ahead: int = 7, max_events: int = 20
    ) -> List[dict]:
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
            async with get_authenticated_google_calendar_service(
                user, self.session
            ) as calendar_service:
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
                        )

                        # TaskSourceを作成（カレンダーイベント情報を保存）
                        event_id = event.get("id", "")
                        html_link = event.get(
                            "htmlLink", ""
                        )  # Google Calendar APIの正式フィールド名

                        event_url = self._generate_calendar_event_url(
                            event_id, html_link
                        )

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

                        self.logger.info(
                            f"カレンダーイベントからタスクを生成しました: {task.title}"
                        )

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

    async def _generate_task_from_calendar_event(
        self, event: dict
    ) -> TaskGenerationResponse | None:
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
カレンダーイベントを分析し、以下の条件に当てはまる場合のみタスクを生成してください：

1. 会議やイベントの準備が必要
2. 会議後のフォローアップが必要
3. 資料作成や確認などの事前作業が必要
4. 何らかのアクションアイテムが発生する可能性がある

単純な定期会議や個人的な予定など、特別な準備やアクションが不要な場合は、title を空文字列で返してください。

expires_at は UNIX タイムスタンプで返してください。通常はイベント開始時刻より前に設定してください。
期限が明確でない場合は null を返してください。""",
                },
                {
                    "role": "user",
                    "content": f"""以下のカレンダーイベントを分析してタスクを生成してください：

イベント名: {summary}
説明: {description}
場所: {location}
開始時刻: {start_str}
終了時刻: {end_str}

このイベントに関連して、事前準備やフォローアップのための適切なタスクのタイトル、説明、期限を生成してください。""",
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
            self.logger.error(f"LLMでのカレンダータスク生成に失敗: {str(e)}")
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
            # 元のメールの送信者情報を取得・正規化
            original_sender = self._extract_email_address(
                original_email.get("from", "")
            )
            original_email_id = original_email.get("id", "")

            if not original_sender:
                self.logger.error("送信者のメールアドレスが取得できませんでした")
                return None

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
            # Google Calendarサービスを使用して空き時間を取得
            async with get_authenticated_google_calendar_service(
                user, self.session
            ) as calendar_service:
                return await calendar_service.get_free_time(days_ahead=days_ahead)

        except Exception as e:
            self.logger.error(f"Google Calendar空き時間取得に失敗: {str(e)}")
            return None

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
        # GoogleCalendarServiceのロジックをここに移行
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
        email_match = re.search(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", email_field
        )
        if email_match:
            return email_match.group(0).strip()

        # そのまま返す（既に正しい形式の場合）
        return email_field.strip()

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
