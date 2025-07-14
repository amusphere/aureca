import logging
from datetime import datetime
from typing import List

from app.repositories.task_source import create_task_source, get_task_source_by_uuid
from app.repositories.tasks import create_task
from app.schema import SourceType, TaskSource, User
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
        self, task_source_uuid: str, user: User, create_gmail_draft: bool = False
    ) -> EmailReplyDraftResponse | None:
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

            # Gmailに下書きを作成する場合
            if create_gmail_draft and reply_draft:
                await self._create_gmail_draft(user, email_content, reply_draft)

            return reply_draft

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
            original_subject = email_content.get("subject", "")
            original_body = email_content.get("body", "")
            sender = email_content.get("from", "")
            date = email_content.get("date", "")

            # タスク情報
            task_title = task_source.title or ""
            task_content = task_source.content or ""

            # 件名にRe:を追加（既にある場合は追加しない）
            reply_subject = (
                original_subject
                if original_subject.startswith("Re:")
                else f"Re: {original_subject}"
            )

            # LLMへのプロンプトを作成
            prompts = [
                {
                    "role": "system",
                    "content": """あなたは丁寧で効率的なメール返信を作成するアシスタントです。
以下のガイドラインに従って返信メールを作成してください：

1. 丁寧で適切なビジネスメールの形式を使用する
2. 元のメール内容を適切に参照する
3. 関連するタスク情報があれば適切に組み込む
4. 簡潔で明確な文章を心がける
5. 日本語で作成する

返信の構成：
- 適切な挨拶
- 元のメールへの応答
- 必要に応じてタスクに関する情報
- 適切な結び

件名は「Re:」で始まる適切な件名を返してください。""",
                },
                {
                    "role": "user",
                    "content": f"""以下の情報を基に返信メールの下書きを作成してください：

【元のメール情報】
件名: {original_subject}
送信者: {sender}
日時: {date}
本文: {original_body}

【関連タスク情報】
タスクタイトル: {task_title}
タスク内容: {task_content}

適切な返信メールの件名と本文を作成してください。""",
                },
            ]

            # LLMで返信下書きを生成
            response = llm_chat_completions_perse(
                prompts=prompts,
                response_format=EmailReplyDraftResponse,
                temperature=0.3,
                max_tokens=800,
            )

            # 生成された件名を確認し、必要に応じて調整
            if response.subject and not response.subject.startswith("Re:"):
                response.subject = reply_subject

            return response

        except Exception as e:
            self.logger.error(f"LLMでの返信下書き生成に失敗: {str(e)}")
            return None

    async def _create_gmail_draft(
        self, user: User, original_email: dict, reply_draft: EmailReplyDraftResponse
    ) -> dict | None:
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

            # Gmail下書きを作成
            async with get_authenticated_gmail_service(
                user, self.session
            ) as gmail_service:
                draft_result = await gmail_service.create_draft(
                    to=original_sender,
                    subject=reply_draft.subject,
                    body=reply_draft.body,
                )

            self.logger.info(
                f"Gmail下書きを作成しました: {draft_result.get('id', 'unknown')}"
            )
            return draft_result

        except Exception as e:
            self.logger.error(f"Gmail下書き作成に失敗: {str(e)}")
            return None
