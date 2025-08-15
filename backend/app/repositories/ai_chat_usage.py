from datetime import datetime

from sqlalchemy import and_, text
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session, select

from app.schema import AIChatUsage


class AIChatUsageRepository:
    """Optimized repository for AI chat usage management with lightweight database operations"""

    @staticmethod
    def get_current_usage_count(session: Session, user_id: int, usage_date: str) -> int:
        """
        高速な利用数取得クエリ - 単一クエリで利用数のみを取得
        要件: 3.3 - 利用数を確認する場合、システムは単一のクエリで高速に結果を返す
        """
        stmt = select(AIChatUsage.usage_count).where(
            and_(AIChatUsage.user_id == user_id, AIChatUsage.usage_date == usage_date)
        )
        result = session.exec(stmt).first()
        return result if result is not None else 0

    @staticmethod
    def increment_usage_count(session: Session, user_id: int, usage_date: str) -> int:
        """
        効率的な利用数インクリメント処理 - UPSERT操作で高速処理
        要件: 3.1 - ユーザーがAIChatを利用する場合、システムは日次利用カウンターを1増加させる
        要件: 3.4 - 最小限のテーブル構造を使用する
        """
        current_timestamp = datetime.now().timestamp()

        # PostgreSQL UPSERT (ON CONFLICT) を使用した効率的な処理
        stmt = insert(AIChatUsage).values(
            user_id=user_id,
            usage_date=usage_date,
            usage_count=1,
            created_at=current_timestamp,
            updated_at=current_timestamp,
        )

        # 既存レコードがある場合は usage_count を +1、updated_at を更新
        stmt = stmt.on_conflict_do_update(
            index_elements=["user_id", "usage_date"],
            set_={"usage_count": AIChatUsage.usage_count + 1, "updated_at": current_timestamp},
        ).returning(AIChatUsage.usage_count)

        result = session.exec(stmt).first()
        session.commit()
        return result

    @staticmethod
    def get_daily_usage_record(session: Session, user_id: int, usage_date: str) -> AIChatUsage | None:
        """
        日次利用記録の取得 - 複合インデックスを活用した高速検索
        """
        stmt = select(AIChatUsage).where(and_(AIChatUsage.user_id == user_id, AIChatUsage.usage_date == usage_date))
        return session.exec(stmt).first()

    @staticmethod
    def reset_daily_usage(session: Session, user_id: int, usage_date: str) -> None:
        """
        日次リセット処理の最適化 - 特定ユーザーの特定日付のリセット
        要件: 3.2 - 日付が変わる場合、システムは利用カウンターを0にリセットする
        """
        stmt = select(AIChatUsage).where(and_(AIChatUsage.user_id == user_id, AIChatUsage.usage_date == usage_date))
        usage_record = session.exec(stmt).first()

        if usage_record:
            usage_record.usage_count = 0
            usage_record.updated_at = datetime.now().timestamp()
            session.commit()

    @staticmethod
    def bulk_reset_daily_usage(session: Session, usage_date: str) -> int:
        """
        日次リセット処理の最適化 - 全ユーザーの特定日付を一括リセット
        要件: 3.2 - 日付が変わる場合、システムは利用カウンターを0にリセットする
        """
        # 効率的な一括更新クエリ
        stmt = text("""
            UPDATE ai_chat_usage
            SET usage_count = 0, updated_at = :updated_at
            WHERE usage_date = :usage_date AND usage_count > 0
        """)

        result = session.exec(stmt, {"updated_at": datetime.now().timestamp(), "usage_date": usage_date})
        session.commit()
        return result.rowcount

    @staticmethod
    def get_usage_stats(session: Session, user_id: int, usage_date: str) -> dict:
        """
        利用統計情報の取得 - 必要最小限の情報を高速取得
        """
        stmt = select(AIChatUsage.usage_count, AIChatUsage.updated_at).where(
            and_(AIChatUsage.user_id == user_id, AIChatUsage.usage_date == usage_date)
        )
        result = session.exec(stmt).first()

        if result:
            usage_count, updated_at = result
            return {"usage_count": usage_count, "updated_at": updated_at, "usage_date": usage_date}
        else:
            return {"usage_count": 0, "updated_at": None, "usage_date": usage_date}

    @staticmethod
    def cleanup_old_records(session: Session, cutoff_date: str) -> int:
        """
        古いレコードのクリーンアップ - データベース負荷軽減
        要件: 3.4 - データベース負荷を軽減する場合、システムは最小限のテーブル構造を使用する
        """
        stmt = text("""
            DELETE FROM ai_chat_usage
            WHERE usage_date < :cutoff_date
        """)

        result = session.exec(stmt, {"cutoff_date": cutoff_date})
        session.commit()
        return result.rowcount

    @staticmethod
    def get_usage_history(session: Session, user_id: int, limit: int = 30) -> list[AIChatUsage]:
        """
        利用履歴の取得 - インデックスを活用した効率的な検索
        """
        stmt = (
            select(AIChatUsage)
            .where(AIChatUsage.user_id == user_id)
            .order_by(AIChatUsage.usage_date.desc())
            .limit(limit)
        )
        return list(session.exec(stmt).all())

    @staticmethod
    def create_daily_usage(session: Session, user_id: int, usage_date: str, usage_count: int = 1) -> AIChatUsage:
        """
        日次利用記録の作成 - テスト用のヘルパーメソッド
        """
        from datetime import datetime

        from sqlalchemy.dialects.postgresql import insert

        current_timestamp = datetime.now().timestamp()

        # Create new record with specified usage_count
        stmt = insert(AIChatUsage).values(
            user_id=user_id,
            usage_date=usage_date,
            usage_count=usage_count,
            created_at=current_timestamp,
            updated_at=current_timestamp,
        )

        # If record exists, update it with the new count
        stmt = stmt.on_conflict_do_update(
            index_elements=["user_id", "usage_date"],
            set_={"usage_count": usage_count, "updated_at": current_timestamp},
        )

        session.exec(stmt)
        session.commit()

        # Return the created/updated record
        return AIChatUsageRepository.get_daily_usage_record(session, user_id, usage_date)


# 後方互換性のための関数エイリアス（既存コードとの互換性維持）
def get_current_usage_count(session: Session, user_id: int, usage_date: str) -> int:
    """Backward compatibility wrapper"""
    return AIChatUsageRepository.get_current_usage_count(session, user_id, usage_date)


def increment_usage_count(session: Session, user_id: int, usage_date: str) -> int:
    """Backward compatibility wrapper"""
    return AIChatUsageRepository.increment_usage_count(session, user_id, usage_date)


def get_daily_usage(session: Session, user_id: int, usage_date: str) -> AIChatUsage | None:
    """Backward compatibility wrapper"""
    return AIChatUsageRepository.get_daily_usage_record(session, user_id, usage_date)


def get_usage_history(session: Session, user_id: int, limit: int = 30) -> list[AIChatUsage]:
    """Backward compatibility wrapper"""
    return AIChatUsageRepository.get_usage_history(session, user_id, limit)


def create_daily_usage(session: Session, user_id: int, usage_date: str, usage_count: int = 1) -> AIChatUsage:
    """Backward compatibility wrapper for creating daily usage record"""
    from datetime import datetime

    from sqlalchemy.dialects.postgresql import insert

    current_timestamp = datetime.now().timestamp()

    # Create new record with specified usage_count
    stmt = insert(AIChatUsage).values(
        user_id=user_id,
        usage_date=usage_date,
        usage_count=usage_count,
        created_at=current_timestamp,
        updated_at=current_timestamp,
    )

    # If record exists, update it with the new count
    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id", "usage_date"],
        set_={"usage_count": usage_count, "updated_at": current_timestamp},
    )

    session.exec(stmt)
    session.commit()

    # Return the created/updated record
    return AIChatUsageRepository.get_daily_usage_record(session, user_id, usage_date)


def update_usage_count(session: Session, user_id: int, usage_date: str, usage_count: int) -> AIChatUsage:
    """Backward compatibility wrapper for updating usage count"""
    from datetime import datetime

    from sqlalchemy.dialects.postgresql import insert

    current_timestamp = datetime.now().timestamp()

    # Update existing record or create new one with specified count
    stmt = insert(AIChatUsage).values(
        user_id=user_id,
        usage_date=usage_date,
        usage_count=usage_count,
        created_at=current_timestamp,
        updated_at=current_timestamp,
    )

    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id", "usage_date"],
        set_={"usage_count": usage_count, "updated_at": current_timestamp},
    )

    session.exec(stmt)
    session.commit()

    # Return the updated record
    return AIChatUsageRepository.get_daily_usage_record(session, user_id, usage_date)
