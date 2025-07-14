import logging
from datetime import datetime
from typing import List

from app.repositories.tasks import create_task
from app.schema import User, TaskSource, SourceType
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

                        # タスクソースを作成
                        task_source = TaskSource(
                            task_id=task.id,
                            source_type=SourceType.EMAIL,
                            source_id=email["id"],
                            title=email_content.get("subject", ""),
                            content=email_content.get("body", "")[:1000],
                            source_url=None,
                            extra_data=None,
                        )
                        self.session.add(task_source)
                        self.session.commit()
                        self.session.refresh(task_source)

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
本文: {body[:1000]}...

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
