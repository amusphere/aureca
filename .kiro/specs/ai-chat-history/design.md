# 設計書

## 概要

AIチャット履歴機能は、ユーザーとAIの会話を永続化し、継続的な対話を可能にするシステムです。既存のAIハブ・スポークシステムと統合し、会話のコンテキストを保持しながら自然な対話体験を提供します。

## アーキテクチャ

### システム構成

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│                 │    │                 │    │                 │
│ Chat Interface  │◄──►│ Chat Router     │◄──►│ chat_threads    │
│ Message List    │    │ Chat Service    │    │ chat_messages   │
│ Pagination      │    │ Chat Repository │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   AI Hub        │
                       │ (with history)  │
                       └─────────────────┘
```

### レイヤー構造

1. **Router Layer** (`routers/api/chat.py`)
   - HTTPエンドポイントの定義
   - リクエスト/レスポンスの処理
   - 認証とバリデーション

2. **Service Layer** (`services/chat_service.py`)
   - ビジネスロジックの実装
   - AIハブとの統合
   - 履歴管理とコンテキスト生成

3. **Repository Layer** (`repositories/chat_thread.py`, `repositories/chat_message.py`)
   - データベースアクセス
   - CRUD操作
   - クエリ最適化

4. **Model Layer** (`models/chat.py`)
   - Pydanticモデル定義
   - リクエスト/レスポンス検証

## コンポーネントと インターフェース

### データベーススキーマ

#### ChatThread テーブル
```python
class ChatThread(SQLModel, table=True):
    __tablename__ = "chat_threads"

    id: int = Field(primary_key=True)
    uuid: str = Field(default_factory=lambda: str(uuid4()), index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    title: str | None = Field(nullable=True)  # 自動生成されるタイトル
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

    # リレーションシップ
    user: User = Relationship(back_populates="chat_threads")
    messages: list["ChatMessage"] = Relationship(
        back_populates="thread",
        cascade_delete=True,
        sa_relationship_kwargs={"order_by": "ChatMessage.created_at"}
    )
```

#### ChatMessage テーブル
```python
class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_messages"

    id: int = Field(primary_key=True)
    uuid: str = Field(default_factory=lambda: str(uuid4()), index=True)
    thread_id: int = Field(foreign_key="chat_threads.id", index=True)
    role: str = Field(index=True)  # OpenAI API準拠
    content: str
    created_at: float = Field(default_factory=time.time, index=True)

    # リレーションシップ
    thread: ChatThread = Relationship(back_populates="messages")
```

### APIエンドポイント

#### 1. GET /api/chat/threads
```python
@router.get("/threads", response_model=list[ChatThreadResponse])
async def get_chat_threads(
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
) -> list[ChatThreadResponse]:
    """ユーザーのチャットスレッド一覧を取得"""
```

#### 2. POST /api/chat/threads
```python
@router.post("/threads", response_model=ChatThreadResponse)
async def create_chat_thread(
    request: CreateChatThreadRequest,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
) -> ChatThreadResponse:
    """新しいチャットスレッドを作成"""
```

#### 3. GET /api/chat/threads/{uuid}
```python
@router.get("/threads/{thread_uuid}", response_model=ChatThreadWithMessagesResponse)
async def get_chat_thread(
    thread_uuid: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
) -> ChatThreadWithMessagesResponse:
    """チャットスレッドとメッセージを取得（ページネーション付き）"""
```

#### 4. POST /api/chat/threads/{uuid}/messages
```python
@router.post("/threads/{thread_uuid}/messages", response_model=ChatMessageResponse)
async def send_message(
    thread_uuid: str,
    request: SendMessageRequest,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
) -> ChatMessageResponse:
    """メッセージを送信してAI応答を取得"""
```

#### 5. DELETE /api/chat/threads/{uuid}
```python
@router.delete("/threads/{thread_uuid}")
async def delete_chat_thread(
    thread_uuid: str,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
) -> dict[str, str]:
    """チャットスレッドを削除（ハードデリート）"""
```

### サービス層インターフェース

#### ChatService
```python
class ChatService:
    def __init__(self, session: Session):
        self.session = session
        self.thread_repository = ChatThreadRepository()
        self.message_repository = ChatMessageRepository()

    async def get_or_create_default_thread(self, user_id: int) -> ChatThread:
        """ユーザーのデフォルトスレッドを取得または作成"""

    async def send_message_with_ai_response(
        self,
        thread_uuid: str,
        user_message: str,
        user: User
    ) -> tuple[ChatMessage, ChatMessage]:
        """メッセージ送信とAI応答の処理"""

    async def get_conversation_context(
        self,
        thread_id: int,
        limit: int = 30
    ) -> list[dict[str, str]]:
        """AIプロンプト用の会話履歴を取得"""

    async def generate_thread_title(
        self,
        thread_id: int
    ) -> str:
        """会話内容からスレッドタイトルを自動生成"""
```

### リポジトリ層インターフェース

#### ChatThreadRepository
```python
class ChatThreadRepository:
    async def find_by_user_id(self, session: Session, user_id: int) -> list[ChatThread]:
        """ユーザーのスレッド一覧を取得"""

    async def find_by_uuid(
        self,
        session: Session,
        uuid: str,
        user_id: int
    ) -> ChatThread | None:
        """UUIDでスレッドを取得（ユーザー権限チェック付き）"""

    async def create(
        self,
        session: Session,
        user_id: int,
        title: str | None = None
    ) -> ChatThread:
        """新しいスレッドを作成"""

    async def delete_by_uuid(
        self,
        session: Session,
        uuid: str,
        user_id: int
    ) -> bool:
        """スレッドを削除（権限チェック付き）"""
```

#### ChatMessageRepository
```python
class ChatMessageRepository:
    async def find_by_thread_id_paginated(
        self,
        session: Session,
        thread_id: int,
        page: int = 1,
        per_page: int = 30
    ) -> tuple[list[ChatMessage], int]:
        """スレッドのメッセージをページネーション付きで取得"""

    async def get_recent_messages_for_context(
        self,
        session: Session,
        thread_id: int,
        limit: int = 30
    ) -> list[ChatMessage]:
        """AIコンテキスト用の最新メッセージを取得"""

    async def create(
        self,
        session: Session,
        thread_id: int,
        role: str,
        content: str
    ) -> ChatMessage:
        """新しいメッセージを作成"""
```

## データモデル

### Pydanticモデル

#### リクエストモデル
```python
class CreateChatThreadRequest(BaseModel):
    title: str | None = None

class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
```

#### レスポンスモデル
```python
class ChatThreadResponse(BaseModel):
    uuid: str
    title: str | None
    created_at: float
    updated_at: float
    message_count: int

class ChatMessageResponse(BaseModel):
    uuid: str
    role: str
    content: str
    created_at: float

class ChatThreadWithMessagesResponse(BaseModel):
    thread: ChatThreadResponse
    messages: list[ChatMessageResponse]
    pagination: PaginationInfo

class PaginationInfo(BaseModel):
    page: int
    per_page: int
    total_messages: int
    total_pages: int
    has_next: bool
    has_prev: bool
```

## エラーハンドリング

### エラータイプと対応

1. **認証エラー (401)**
   - 未認証ユーザーのアクセス
   - 無効なトークン

2. **認可エラー (403)**
   - 他ユーザーのスレッドへのアクセス
   - 権限不足

3. **リソース不存在エラー (404)**
   - 存在しないスレッドUUID
   - 削除済みスレッド

4. **バリデーションエラー (422)**
   - 不正なリクエストパラメータ
   - メッセージ長制限超過

5. **システムエラー (500)**
   - データベース接続エラー
   - AI API呼び出しエラー

### エラーレスポンス形式
```python
class ErrorResponse(BaseModel):
    error: str
    error_code: str
    details: dict[str, Any] | None = None
```

## テスト戦略

### ユニットテスト
- **Repository Layer**: データベース操作の正確性
- **Service Layer**: ビジネスロジックの検証
- **Model Layer**: バリデーションルールの確認

### 統合テスト
- **API Endpoints**: エンドツーエンドの動作確認
- **AI Integration**: AIハブとの連携テスト
- **Database Transactions**: トランザクション整合性

### パフォーマンステスト
- **Pagination**: 大量メッセージでのページネーション性能
- **Context Generation**: 履歴取得の応答時間
- **Concurrent Access**: 同時アクセス時の動作

### テストデータ
```python
# テスト用のファクトリー関数
def create_test_thread(user_id: int, message_count: int = 10) -> ChatThread:
    """テスト用のスレッドとメッセージを作成"""

def create_test_conversation(
    thread_id: int,
    exchanges: int = 5
) -> list[ChatMessage]:
    """テスト用の会話履歴を作成"""
```

## セキュリティ考慮事項

### データアクセス制御
- **ユーザー分離**: 各ユーザーは自分のデータのみアクセス可能
- **UUID使用**: 推測困難な識別子でリソース保護
- **認証必須**: すべてのエンドポイントで認証チェック

### データ保護
- **入力検証**: SQLインジェクション対策
- **出力エスケープ**: XSS対策
- **レート制限**: API乱用防止

### プライバシー
- **データ暗号化**: 機密情報の暗号化保存
- **ログ制限**: 個人情報のログ出力制限
- **データ削除**: ハードデリートによる完全削除

## パフォーマンス最適化

### データベース最適化
```sql
-- インデックス設計
CREATE INDEX idx_chat_threads_user_id ON chat_threads(user_id);
CREATE INDEX idx_chat_threads_uuid ON chat_threads(uuid);
CREATE INDEX idx_chat_messages_thread_id ON chat_messages(thread_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at);
CREATE INDEX idx_chat_messages_thread_created ON chat_messages(thread_id, created_at);
```

### クエリ最適化
- **ページネーション**: OFFSET/LIMIT最適化
- **JOIN最小化**: 必要な場合のみリレーション取得
- **バッチ処理**: 複数メッセージの一括挿入

### キャッシュ戦略
- **スレッド情報**: 頻繁にアクセスされるスレッド情報のキャッシュ
- **コンテキスト**: AI用コンテキストの一時キャッシュ
- **ページネーション**: ページ情報のキャッシュ

## 運用・監視

### ログ設計
```python
# 構造化ログの例
logger.info(
    "Chat message sent",
    extra={
        "user_id": user.id,
        "thread_uuid": thread.uuid,
        "message_length": len(content),
        "ai_response_time": response_time,
    }
)
```

### メトリクス
- **メッセージ送信数**: 日次/月次の利用統計
- **応答時間**: AI応答の平均時間
- **エラー率**: API呼び出しの成功率
- **アクティブスレッド数**: 利用中のスレッド数

### アラート
- **高エラー率**: エラー率が閾値を超過
- **応答時間遅延**: AI応答時間が異常に長い
- **データベース接続**: DB接続エラーの発生

## 今後の拡張性

### 機能拡張
- **マルチスレッド対応**: ユーザーごとの複数スレッド管理
- **スレッド検索**: 会話内容での検索機能
- **エクスポート機能**: 会話履歴のエクスポート
- **共有機能**: スレッドの他ユーザーとの共有

### 技術的拡張
- **リアルタイム通信**: WebSocketによるリアルタイム更新
- **ストリーミング応答**: AI応答のストリーミング配信
- **分散処理**: 大規模利用時のスケーリング対応
- **AI モデル切り替え**: 複数AIモデルの選択機能