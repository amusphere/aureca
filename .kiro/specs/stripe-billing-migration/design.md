# 設計書

## 概要

Clerk BillingからStripe SDKへの完全移行を実現する設計。既存のアーキテクチャパターン（Router → Service → Repository → Database）を維持しながら、Stripeの機能を統合し、セキュアで拡張可能なサブスクリプション管理システムを構築する。

## アーキテクチャ

### システム全体図

```mermaid
graph TB
    subgraph "Frontend (Next.js)"
        UI[UI Components]
        Hooks[Custom Hooks]
        Pages[Pages]
    end

    subgraph "Backend (FastAPI)"
        Router[Stripe Router]
        Service[Stripe Service]
        Repository[Subscription Repository]
        Webhook[Webhook Handler]
    end

    subgraph "External Services"
        Stripe[Stripe API]
        StripeCheckout[Stripe Checkout]
        StripePortal[Stripe Customer Portal]
    end

    subgraph "Database"
        Users[Users Table]
        Subscriptions[Subscriptions Table]
    end

    UI --> Hooks
    Hooks --> Router
    Router --> Service
    Service --> Repository
    Repository --> Users
    Repository --> Subscriptions
    Service --> Stripe
    Stripe --> Webhook
    Webhook --> Service
    UI --> StripeCheckout
    UI --> StripePortal
```

### データフロー

1. **ユーザー登録時**: Clerk認証でUser作成（Clerk機能のみ使用）
2. **初回サブスクリプション関連アクセス時**: UserService.ensure_stripe_customer → Stripe Customer作成 → stripe_customer_id保存
3. **サブスクリプション購入**: Frontend → Stripe Checkout → 支払い完了 → Webhook → DB更新
4. **サブスクリプション管理**: Frontend → Stripe Customer Portal → 変更・キャンセル → Webhook → DB更新
5. **機能アクセス制御**: Frontend → `/api/users/me` → サブスクリプション情報付きユーザー情報返却

**重要**: サブスクリプションのライフサイクル管理（作成・更新・キャンセル）はすべてStripeの公式機能を使用し、
アプリケーションはWebhookを通じてStripeの状態変更を受け取り、ローカルDBを同期する。

## コンポーネントとインターフェース

### Backend Components

#### 1. User Service (`backend/app/services/user_service.py`)

```python
class UserService:
    async def ensure_stripe_customer(self, user: User) -> str
    async def get_user_with_subscription(self, user_id: int) -> UserWithSubscription
    async def update_user_stripe_customer_id(self, user_id: int, stripe_customer_id: str) -> User
```

#### 2. Stripe Service (`backend/app/services/stripe_service.py`)

```python
class StripeService:
    async def create_customer(self, user: User) -> str
    async def get_customer(self, stripe_customer_id: str) -> stripe.Customer
    async def create_checkout_session(self, customer_id: str, price_id: str, success_url: str, cancel_url: str) -> stripe.checkout.Session
    async def create_customer_portal_session(self, customer_id: str, return_url: str) -> stripe.billing_portal.Session
    async def verify_webhook_signature(self, payload: bytes, signature: str) -> stripe.Event

    # Note: サブスクリプションの作成・更新・キャンセルはStripe CheckoutとCustomer Portalで処理
    # WebhookでStripeからの変更通知を受け取り、ローカルDBを同期
```

#### 3. Subscription Repository (`backend/app/repositories/subscription.py`)

```python
class SubscriptionRepository:
    async def create_subscription(self, subscription_data: SubscriptionCreate) -> Subscription
    async def get_subscription_by_user_id(self, user_id: int) -> Subscription | None
    async def get_subscription_by_stripe_id(self, stripe_subscription_id: str) -> Subscription | None
    async def update_subscription(self, subscription_id: int, update_data: SubscriptionUpdate) -> Subscription
    async def get_active_subscription(self, user_id: int) -> Subscription | None
    async def deactivate_subscription(self, subscription_id: int) -> Subscription
```

#### 4. Stripe Router (`backend/app/routers/api/stripe.py`)

```python
@router.post("/create-checkout-session")
async def create_checkout_session(request: CheckoutSessionRequest, user: User = Depends(auth_user))

@router.post("/create-portal-session")
async def create_portal_session(user: User = Depends(auth_user))

@router.post("/webhook")
async def stripe_webhook(request: Request)
```

#### 5. Users Router 拡張 (`backend/app/routers/api/users.py`)

```python
@router.get("/me")
async def get_current_user(user: User = Depends(auth_user)) -> UserWithSubscription:
    # サブスクリプション情報を含むユーザー情報を返却
    # isPremium, planName, expiresAt などの情報を含む
```

#### 6. Webhook Handler (`backend/app/services/stripe_webhook_handler.py`)

```python
class StripeWebhookHandler:
    async def handle_customer_subscription_created(self, event: stripe.Event) -> None
    async def handle_customer_subscription_updated(self, event: stripe.Event) -> None
    async def handle_customer_subscription_deleted(self, event: stripe.Event) -> None
    async def handle_invoice_payment_succeeded(self, event: stripe.Event) -> None
    async def handle_invoice_payment_failed(self, event: stripe.Event) -> None
```

### Frontend Components

#### 1. User Hook 拡張 (`frontend/components/hooks/useUser.ts`)

```typescript
interface UserWithSubscription {
  id: number;
  uuid: string;
  email: string;
  name: string;
  subscription: {
    isPremium: boolean;
    planName: string | null;
    status: string | null;
    currentPeriodEnd: number | null;
    cancelAtPeriodEnd: boolean;
  } | null;
}

interface UseUserReturn {
  user: UserWithSubscription | null;
  isLoading: boolean;
  error: string | null;
  isPremium: boolean;
  refreshUser: () => Promise<void>;
}
```

#### 2. Subscription Hook (`frontend/components/hooks/useSubscription.ts`)

```typescript
interface UseSubscriptionReturn {
  createCheckoutSession: (priceId: string) => Promise<void>;
  openCustomerPortal: () => Promise<void>;
  isLoading: boolean;
  error: string | null;
}
```

#### 3. Subscription Page (`frontend/app/(authed)/subscription/page.tsx`)

- Stripe Pricing Tableの統合
- 現在のプラン表示
- Customer Portalへのリンク

#### 4. Premium Feature Guard (`frontend/components/components/commons/PremiumGuard.tsx`)

Clerkの`<Protect>`コンポーネントを置き換える新しいコンポーネント

```typescript
interface PremiumGuardProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  showUpgrade?: boolean;
}
```

## データモデル

### 1. Users Table 拡張

```sql
ALTER TABLE users ADD COLUMN stripe_customer_id VARCHAR(255) UNIQUE;
CREATE INDEX idx_users_stripe_customer_id ON users(stripe_customer_id);
```

### 2. Subscriptions Table (新規)

```sql
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT gen_random_uuid() NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    stripe_subscription_id VARCHAR(255) UNIQUE NOT NULL,
    stripe_customer_id VARCHAR(255) NOT NULL,
    stripe_price_id VARCHAR(255) NOT NULL,
    plan_name VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL, -- active, canceled, incomplete, past_due, etc.
    current_period_start BIGINT NOT NULL,
    current_period_end BIGINT NOT NULL,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    canceled_at BIGINT NULL,
    trial_start BIGINT NULL,
    trial_end BIGINT NULL,
    created_at BIGINT NOT NULL DEFAULT EXTRACT(EPOCH FROM NOW()),
    updated_at BIGINT NOT NULL DEFAULT EXTRACT(EPOCH FROM NOW())
);

CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_stripe_subscription_id ON subscriptions(stripe_subscription_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_current_period_end ON subscriptions(current_period_end);
```

### 3. SQLModel定義

```python
class Subscription(SQLModel, table=True):
    __tablename__ = "subscriptions"

    id: int | None = Field(default=None, primary_key=True)
    uuid: UUID = Field(default_factory=uuid4, index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    stripe_subscription_id: str = Field(unique=True, index=True)
    stripe_customer_id: str = Field(index=True)
    stripe_price_id: str = Field(index=True)
    plan_name: str
    status: str = Field(index=True)
    current_period_start: float
    current_period_end: float
    cancel_at_period_end: bool = Field(default=False)
    canceled_at: float | None = Field(default=None)
    trial_start: float | None = Field(default=None)
    trial_end: float | None = Field(default=None)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

    # Relationships
    user: User = Relationship(back_populates="subscriptions")

# User モデルにも関係を追加
class User(SQLModel, table=True):
    # ... 既存のフィールド ...
    stripe_customer_id: str | None = Field(default=None, unique=True, index=True)

    # Relationships
    subscriptions: list["Subscription"] = Relationship(back_populates="user")
```

## エラーハンドリング

### Backend Error Handling

1. **Stripe API エラー**
   - Rate limiting: 指数バックオフで再試行
   - Invalid request: 詳細なエラーメッセージをログに記録
   - Authentication errors: 設定確認を促すメッセージ

2. **Webhook エラー**
   - 署名検証失敗: セキュリティログに記録
   - 処理失敗: 再試行キューに追加
   - 重複イベント: idempotency keyで重複処理を防止

3. **Database エラー**
   - 制約違反: 適切なHTTPステータスコードで応答
   - 接続エラー: ヘルスチェックエンドポイントで監視

### Frontend Error Handling

1. **API エラー**
   - Network errors: 再試行ボタン付きエラー表示
   - Authentication errors: ログイン画面にリダイレクト
   - Subscription errors: サポート連絡先を表示

2. **Stripe Checkout エラー**
   - Payment failures: エラーメッセージと再試行オプション
   - Session expired: 新しいセッション作成

## テスト戦略

### Backend Testing

1. **Unit Tests**
   - StripeService: モックを使用したStripe API呼び出しテスト
   - SubscriptionRepository: データベース操作テスト
   - WebhookHandler: イベント処理ロジックテスト

2. **Integration Tests**
   - Stripe Test Mode APIを使用した実際のAPI呼び出しテスト
   - Webhook エンドポイントのテスト
   - データベース統合テスト

3. **E2E Tests**
   - サブスクリプション購入フローテスト
   - キャンセル・更新フローテスト

### Frontend Testing

1. **Component Tests**
   - PremiumGuard: 権限制御ロジックテスト
   - Subscription components: UI状態テスト

2. **Hook Tests**
   - useSubscription: API呼び出しとstate管理テスト

3. **Integration Tests**
   - Stripe Checkout統合テスト
   - Customer Portal統合テスト

## セキュリティ考慮事項

### API Security

1. **Webhook Security**
   - Stripe署名検証の実装
   - HTTPS必須
   - Rate limiting

2. **API Key Management**
   - 環境変数での管理
   - Test/Live mode の適切な分離
   - 最小権限の原則

### Data Protection

1. **PII Protection**
   - 支払い情報はStripeに保存、ローカルには保存しない
   - ログに機密情報を含めない

2. **Access Control**
   - サブスクリプション状態の検証はバックエンドで実行
   - フロントエンドでの権限チェックは表示制御のみ

## パフォーマンス最適化

### Backend Optimization

1. **Database Optimization**
   - 適切なインデックス設計
   - サブスクリプション状態のキャッシュ
   - Connection pooling

2. **API Optimization**
   - Stripe API呼び出しの最小化
   - バッチ処理での効率化

### Frontend Optimization

1. **State Management**
   - サブスクリプション状態のキャッシュ
   - 不要な再レンダリングの防止

2. **Loading States**
   - Stripe Checkout読み込み中の適切なUI表示
   - Progressive loading

## 移行戦略

### Phase 1: Infrastructure Setup
1. Stripe アカウント設定
2. データベーススキーマ更新
3. 基本的なStripe Service実装

### Phase 2: Core Functionality
1. Customer作成・管理機能
2. Subscription CRUD操作
3. Webhook処理

### Phase 3: Frontend Integration
1. Pricing Table統合
2. Customer Portal統合
3. Premium feature guards

### Phase 4: Migration & Cleanup
1. 既存Clerk Billing機能の無効化
2. データ移行（必要に応じて）
3. 旧コードの削除

## 監視とログ

### Monitoring

1. **Stripe Dashboard**
   - 支払い状況の監視
   - エラー率の追跡
   - Webhook配信状況

2. **Application Monitoring**
   - サブスクリプション関連APIのレスポンス時間
   - エラー率とエラー内容
   - データベースパフォーマンス

### Logging

1. **Structured Logging**
   - JSON形式でのログ出力
   - 相関IDによるリクエスト追跡
   - 機密情報の除外

2. **Audit Logging**
   - サブスクリプション変更の記録
   - 支払い関連イベントの記録
   - セキュリティイベントの記録