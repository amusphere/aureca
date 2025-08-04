from datetime import datetime

from sqlmodel import Session, select

from app.schema import GoogleOAuthToken


def find_active_token_by_user_id(
    user_id: int,
    session: Session,
) -> GoogleOAuthToken | None:
    """ユーザーIDでアクティブなトークンを検索"""
    return session.exec(
        select(GoogleOAuthToken).where(
            GoogleOAuthToken.user_id == user_id,
        )
    ).first()


def find_all_active_tokens_by_user_id(
    user_id: int,
    session: Session,
) -> list[GoogleOAuthToken]:
    """ユーザーIDでアクティブなトークンを全て検索"""
    return session.exec(
        select(GoogleOAuthToken).where(
            GoogleOAuthToken.user_id == user_id,
        )
    ).all()


def create_oauth_token(
    oauth_token: GoogleOAuthToken,
    session: Session,
) -> GoogleOAuthToken:
    """新しいOAuthトークンを作成"""
    session.add(oauth_token)
    session.commit()
    session.refresh(oauth_token)
    return oauth_token


def update_token_data(
    token_id: int,
    access_token: str,
    session: Session,
    refresh_token: str | None = None,
    expires_at: float | None = None,
) -> GoogleOAuthToken | None:
    """トークンデータを更新"""
    oauth_token = session.get(GoogleOAuthToken, token_id)
    if oauth_token:
        oauth_token.access_token = access_token
        if refresh_token:
            oauth_token.refresh_token = refresh_token
        oauth_token.expires_at = expires_at
        oauth_token.updated_at = datetime.now().timestamp()

        session.add(oauth_token)
        session.commit()
        session.refresh(oauth_token)
        return oauth_token
    return None


def delete_all_active_tokens_by_user_id(
    user_id: int,
    session: Session,
) -> int:
    """ユーザーのアクティブなトークンを全て物理削除"""
    tokens = find_all_active_tokens_by_user_id(user_id, session)
    count = len(tokens)
    for token in tokens:
        session.delete(token)
    session.commit()
    return count


def upsert_oauth_token(
    session: Session,
    user_id: int,
    access_token: str,
    refresh_token: str | None = None,
    expires_at: float | None = None,
    scope: str | None = None,
    google_user_id: str | None = None,
    google_email: str | None = None,
) -> GoogleOAuthToken:
    """OAuth トークンをアップサート（存在すれば更新、なければ作成）"""
    existing_token = find_active_token_by_user_id(user_id, session)

    if existing_token:
        # 既存のトークンを更新
        existing_token.access_token = access_token
        existing_token.refresh_token = refresh_token
        existing_token.expires_at = expires_at
        existing_token.scope = scope
        existing_token.google_user_id = google_user_id
        existing_token.google_email = google_email
        existing_token.updated_at = datetime.now().timestamp()

        session.add(existing_token)
        session.commit()
        session.refresh(existing_token)
        return existing_token
    else:
        # 新しいトークンを作成
        oauth_token = GoogleOAuthToken(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            scope=scope,
            google_user_id=google_user_id,
            google_email=google_email,
        )
        return create_oauth_token(oauth_token, session)
