"""
Main AI Hub - Consolidated orchestrator and operator functionality
"""

import os
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from sqlmodel import Session

from app.schema import User
from app.utils.llm import llm_chat_completions, llm_chat_completions_perse

from ..spokes.manager import SpokeManager
from ..utils.exceptions import InvalidParameterError
from ..utils.logger import AIAssistantLogger
from .models import NextAction, OperatorResponse, SpokeResponse


class AIHub:
    """
    Main AI Hub - Central controller for the hub-and-spoke AI system

    Combines the functionality of orchestrator and operator into a single,
    simplified interface that maintains the hub-and-spoke architecture.
    """

    def __init__(
        self,
        user_id: int,
        session: Session | None = None,
    ):
        self.user_id = user_id
        self.session = session
        self.logger = AIAssistantLogger("ai_hub")

        # Initialize spoke manager
        spokes_dir = os.path.join(os.path.dirname(__file__), "..", "spokes")
        self.spoke_manager = SpokeManager(spokes_dir, session)

    async def process_request(
        self,
        prompt: str,
        current_user: User,
    ) -> dict[str, Any]:
        """
        Process user request through the hub-and-spoke system

        Args:
            prompt: User's natural language prompt
            current_user: Current user object

        Returns:
            Dictionary containing analysis, execution results, and summary
        """
        try:
            # Step 1: Analyze prompt and generate action plan
            operator_response = await self._analyze_prompt(prompt)

            # Step 2: Execute action plan through spokes
            execution_results = await self._execute_actions(operator_response.actions, current_user)

            # Step 3: Create summary
            summary = self._create_execution_summary(prompt, operator_response, execution_results)

            return {
                "success": True,
                "operator_response": {
                    "analysis": operator_response.analysis,
                    "confidence": operator_response.confidence,
                    "actions_planned": len(operator_response.actions),
                },
                "execution_results": [
                    {
                        "success": result.success,
                        "data": result.data,
                        "error": result.error,
                        "metadata": result.metadata,
                    }
                    for result in execution_results
                ],
                "summary": summary,
            }

        except Exception as e:
            self.logger.log_error(e, {"user_id": self.user_id, "prompt": prompt})
            return {
                "success": False,
                "error": f"Processing error: {str(e)}",
                "operator_response": None,
                "execution_results": [],
                "summary": {
                    "total_actions": 0,
                    "successful_actions": 0,
                    "failed_actions": 1,
                    "overall_status": "failed",
                },
            }

    async def _analyze_prompt(self, prompt: str) -> OperatorResponse:
        """Analyze user prompt and generate action plan"""
        system_prompt = self._generate_system_prompt()

        self.logger.info(f"Analyzing prompt with system prompt length: {len(system_prompt)}")

        try:
            operator_response = llm_chat_completions_perse(
                prompts=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                response_format=OperatorResponse,
                temperature=0.7,
                max_tokens=1500,
            )

            # Validate actions against supported actions
            supported_actions = self.spoke_manager.get_all_action_types()
            for action in operator_response.actions:
                if action.action_type not in supported_actions and action.action_type != "unknown":
                    raise InvalidParameterError(f"Unsupported action type: {action.action_type}")

            self.logger.info(f"Prompt analysis complete: {len(operator_response.actions)} actions planned")
            return operator_response

        except Exception as e:
            self.logger.log_error(e, {"user_id": self.user_id, "prompt": prompt})
            return OperatorResponse(
                actions=[
                    NextAction(
                        spoke_name="unknown",
                        action_type="unknown",
                        description=f"Error: {str(e)}",
                    )
                ],
                analysis=f"Prompt analysis error: {str(e)}",
                confidence=0.0,
            )

    async def _execute_actions(
        self,
        actions: list[NextAction],
        current_user: User,
    ) -> list[SpokeResponse]:
        """Execute actions through spoke system"""
        # Sort by priority (lower numbers = higher priority)
        sorted_actions = sorted(actions, key=lambda x: x.priority)

        results = []
        for action in sorted_actions:
            try:
                result = await self.spoke_manager.execute_action(action, current_user)
                results.append(result)

                # Stop execution on critical errors (priority 1 failures)
                if not result.success and action.priority == 1:
                    self.logger.warning(f"Critical action failed, stopping execution: {action.action_type}")
                    break

            except Exception as e:
                self.logger.log_error(
                    e,
                    {
                        "action_type": action.action_type,
                        "spoke_name": action.spoke_name,
                    },
                )
                results.append(SpokeResponse(success=False, error=f"Execution error: {str(e)}"))

        return results

    def _generate_system_prompt(self) -> str:
        """Generate system prompt with available actions"""
        # Get current time in JST
        jst = ZoneInfo("Asia/Tokyo")
        current_time = datetime.now(jst).isoformat()

        # Get available actions from spoke manager
        actions_list = self.spoke_manager.get_actions_description()

        return f"""
あなたはユーザーのリクエストを解析し、適切なアクションを決定するAIアシスタントです。

利用可能なアクション:
{actions_list}

現在の日時: {current_time} (JST)
ユーザーID: {self.user_id}

## 重要な指示:
- parameters に user_id: {self.user_id} を必ず含めてください
- 相対的な日時表現（「明日」「来週」「今日」「次の金曜日」など）は具体的な日時に変換してください
- 日時に関することは基本的に日本時間（JST）で処理を行ってください
- オプショナルなパラメータが存在しない場合は、`null` または `None` を返してください

## タスク優先度の判定ガイドライン:
タスク作成・更新時には、ユーザーのリクエスト内容を分析して適切な優先度を設定してください：

**high (高優先度)**:
- 緊急キーワード: 「緊急」「至急」「ASAP」「すぐに」「今日中」「明日まで」
- 重要なイベント: 「重要な会議」「面接」「プレゼン」「締切」「顧客対応」
- 権威・影響度: 「社長」「役員」「クライアント」「重要な取引先」

**middle (中優先度)**:
- 計画的対応: 「今週中」「来週まで」「確認してください」「対応をお願いします」
- 標準業務: 「会議」「ミーティング」「準備」「確認」「報告」

**low (低優先度)**:
- 余裕のある対応: 「時間があるときに」「参考まで」「いつでも」「定期的に」
- 情報共有: 「FYI」「お知らせ」「連絡まで」

**null (優先度なし)**:
- 緊急性・重要性が不明確、または単純な情報提供のみの場合

迷った場合は、より低い優先度を選択してください。
"""

    def _create_execution_summary(
        self,
        prompt: str,
        operator_response: OperatorResponse,
        execution_results: list[SpokeResponse],
    ) -> dict[str, Any]:
        """Create execution summary"""
        total_actions = len(execution_results)
        successful_actions = sum(1 for result in execution_results if result.success)
        failed_actions = total_actions - successful_actions

        # Calculate success rate
        success_rate = successful_actions / total_actions if total_actions > 0 else 0

        # Determine overall status
        if success_rate == 1.0:
            overall_status = "completed"
        elif success_rate > 0.5:
            overall_status = "partially_completed"
        elif success_rate > 0:
            overall_status = "mostly_failed"
        else:
            overall_status = "failed"

        # Extract results data
        results_data = []
        for i, result in enumerate(execution_results):
            action = operator_response.actions[i] if i < len(operator_response.actions) else None
            results_data.append(
                {
                    "action_type": action.action_type if action else "unknown",
                    "success": result.success,
                    "description": action.description if action else "Unknown action",
                    "data_available": result.data is not None,
                    "error": result.error,
                    "data": (result.data if result.success and result.data is not None else None),
                }
            )

        # Generate natural language response
        results_text = llm_chat_completions(
            prompts=[
                {
                    "role": "system",
                    "content": """あなたは親切で知識豊富なAIアシスタントです。ユーザーの質問に対して実行した処理の結果を基に、自然で分かりやすい日本語で直接的な回答をしてください。

重要なガイドライン：
- IDなどの個人情報は含めない
- ユーザーの元の質問に対する明確で具体的な回答を提供する
- 実行結果から得られた情報を整理して分かりやすく提示する
- 成功した場合は結果を具体的に示し、失敗した場合は理由と対処法を説明する
- 技術的な詳細は避け、ユーザーにとって価値のある情報に焦点を当てる
- 自然で親しみやすい口調で、簡潔かつ明確に回答する
- JSON形式ではなく、自然な文章で回答する""",
                },
                {
                    "role": "user",
                    "content": f"""ユーザーの質問: "{prompt}"

実行した処理の結果:
- 実行したアクション数: {total_actions}
- 成功したアクション: {successful_actions}
- 失敗したアクション: {failed_actions}
- 全体のステータス: {overall_status}
- 処理の信頼度: {operator_response.confidence}

オペレーターの分析: {operator_response.analysis}

各アクションの詳細結果:
{chr(10).join([f"- {item['action_type']}: {'成功' if item['success'] else '失敗'} - {item['description']}" + (f" (エラー: {item['error']})" if item["error"] else "") for item in results_data])}

実際に取得されたデータ:
{chr(10).join([f"- {item['description']}: {item['data']}" for item in results_data if item["success"] and item["data"] is not None])}

この情報を基に、ユーザーの質問「{prompt}」に対する適切で自然な返答を生成してください。ユーザーが求めている具体的な情報や回答を中心に、分かりやすく説明してください。""",
                },
            ],
            temperature=0.7,
            max_tokens=800,
        )

        return {
            "total_actions": total_actions,
            "successful_actions": successful_actions,
            "failed_actions": failed_actions,
            "success_rate": round(success_rate, 2),
            "overall_status": overall_status,
            "confidence": operator_response.confidence,
            "results_data": results_data,
            "results_text": results_text,
        }
