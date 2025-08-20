import base64
from datetime import datetime

import requests
from cryptography.fernet import Fernet
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from sqlmodel import Session

# Import Google OAuth configuration
from app.config.auth import GoogleOAuthConfig
from app.models.google_oauth import GoogleCallbackRequest
from app.repositories import google_oauth_token
from app.schema import GoogleOAuthToken

# Google OAuth設定
GOOGLE_CLIENT_ID = GoogleOAuthConfig.CLIENT_ID
GOOGLE_CLIENT_SECRET = GoogleOAuthConfig.CLIENT_SECRET
GOOGLE_REDIRECT_URI = GoogleOAuthConfig.REDIRECT_URI
ENCRYPTION_KEY = GoogleOAuthConfig.ENCRYPTION_KEY

# Google Calendar API のスコープ
SCOPES = [
    "openid",  # Google が自動で追加するため明示的に含める
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]


class GoogleOauthService:
    def __init__(self, session: Session | None = None):
        # 環境変数のチェック
        if not ENCRYPTION_KEY:
            raise ValueError("GOOGLE_OAUTH_ENCRYPTION_KEY environment variable is required")
        if not GOOGLE_CLIENT_ID:
            raise ValueError("GOOGLE_CLIENT_ID environment variable is required")
        if not GOOGLE_CLIENT_SECRET:
            raise ValueError("GOOGLE_CLIENT_SECRET environment variable is required")

        # Convert hex string to bytes, then base64 encode for Fernet
        if len(ENCRYPTION_KEY) == 64:  # Hex string (32 bytes * 2)
            key_bytes = bytes.fromhex(ENCRYPTION_KEY)
            fernet_key = base64.urlsafe_b64encode(key_bytes)
            self.fernet = Fernet(fernet_key)
        else:
            # Assume it's already a proper Fernet key
            self.fernet = Fernet(ENCRYPTION_KEY.encode())
        self.session = session

    def _encrypt_token(self, token: str) -> str:
        """トークンを暗号化"""
        return self.fernet.encrypt(token.encode()).decode()

    def _decrypt_token(self, encrypted_token: str) -> str:
        """トークンを復号化"""
        return self.fernet.decrypt(encrypted_token.encode()).decode()

    def get_auth_url(self, user_id: int) -> str:
        """Google OAuth認証URLを生成"""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [GOOGLE_REDIRECT_URI],
                }
            },
            scopes=SCOPES,
        )
        flow.redirect_uri = GOOGLE_REDIRECT_URI

        # ユーザーIDをstateに含める
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",  # 強制的に同意画面を表示してrefresh_tokenを確実に取得
            state=str(user_id),
        )

        return auth_url

    def get_user_info(self, credentials: Credentials) -> dict:
        """OAuth2 userinfo エンドポイントを使用してユーザー情報を取得"""
        userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"

        headers = {"Authorization": f"Bearer {credentials.token}"}
        response = requests.get(userinfo_url, headers=headers)

        if response.status_code != 200:
            raise Exception(f"Failed to fetch user info: {response.status_code} {response.text}")

        return response.json()

    def save_oauth_tokens(self, callback_request: GoogleCallbackRequest):
        """認証コードをアクセストークンに交換し、データベースに保存"""
        user_id = int(callback_request.state)
        code = callback_request.code

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [GOOGLE_REDIRECT_URI],
                }
            },
            scopes=SCOPES,
        )
        flow.redirect_uri = GOOGLE_REDIRECT_URI

        # 認証コードでトークンを取得
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # OAuth2 userinfo エンドポイントを使用してユーザー情報を取得
        user_info = self.get_user_info(credentials)

        # トークンをデータベースに保存
        self.store_oauth_tokens(
            user_id=user_id,
            credentials=credentials,
            google_user_id=user_info.get("id"),
            google_email=user_info.get("email"),
        )

    def store_oauth_tokens(
        self,
        user_id: int,
        credentials: Credentials,
        google_user_id: str = None,
        google_email: str = None,
    ) -> GoogleOAuthToken:
        """OAuth認証情報をデータベースに保存（アップサート方式）"""
        expires_at = None
        if credentials.expiry:
            expires_at = credentials.expiry.timestamp()

        return google_oauth_token.upsert_oauth_token(
            user_id=user_id,
            access_token=self._encrypt_token(credentials.token),
            refresh_token=(self._encrypt_token(credentials.refresh_token) if credentials.refresh_token else None),
            expires_at=expires_at,
            scope=" ".join(credentials.scopes) if credentials.scopes else None,
            google_user_id=google_user_id,
            google_email=google_email,
            session=self.session,
        )

    def get_credentials(self, user_id: int) -> Credentials | None:
        """ユーザーのGoogle認証情報を取得"""
        oauth_token = google_oauth_token.find_active_token_by_user_id(user_id=user_id, session=self.session)

        if not oauth_token:
            return None

        # 復号化してCredentialsオブジェクトを作成
        access_token = self._decrypt_token(oauth_token.access_token)
        refresh_token = None
        if oauth_token.refresh_token:
            refresh_token = self._decrypt_token(oauth_token.refresh_token)

        # refresh_tokenが存在しない場合、適切なエラーメッセージと共にNoneを返す
        if not refresh_token:
            raise ValueError("Refresh token not found. Please re-authenticate to grant access to your Google Calendar.")

        credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            scopes=oauth_token.scope.split() if oauth_token.scope else None,
        )

        # トークンの有効期限をチェック
        if oauth_token.expires_at:
            credentials.expiry = datetime.fromtimestamp(oauth_token.expires_at)

        # トークンが期限切れの場合、リフレッシュを試行
        if credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
                # 更新されたトークンを保存
                self.update_tokens(oauth_token.id, credentials)
            except Exception as e:
                raise ValueError(f"Failed to refresh access token: {str(e)}. Please re-authenticate.") from e

        return credentials

    def update_tokens(self, token_id: int, credentials: Credentials):
        """トークンを更新"""
        expires_at = credentials.expiry.timestamp() if credentials.expiry else None

        google_oauth_token.update_token_data(
            token_id=token_id,
            access_token=self._encrypt_token(credentials.token),
            refresh_token=(self._encrypt_token(credentials.refresh_token) if credentials.refresh_token else None),
            expires_at=expires_at,
            session=self.session,
        )

    def revoke_access(self, user_id: int):
        """ユーザーのアクセスを取り消し（レコードを削除）"""
        return google_oauth_token.delete_all_active_tokens_by_user_id(user_id=user_id, session=self.session)
