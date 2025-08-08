"""
AIチャット利用制限の定数定義

このモジュールは、プラン別のAIチャット利用制限をハードコーディングされた定数として管理します。
複雑な設定ファイルを使用せず、高速で保守性の高い制限値管理を提供します。
"""


class PlanLimits:
    """AIチャット利用制限の定数定義クラス

    各プランの利用制限値をハードコーディングされた定数として管理し、
    高速なアクセスと保守性の向上を実現します。

    プラン別制限値:
    - free: 0回 (利用不可)
    - standard: 10回 (1日10回まで)
    """

    # プラン別制限値の定数定義
    FREE = 0  # freeプラン: 利用不可
    STANDARD = 10  # standardプラン: 1日10回まで

    # プラン名と制限値のマッピング
    PLAN_LIMITS: dict[str, int] = {
        "free": FREE,
        "standard": STANDARD,
    }

    @classmethod
    def get_limit(cls, plan_name: str) -> int:
        """プラン名から制限値を取得

        Args:
            plan_name (str): プラン名 (大文字小文字を区別しない)

        Returns:
            int: プランの利用制限値。無効なプラン名の場合はfreeプランの制限値(0)を返す

        Examples:
            >>> PlanLimits.get_limit("standard")
            10
            >>> PlanLimits.get_limit("STANDARD")
            10
            >>> PlanLimits.get_limit("free")
            0
            >>> PlanLimits.get_limit("invalid")
            0
        """
        if not isinstance(plan_name, str):
            return cls.FREE

        return cls.PLAN_LIMITS.get(plan_name.lower(), cls.FREE)

    @classmethod
    def is_valid_plan(cls, plan_name: str) -> bool:
        """プラン名の有効性をチェック

        Args:
            plan_name (str): チェックするプラン名

        Returns:
            bool: 有効なプラン名の場合True、無効な場合False

        Examples:
            >>> PlanLimits.is_valid_plan("standard")
            True
            >>> PlanLimits.is_valid_plan("free")
            True
            >>> PlanLimits.is_valid_plan("invalid")
            False
            >>> PlanLimits.is_valid_plan("")
            False
        """
        if not isinstance(plan_name, str) or not plan_name.strip():
            return False

        return plan_name.lower() in cls.PLAN_LIMITS

    @classmethod
    def get_available_plans(cls) -> list[str]:
        """利用可能なプラン名の一覧を取得

        Returns:
            List[str]: 利用可能なプラン名のリスト

        Examples:
            >>> PlanLimits.get_available_plans()
            ['free', 'standard']
        """
        return list(cls.PLAN_LIMITS.keys())

    @classmethod
    def get_plan_info(cls, plan_name: str) -> dict[str, any]:
        """プランの詳細情報を取得

        Args:
            plan_name (str): プラン名

        Returns:
            Dict[str, any]: プランの詳細情報 (名前、制限値、有効性)

        Examples:
            >>> PlanLimits.get_plan_info("standard")
            {'name': 'standard', 'limit': 10, 'is_valid': True}
            >>> PlanLimits.get_plan_info("invalid")
            {'name': 'invalid', 'limit': 0, 'is_valid': False}
        """
        return {"name": plan_name, "limit": cls.get_limit(plan_name), "is_valid": cls.is_valid_plan(plan_name)}
