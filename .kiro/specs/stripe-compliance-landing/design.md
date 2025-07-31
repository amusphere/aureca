# 設計書

## 概要

Stripe基準適合のための公開ランディングページを作成します。Stripeの公式ガイドラインに従い、以下の必須要素を含む完全に公開されたウェブサイトを構築します：

1. **明確な事業内容の説明** - AIタスク管理サービスの詳細
2. **企業情報の明示** - Nadeshiko.AIの会社概要
3. **連絡先情報** - 問い合わせ方法の提供
4. **利用規約・プライバシーポリシー** - 法的文書へのアクセス
5. **料金体系** - サービスの価格設定（無料・有料プランの明示）
6. **返金・キャンセルポリシー** - 取引条件の明確化

現在のログイン必須のルートページを、一般ユーザーがアクセス可能な情報提供ページに変更し、既存の認証システム（Clerk）は維持します。

## アーキテクチャ

### ルーティング構造の変更

```
現在: / → ClerkLoginPage（ログイン必須）
変更後: / → LandingPage（公開）
       /login → ClerkLoginPage（ログイン）
       /signup → ClerkSignupPage（サインアップ）
```

### コンポーネント階層

```
app/
├── page.tsx (LandingPage) ← 新規作成
├── (public)/
│   ├── login/
│   │   └── page.tsx (ClerkLoginPage) ← 既存から移動
│   ├── signup/
│   │   └── page.tsx (ClerkSignupPage) ← 新規作成
│   ├── terms-of-service/
│   │   └── page.tsx (利用規約) ← 既存
│   ├── privacy-policy/
│   │   └── page.tsx (プライバシーポリシー) ← 既存
│   └── legal-notice/
│       └── page.tsx (特定商取引法に基づく表記) ← 既存
└── (authed)/ ← 既存のまま
```

### ランディングページコンポーネント階層

```
components/components/landing/
├── LandingHeader.tsx ← 新規作成
├── HeroSection.tsx ← 新規作成
├── ServiceDetailSection.tsx ← 新規作成
├── PricingSection.tsx ← 新規作成
├── CompanyInfoSection.tsx ← 新規作成
├── ContactSection.tsx ← 新規作成
└── LandingFooter.tsx ← 新規作成
```

## コンポーネントと インターフェース

### 1. LandingPage コンポーネント

**場所**: `frontend/app/page.tsx`

**責任**:
- 企業情報（Nadeshiko.AI）の表示
- サービス内容（AIタスク管理）の説明
- ログイン・サインアップへの導線
- SEO対応（メタタグ、構造化データ）

**Props**: なし（静的コンテンツ）

**構成セクション**:
1. ヘッダー（ナビゲーション・ログインボタン）
2. ヒーローセクション（サービス概要・価値提案）
3. サービス詳細セクション（AIタスク管理機能の詳細説明）
4. 料金プランセクション（無料・有料プランの明示）
5. 企業情報セクション（会社概要・ミッション）
6. 連絡先セクション（問い合わせ方法）
7. フッター（利用規約・プライバシーポリシー・特定商取引法に基づく表記）

### 2. LandingHeader コンポーネント

**場所**: `frontend/components/components/landing/LandingHeader.tsx`

**責任**:
- ロゴ・企業名の表示
- ログイン・サインアップボタン
- レスポンシブナビゲーション

**Props**:
```typescript
interface LandingHeaderProps {
  // プロパティなし（静的）
}
```

### 3. HeroSection コンポーネント

**場所**: `frontend/components/components/landing/HeroSection.tsx`

**責任**:
- メインキャッチコピーの表示
- サービス概要の説明
- CTA（Call to Action）ボタン

### 4. ServiceDetailSection コンポーネント

**場所**: `frontend/components/components/landing/ServiceDetailSection.tsx`

**責任**:
- AIタスク管理機能の詳細説明
- Google連携機能の具体的な説明
- 主要機能の視覚的表示
- サービスの利用方法・手順の説明

### 5. PricingSection コンポーネント

**場所**: `frontend/components/components/landing/PricingSection.tsx`

**責任**:
- 料金プランの明確な表示（無料・有料）
- 各プランの機能比較
- 支払い方法の説明
- 特定商取引法に基づく表記へのリンク

### 6. CompanyInfoSection コンポーネント

**場所**: `frontend/components/components/landing/CompanyInfoSection.tsx`

**責任**:
- 企業名（Nadeshiko.AI）の明示
- 会社概要・ミッションの説明
- 事業内容の詳細説明
- 運営体制の透明性確保

### 7. ContactSection コンポーネント

**場所**: `frontend/components/components/landing/ContactSection.tsx`

**責任**:
- 問い合わせフォーム
- メールアドレス・電話番号の表示
- サポート時間の明示
- 所在地情報（必要に応じて）

### 8. 法的文書ページ（既存）

**既存ページの活用**:
- `frontend/app/(public)/terms-of-service/page.tsx`: 利用規約ページ（既存）
- `frontend/app/(public)/privacy-policy/page.tsx`: プライバシーポリシーページ（既存）
- `frontend/app/(public)/legal-notice/page.tsx`: 特定商取引法に基づく表記（既存・返金ポリシー含む）

### 9. 認証ページの再構成

**既存の変更**:
- `frontend/app/page.tsx`: LandingPageに変更
- `frontend/components/auth/ClerkLoginPage.tsx`: `/login`に移動

**新規作成**:
- `frontend/app/(public)/login/page.tsx`: ログイン専用ページ
- `frontend/app/(public)/signup/page.tsx`: サインアップ専用ページ

## データモデル

### メタデータ設定

```typescript
// app/layout.tsx
export const metadata: Metadata = {
  title: "Nadeshiko.AI - AIタスク管理アプリケーション",
  description: "AIを活用したスマートなタスク管理で、あなたの生産性を向上させます。Google連携でメールやカレンダーからタスクを自動生成。",
  keywords: ["AI", "タスク管理", "生産性", "Google連携", "自動化"],
  openGraph: {
    title: "Nadeshiko.AI - AIタスク管理アプリケーション",
    description: "AIを活用したスマートなタスク管理で、あなたの生産性を向上させます。",
    type: "website",
    locale: "ja_JP",
  },
};
```

### 構造化データ（JSON-LD）

```typescript
const structuredData = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "Nadeshiko.AI",
  "applicationCategory": "ProductivityApplication",
  "description": "AIを活用したタスク管理アプリケーション",
  "operatingSystem": "Web",
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "JPY"
  }
};
```

## エラーハンドリング

### 認証エラー

- ログイン失敗時: エラーメッセージ表示、再試行促進
- セッション期限切れ: ランディングページにリダイレクト

### ナビゲーションエラー

- 存在しないページ: 404ページからランディングページへの導線
- 認証が必要なページへの直接アクセス: ログインページにリダイレクト

## テスト戦略

### 単体テスト

1. **LandingPage コンポーネント**
   - 企業名の表示確認
   - サービス説明の表示確認
   - ログイン・サインアップボタンの存在確認

2. **LandingHeader コンポーネント**
   - ナビゲーションリンクの動作確認
   - レスポンシブ表示の確認

3. **認証フロー**
   - ログインページへのリダイレクト確認
   - サインアップページへのリダイレクト確認

### 統合テスト

1. **ルーティングテスト**
   - `/` → LandingPage表示
   - `/auth/login` → ログインページ表示
   - `/auth/signup` → サインアップページ表示

2. **認証フローテスト**
   - 未認証ユーザーの保護されたページアクセス
   - 認証後のダッシュボードリダイレクト

### E2Eテスト

1. **Stripe審査シナリオ**
   - ルートページへのアクセス（ログイン不要）
   - 企業情報の表示確認
   - サービス内容の表示確認
   - 法的ページ（利用規約、プライバシーポリシー）へのアクセス

2. **ユーザージャーニーテスト**
   - 新規ユーザー: ランディング → サインアップ → ダッシュボード
   - 既存ユーザー: ランディング → ログイン → ダッシュボード

## SEO・アクセシビリティ対応

### SEO対策

1. **メタタグ最適化**
   - title、description、keywordsの設定
   - Open Graphタグの設定
   - 構造化データ（JSON-LD）の実装

2. **コンテンツ最適化**
   - 適切な見出し構造（h1, h2, h3）
   - 意味のあるalt属性
   - 内部リンクの最適化

### アクセシビリティ対応

1. **WCAG 2.1 AA準拠**
   - キーボードナビゲーション対応
   - スクリーンリーダー対応
   - 適切なコントラスト比

2. **セマンティックHTML**
   - 適切なHTML要素の使用
   - ARIA属性の適切な設定
   - フォーカス管理

## セキュリティ考慮事項

### CSP（Content Security Policy）

```typescript
const cspHeader = `
  default-src 'self';
  script-src 'self' 'unsafe-eval' 'unsafe-inline' https://clerk.dev;
  style-src 'self' 'unsafe-inline';
  img-src 'self' blob: data: https:;
  font-src 'self';
  connect-src 'self' https://api.clerk.dev;
  frame-src https://clerk.dev;
`;
```

### プライバシー保護

- 不要なトラッキングの除去
- Cookie使用の最小化
- GDPR準拠のプライバシーポリシー

## パフォーマンス最適化

### Core Web Vitals対応

1. **LCP（Largest Contentful Paint）**
   - 画像の最適化（WebP形式、適切なサイズ）
   - フォントの最適化（font-display: swap）

2. **FID（First Input Delay）**
   - JavaScriptの最小化
   - 重要でないスクリプトの遅延読み込み

3. **CLS（Cumulative Layout Shift）**
   - 画像・動画のサイズ指定
   - フォント読み込み時のレイアウトシフト防止

### 読み込み最適化

- 静的アセットのCDN配信
- 画像の遅延読み込み
- コンポーネントの適切な分割