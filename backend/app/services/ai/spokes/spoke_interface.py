"""
スポーク共通インターフェース
"""

import json
from abc import ABC

from app.schema import User
from app.services.ai.logger import AIAssistantLogger
from app.services.ai.models import NextAction, SpokeResponse
from app.utils.llm import llm_chat_completions
from sqlmodel import Session


class BaseSpoke(ABC):
    """スポーク基底クラス

    このクラスを継承してスポークを実装する場合、アクションメソッドは
    関数名の先頭に 'action_' を付ける必要があります。

    例:
        - get_calendar_events アクション -> action_get_calendar_events メソッド
        - send_email アクション -> action_send_email メソッド
        - create_task アクション -> action_create_task メソッド

    アクションメソッドは自動的に get_supported_actions() で検出され、
    execute_action() によって呼び出されます。
    """

    def __init__(
        self,
        session: Session,
        current_user: User,
    ):
        self.session = session
        self.current_user = current_user
        self.logger = AIAssistantLogger(self.__class__.__name__)

    async def execute_action(
        self,
        action: NextAction,
        action_definition: dict,
    ) -> SpokeResponse:
        """アクションを実行する"""
        try:
            # アクション名をメソッド名に変換 (例: get_calendar_events -> action_get_calendar_events)
            method_name = f"action_{action.action_type}"

            # メソッドが存在するかチェック
            if not hasattr(self, method_name):
                return SpokeResponse(
                    success=False,
                    error=f"Unsupported action type: {action.action_type}",
                )

            # 元のパラメータを初期値として設定
            parameters = action.get_parameters_dict()

            try:
                predict_parameters = await self._predict_parameters(
                    spoke_name=action.spoke_name,
                    action_type=action.action_type,
                    parameters=parameters,
                    action_definition=action_definition,
                )

                if predict_parameters:
                    parameters = predict_parameters
                else:
                    # パラメータが空の場合は、元のパラメータを使用
                    self.logger.warning(
                        f"No predicted parameters for {action.spoke_name}.{action.action_type}, using original parameters."
                    )
            except Exception as e:
                # パラメータ推測に失敗した場合はログに記録し、元のパラメータを使用
                self.logger.error(
                    f"Failed to predict parameters for {action.spoke_name}.{action.action_type}: {str(e)}"
                )

            self.logger.info(
                f"Executing action {action.spoke_name}.{action.action_type} with parameters: {parameters}"
            )

            return await getattr(self, method_name)(parameters)

        except Exception as e:
            return SpokeResponse(
                success=False,
                error=f"Error executing action {action.spoke_name}.{action.action_type}: {str(e)}",
            )

    @classmethod
    def get_supported_actions(cls) -> list[str]:
        """このスポークがサポートするアクションタイプのリストを返す"""
        # action_で始まるメソッドを自動的に検出
        actions = []
        for attr_name in dir(cls):
            if attr_name.startswith("action_") and callable(getattr(cls, attr_name)):
                # action_プレフィックスを除去してアクション名を取得
                action_name = attr_name[7:]  # "action_"の長さは7文字
                actions.append(action_name)
        return sorted(actions)  # ソートして一貫性を保つ

    async def _predict_parameters(
        self,
        spoke_name: str,
        action_type: str,
        parameters: dict,
        action_definition: dict,
    ) -> dict:
        """
        LLMにパラメータの推測を依頼する
        """
        prompt = f"""
あなたは与えられた情報を基に、アクションに必要なパラメータを推測するAIアシスタントです。

以下の情報を基に、アクションに必要なパラメータを推測してください：

**スポーク名**: {spoke_name}
**アクションタイプ**: {action_type}
**現在のパラメータ**: {parameters}

**アクション定義**:
{action_definition}

以下のJSONフォーマットで応答してください：
{{
    "predicted_parameters": {{
        // 推測したパラメータの値をここに記載
        // 必須パラメータは必ず含める
        // オプションパラメータは適切と思われる場合のみ含める
    }},
}}

注意事項：
- 必須パラメータ（required: true）は必ず推測して含めてください
- 日時パラメータの場合は、元のパラメータのタイムゾーンを考慮し、元のタイムゾーンに則した適切な形式で推測してください
- user_idなどのIDパラメータは、具体的な値が分からない場合は null にしてください
- 不明なパラメータは推測せず、null または省略してください
"""

        # ログにプロンプトを記録（デバッグ用）
        self.logger.info(prompt)

        try:
            # LLM APIを呼び出し
            response_content = llm_chat_completions(
                prompts=[
                    {
                        "role": "system",
                        "content": "あなたは正確で有用なパラメータ推測を行うAIアシスタントです。",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=1000,
            )

            # JSONレスポンスをパース
            parsed_response = json.loads(response_content)
            return parsed_response.get("predicted_parameters", {})

        except Exception as e:
            self.logger.error(f"Failed to predict parameters: {str(e)}")
            return {}
