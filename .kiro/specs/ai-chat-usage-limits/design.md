# 設計書

## 概要

AIチャット上限システムのリファクタリングにより、複雑な設定ファイルベースのシステムをシンプルなハードコーディング方式に変更します。ClerkのAPIからユーザープランを取得し、軽量なデータベース構造で利用数を管理する高速で保守性の高いシステムを構築します。既存のアーキテクチャに従い、Router → Service → Repository → Database の階層構造を維持しながら実装します。

## アーキテクチャ

### システム構成図

```mermaid
graph TB
    subgraph "Frontend"
        UI[AIChatModal]
        Hook[useAIChatUsage Hook]
        API[/api/ai/usage API Route]
    end

    subgraph "Backend"
        Router[AI Router]
        Service[AI Usage Service]
        Clerk[Clerk API Client]
        Repo[Usage Repository]
        DB[(PostgreSQL)]
        Constants[Plan Limits Constants]
    end

    subgraph "External"
        ClerkAPI[Clerk API]
    end

    UI --> Hook
    Hook --> API
    API --> Router
    Router --> Service
    Service --> Clerk
    Service --> Repo
    Service --> Constants
    Clerk --> ClerkAPI
    Repo --> DB

    UI -.->|利用回数表示| Hook
    Service -.->|プラン取得| Clerk
    Service -.->|制限値取得| Constants
```

### データフロー

1. **プラン取得**: ユーザーID → Clerk API → プラン情報取得 → フォールバック処理
2. **制限値取得**: プラン名 → ハードコーディング定数 → 制限値返却
3. **利用数確認**: ユーザーID + 日付 → データベース → 現在の利用数
4. **利用可否判定**: 現在利用数 + 制限値 → 判定結果
5. **利用記録**: AIChatリクエスト → 利用数インクリメント → データベース更新
6. **UI表示**: 残り回数計算 → レスポンシブUI更新

## コンポーネントとインターフェース

### データベーススキーマ

```sql
-- シンプル化されたテーブル: ai_chat_usage
CREATE TABLE ai_chat_usage (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    usage_date DATE NOT NULL,
    usage_count INTEGER NOT NULL DEFAULT 0,
    created_at FLOAT NOT NULL,
    updated_at FLOAT NOT NULL,

    -- 高速検索のための複合インデックス
    UNIQUE(user_id, usage_date),
    INDEX idx_user_date_fast (user_id, usage_date)
);
```

### バックエンドインターフェース

#### SQLModelスキーマ
```python
class AIChatUsage(SQLModel, table=True):
    __tablename__ = "ai_chat_usage"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    usage_date: str = Field(index=True)  # YYYY-MM-DD形式
    usage_count: int = Field(default=0)
    created_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    updated_at: float = Field(default_factory=lambda: datetime.now().timestamp())

    user: User = Relationship()

# プラン制限の定数定義
class PlanLimits:
    FREE = 0
    STANDARD = 10

    @classmethod
    def get_limit(cls, plan_name: str) -> int:
        """プラン名から制限値を取得"""
        limits = {
            "free": cls.FREE,
            "standard": cls.STANDARD,
        }
        return limits.get(plan_name.lower(), cls.FREE)  # デフォルトはfree
```

#### Pydanticモデル
```python
class AIChatUsageResponse(BaseModel):
    remaining_count: int
    daily_limit: int
    reset_time: str  # ISO 8601形式
    can_use_chat: bool

class AIChatUsageError(BaseModel):
    error: str
    error_code: str
    remaining_count: int
    reset_time: str
```

#### サービス層インターフェース
```python
class AIChatUsageService:
    async def can_use_chat(self, user_id: int) -> bool
    async def get_user_plan(self, user_id: int) -> str
    async def get_current_usage(self, user_id: int) -> int
    async def increment_usage(self, user_id: int) -> AIChatUsageResponse
    async def get_usage_stats(self, user_id: int) -> AIChatUsageResponse

class ClerkService:
    async def get_user_plan(self, user_id: int) -> str
    async def has_subscription(self, user_id: int, plan_name: str) -> bool
```

### フロントエンドインターフェース

#### TypeScript型定義
```typescript
interface AIChatUsage {
  remainingCount: number;
  dailyLimit: number;
  resetTime: string;
  canUseChat: boolean;
}

interface AIChatUsageError {
  error: string;
  errorCode: string;
  remainingCount: number;
  resetTime: string;
}
```

#### カスタムフック
```typescript
interface UseAIChatUsageReturn {
  usage: AIChatUsage | null;
  loading: boolean;
  error: AIChatUsageError | null;
  checkUsage: () => Promise<void>;
  refreshUsage: () => Promise<void>;
}

const useAIChatUsage: () => UseAIChatUsageReturn;
```

## データモデル

### プラン制限の定数管理

ハードコーディングされた定数でプラン制限を管理し、高速な処理を実現：

```python
# constants/plan_limits.py
class PlanLimits:
    """AIチャット利用制限の定数定義"""

    # プラン別制限値
    FREE = 0        # 利用不可
    STANDARD = 10   # 1日10回

    # プラン名マッピング
    PLAN_LIMITS = {
        "free": FREE,
        "standard": STANDARD,
    }

    @classmethod
    def get_limit(cls, plan_name: str) -> int:
        """プラン名から制限値を取得（大文字小文字を区別しない）"""
        return cls.PLAN_LIMITS.get(plan_name.lower(), cls.FREE)

    @classmethod
    def is_valid_plan(cls, plan_name: str) -> bool:
        """有効なプラン名かチェック"""
        return plan_name.lower() in cls.PLAN_LIMITS
```

### Clerk API統合

```python
# services/clerk_service.py
class ClerkService:
    """Clerk APIとの統合サービス"""

    def __init__(self):
        self.client = clerk_backend_api.Client(api_key=settings.CLERK_SECRET_KEY)

    async def get_user_plan(self, user_id: int) -> str:
        """ユーザーのサブスクリプションプランを取得"""
        try:
            # Clerk APIからユーザー情報を取得
            user = await self.client.users.get(user_id)

            # サブスクリプション情報をチェック
            if hasattr(user, 'public_metadata') and 'plan' in user.public_metadata:
                return user.public_metadata['plan']

            # フォールバック: freeプラン
            return "free"

        except Exception as e:
            logger.warning(f"Clerk API error for user {user_id}: {e}")
            return "free"  # エラー時はfreeプランにフォールバック
```

### データ整合性とパフォーマンス

- **UNIQUE制約**: `(user_id, usage_date)` で重複防止
- **外部キー制約**: `user_id` でユーザーテーブルとの整合性保証
- **最適化されたインデックス**: `(user_id, usage_date)` での高速検索
- **軽量テーブル構造**: 必要最小限のカラムで高速処理
- **Clerk APIキャッシュ**: プラン情報の一時キャッシュで API呼び出し削減

## エラーハンドリング

### エラー分類と対応

1. **利用制限エラー**
   - エラーコード: `USAGE_LIMIT_EXCEEDED`
   - メッセージ: "本日の利用回数上限（10回）に達しました。明日の00:00にリセットされます。"
   - HTTPステータス: 429 (Too Many Requests)

2. **プラン制限エラー**
   - エラーコード: `PLAN_RESTRICTION`
   - メッセージ: "freeプランではAIChatをご利用いただけません。standardプランにアップグレードしてください。"
   - HTTPステータス: 403 (Forbidden)

3. **Clerk API エラー**
   - エラーコード: `CLERK_API_ERROR`
   - メッセージ: "プラン情報の取得に失敗しました。しばらく後にお試しください。"
   - HTTPステータス: 503 (Service Unavailable)
   - フォールバック: freeプランとして処理継続

4. **システムエラー**
   - エラーコード: `SYSTEM_ERROR`
   - メッセージ: "一時的なエラーが発生しました。しばらく後にお試しください。"
   - HTTPステータス: 500 (Internal Server Error)

### レスポンシブUIデザイン

```typescript
// constants/error_messages.ts
const ErrorMessages = {
  USAGE_LIMIT_EXCEEDED: "本日の利用回数上限（10回）に達しました",
  PLAN_RESTRICTION: "freeプランではAIChatをご利用いただけません",
  CLERK_API_ERROR: "プラン情報の取得に失敗しました",
  SYSTEM_ERROR: "一時的なエラーが発生しました"
} as const;

// components/ui/usage_display.tsx
interface UsageDisplayProps {
  currentUsage: number;
  dailyLimit: number;
  planName: string;
  className?: string;
}

const UsageDisplay: React.FC<UsageDisplayProps> = ({
  currentUsage,
  dailyLimit,
  planName,
  className
}) => {
  return (
    <div className={`
      flex flex-col sm:flex-row items-center justify-between
      p-2 sm:p-4 bg-gray-50 rounded-lg
      text-sm sm:text-base
      ${className}
    `}>
      <span className="text-gray-600 mb-1 sm:mb-0">
        利用回数: {currentUsage}/{dailyLimit === 0 ? '利用不可' : dailyLimit}
      </span>
      <span className="text-xs text-gray-500">
        プラン: {planName}
      </span>
    </div>
  );
};
```

## テスト戦略

### バックエンドテスト

1. **単体テスト**
   - PlanLimits定数クラスの制限値取得テスト
   - ClerkServiceのプラン取得とフォールバック処理テスト
   - AIChatUsageServiceのビジネスロジック検証
   - Repository層のデータベース操作テスト

2. **統合テスト**
   - Clerk API統合の正常系・異常系テスト
   - API エンドポイントの動作確認
   - データベーストランザクションの整合性テスト

3. **パフォーマンステスト**
   - ハードコーディング定数の高速アクセステスト
   - 軽量データベース構造の性能測定
   - Clerk APIレスポンス時間の測定

### フロントエンドテスト

1. **コンポーネントテスト**
   - UsageDisplayコンポーネントのレスポンシブ表示テスト
   - エラーメッセージの表示確認
   - プラン別UI制御のテスト

2. **レスポンシブテスト**
   - モバイル・タブレット・デスクトップでの表示確認
   - 画面サイズ変更時のレイアウト維持テスト
   - タッチインターフェースの動作確認

3. **統合テスト**
   - Clerk認証との統合テスト
   - API通信の正常系・異常系テスト
   - プラン変更時のリアルタイム更新テスト

## SOLID原則の適用

### 単一責任原則（SRP）
- **PlanLimits**: プラン制限値の管理のみ
- **ClerkService**: Clerk API統合のみ
- **AIChatUsageService**: 利用数管理のビジネスロジックのみ
- **AIChatUsageRepository**: データベース操作のみ

### 開放閉鎖原則（OCP）
- 新しいプランの追加は定数の追加のみで対応
- インターフェースを通じた拡張可能な設計

### 依存性逆転原則（DIP）
- サービス層は抽象インターフェースに依存
- 具体的な実装は注入可能な設計

## 実装の優先順位

### Phase 1: コア機能のリファクタリング
1. PlanLimits定数クラスの実装
2. 既存設定ファイルシステムの削除
3. ClerkService統合の実装
4. 軽量データベーススキーマへの移行

### Phase 2: UI/UXの改善
1. レスポンシブUIコンポーネントの実装
2. エラーハンドリングの改善
3. ユーザーフレンドリーなメッセージの実装

### Phase 3: パフォーマンス最適化
1. データベースクエリの最適化
2. Clerk APIキャッシュの実装
3. 不要なコードの削除とクリーンアップ

## 運用・監視

### パフォーマンスメトリクス
- ハードコーディング定数アクセス時間
- データベースクエリ実行時間
- Clerk API レスポンス時間

### 品質メトリクス
- コード複雑度の削減率
- テストカバレッジの維持
- 保守性指標の改善

この設計により、複雑なシステムをシンプルで高速、かつ保守性の高いシステムにリファクタリングし、SOLID原則に基づいたクリーンなアーキテクチャを実現します。