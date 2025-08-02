# 設計書

## 概要

AIChatの利用回数制限機能は、サブスクリプションプランに基づいてユーザーの1日あたりのAIChat利用を制限し、リアルタイムで利用状況を追跡・表示するシステムです。既存のアーキテクチャに従い、Router → Service → Repository → Database の階層構造を維持しながら実装します。

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
        Repo[Usage Repository]
        DB[(PostgreSQL)]
    end

    UI --> Hook
    Hook --> API
    API --> Router
    Router --> Service
    Service --> Repo
    Repo --> DB

    UI -.->|利用回数表示| Hook
    Service -.->|制限チェック| Router
```

### データフロー

1. **利用前チェック**: フロントエンド → バックエンド → 利用回数確認 → 制限判定
2. **利用記録**: AIChatリクエスト → 利用回数インクリメント → データベース更新
3. **状態表示**: フロントエンド → 残り回数取得 → UI更新

## コンポーネントとインターフェース

### データベーススキーマ

```sql
-- 新規テーブル: ai_chat_usage_logs
CREATE TABLE ai_chat_usage_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    usage_date DATE NOT NULL,
    usage_count INTEGER NOT NULL DEFAULT 0,
    created_at FLOAT NOT NULL,
    updated_at FLOAT NOT NULL,

    -- パフォーマンス最適化のためのインデックス
    UNIQUE(user_id, usage_date),
    INDEX idx_user_date (user_id, usage_date),
    INDEX idx_usage_date (usage_date)
);
```

### バックエンドインターフェース

#### SQLModelスキーマ
```python
class AIChatUsageLog(SQLModel, table=True):
    __tablename__ = "ai_chat_usage_logs"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    usage_date: str = Field(index=True)  # YYYY-MM-DD形式
    usage_count: int = Field(default=0)
    created_at: float = Field(default_factory=lambda: datetime.now().timestamp())
    updated_at: float = Field(default_factory=lambda: datetime.now().timestamp())

    user: User = Relationship()
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
    async def check_usage_limit(self, user_id: int) -> AIChatUsageResponse
    async def increment_usage(self, user_id: int) -> AIChatUsageResponse
    async def get_daily_limit(self, user_plan: str) -> int
    async def get_usage_stats(self, user_id: int) -> AIChatUsageResponse
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

### 利用回数制限設定

プラン別制限は設定ファイルまたは環境変数で管理し、将来の拡張性を確保：

```python
# 設定例（環境変数またはconfig.py）
AI_CHAT_LIMITS = {
    "free": 0,      # 利用不可
    "basic": 10,    # 1日10回
    "premium": 50,  # 1日50回（将来の拡張）
    "enterprise": -1  # 無制限（将来の拡張）
}
```

### データ整合性

- **UNIQUE制約**: `(user_id, usage_date)` で重複防止
- **外部キー制約**: `user_id` でユーザーテーブルとの整合性保証
- **インデックス最適化**: 頻繁なクエリパターンに対応

### パフォーマンス考慮

- **日次パーティション**: `usage_date` でのクエリ最適化
- **複合インデックス**: `(user_id, usage_date)` での高速検索
- **キャッシュ戦略**: Redis等での利用回数キャッシュ（将来の拡張）

## エラーハンドリング

### エラー分類と対応

1. **利用制限エラー**
   - エラーコード: `USAGE_LIMIT_EXCEEDED`
   - メッセージ: "本日の利用回数上限に達しました。明日の00:00にリセットされます。"
   - HTTPステータス: 429 (Too Many Requests)

2. **プラン制限エラー**
   - エラーコード: `PLAN_RESTRICTION`
   - メッセージ: "現在のプランではAIChatをご利用いただけません。プランをアップグレードしてください。"
   - HTTPステータス: 403 (Forbidden)

3. **システムエラー**
   - エラーコード: `SYSTEM_ERROR`
   - メッセージ: "一時的なエラーが発生しました。しばらく後にお試しください。"
   - HTTPステータス: 500 (Internal Server Error)

### フロントエンドエラー表示

```typescript
const ErrorMessages = {
  USAGE_LIMIT_EXCEEDED: "本日の利用回数上限に達しました",
  PLAN_RESTRICTION: "現在のプランではご利用いただけません",
  SYSTEM_ERROR: "一時的なエラーが発生しました"
} as const;
```

## テスト戦略

### バックエンドテスト

1. **単体テスト**
   - Repository層: データベース操作の正確性
   - Service層: ビジネスロジックの検証
   - 利用回数計算の境界値テスト

2. **統合テスト**
   - API エンドポイントの動作確認
   - データベーストランザクションの整合性
   - エラーハンドリングの検証

3. **パフォーマンステスト**
   - 大量ユーザーでの利用回数チェック性能
   - データベースクエリの実行時間測定

### フロントエンドテスト

1. **コンポーネントテスト**
   - 利用回数表示の正確性
   - フォーム無効化の動作確認
   - エラーメッセージの表示確認

2. **統合テスト**
   - API通信の正常系・異常系
   - リアルタイム更新の動作確認

3. **E2Eテスト**
   - 利用制限到達時のユーザー体験
   - プラン変更時の動作確認

## セキュリティ考慮事項

### 認証・認可

- **ユーザー認証**: Clerk認証システムとの統合
- **API保護**: 認証済みユーザーのみアクセス可能
- **レート制限**: API レベルでの追加制限（DDoS対策）

### データ保護

- **個人情報**: 利用ログに個人識別情報を含めない
- **データ保持**: 古い利用ログの定期削除（GDPR対応）
- **監査ログ**: 管理者による制限変更の記録

## 実装の優先順位

### Phase 1: 基本機能
1. データベーススキーマとマイグレーション
2. バックエンドAPI（利用回数チェック・記録）
3. フロントエンド基本UI（残り回数表示）

### Phase 2: エラーハンドリング
1. 包括的なエラーハンドリング
2. ユーザーフレンドリーなエラーメッセージ
3. フォーム無効化とUI制御

### Phase 3: 最適化・拡張
1. パフォーマンス最適化
2. キャッシュ機能
3. 管理者向け設定インターフェース

## 運用・監視

### メトリクス

- 日次利用回数の統計
- プラン別利用パターン
- エラー発生率の監視

### アラート

- 異常な利用パターンの検出
- システムエラー率の閾値監視
- データベース性能の監視

この設計により、スケーラブルで保守性の高いAIChat利用制限システムを構築し、将来的な機能拡張にも対応できる基盤を提供します。