"""
Base spoke interface for all AI service spokes
"""

import json
from abc import ABC
from typing import Dict, Any

from app.schema import User
from sqlmodel import Session

from ..core.models import NextAction, SpokeResponse
from ..utils.logger import AIAssistantLogger
from app.utils.llm import llm_chat_completions


class BaseSpoke(ABC):
    """
    Base spoke class for all AI service spokes

    To implement a spoke, inherit from this class and create methods
    with the 'action_' prefix for each supported action.

    Example:
        - get_calendar_events action -> action_get_calendar_events method
        - send_email action -> action_send_email method
        - create_task action -> action_create_task method

    Action methods are automatically detected by get_supported_actions()
    and called by execute_action().
    """

    def __init__(self, session: Session, current_user: User):
        self.session = session
        self.current_user = current_user
        self.logger = AIAssistantLogger(self.__class__.__name__)

    async def execute_action(
        self, action: NextAction, action_definition: Dict[str, Any]
    ) -> SpokeResponse:
        """Execute an action"""
        try:
            # Convert action name to method name (e.g., get_calendar_events -> action_get_calendar_events)
            method_name = f"action_{action.action_type}"

            # Check if method exists
            if not hasattr(self, method_name):
                return SpokeResponse(
                    success=False,
                    error=f"Unsupported action type: {action.action_type}",
                )

            # Get original parameters
            parameters = action.get_parameters_dict()

            # Try to predict/enhance parameters using LLM
            try:
                enhanced_parameters = await self._enhance_parameters(
                    action.spoke_name, action.action_type, parameters, action_definition
                )
                if enhanced_parameters:
                    parameters = enhanced_parameters
                else:
                    self.logger.warning(
                        f"No enhanced parameters for {action.spoke_name}.{action.action_type}, using original"
                    )
            except Exception as e:
                self.logger.error(
                    f"Failed to enhance parameters for {action.spoke_name}.{action.action_type}: {str(e)}"
                )

            self.logger.info(
                f"Executing {action.spoke_name}.{action.action_type} with parameters: {parameters}"
            )

            return await getattr(self, method_name)(parameters)

        except Exception as e:
            return SpokeResponse(
                success=False,
                error=f"Error executing {action.spoke_name}.{action.action_type}: {str(e)}",
            )

    @classmethod
    def get_supported_actions(cls) -> list[str]:
        """Get list of action types supported by this spoke"""
        actions = []
        for attr_name in dir(cls):
            if attr_name.startswith("action_") and callable(getattr(cls, attr_name)):
                # Remove "action_" prefix to get action name
                action_name = attr_name[7:]  # "action_" is 7 characters
                actions.append(action_name)
        return sorted(actions)

    async def _enhance_parameters(
        self,
        spoke_name: str,
        action_type: str,
        parameters: Dict[str, Any],
        action_definition: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Use LLM to enhance/predict action parameters
        """
        prompt = f"""
あなたは与えられた情報を基に、アクションに必要なパラメータを推測・補完するAIアシスタントです。

以下の情報を基に、アクションに必要なパラメータを推測してください：

**スポーク名**: {spoke_name}
**アクションタイプ**: {action_type}
**現在のパラメータ**: {parameters}

**アクション定義**:
{action_definition}

以下のJSONフォーマットで応答してください：
{{
    "enhanced_parameters": {{
        // 推測・補完したパラメータの値をここに記載
        // 必須パラメータは必ず含める
        // オプションパラメータは適切と思われる場合のみ含める
    }}
}}

注意事項：
- 必須パラメータ（required: true）は必ず推測して含めてください
- 日時パラメータの場合は、適切な形式で推測してください
- 不明なパラメータは推測せず、null または省略してください
"""

        try:
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

            parsed_response = json.loads(response_content)
            return parsed_response.get("enhanced_parameters", {})

        except Exception as e:
            self.logger.error(f"Failed to enhance parameters: {str(e)}")
            return {}
