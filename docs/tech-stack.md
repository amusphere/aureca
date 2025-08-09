# 技術スタック

## フロントエンド（Next.js 15）
- **フレームワーク**: Next.js App Router - `app/`ディレクトリ構造を使用
- **言語**: TypeScript - 新しいコードは必須
- **スタイリング**: Tailwind CSS + shadcn/uiコンポーネント（UIコンポーネントは変更禁止）
- **認証**: `@clerk/nextjs`とミドルウェア保護
- **状態管理**: `components/hooks/`のカスタムReactフック
- **フォーム**: React Hook Form + Zod検証

## バックエンド（Python 3.12+）
- **フレームワーク**: FastAPI with async/await - 全エンドポイントで必須
- **ORM**: SQLModel - 全データベースモデルで必須
- **データベース**: PostgreSQL with auto-increment `id` + UUID `uuid`フィールド
- **マイグレーション**: Alembic - 全スキーマ変更で必須
- **パッケージマネージャー**: `uv` - 全Pythonコマンドで`uv run`を使用
- **認証**: Clerk SDK（プライマリ）+ email/password（フォールバック）
- **AI統合**: `backend/app/utils/llm.py`経由のOpenAI API

## データベース
- **RDBMS**: PostgreSQL
- **ORM**: SQLModel
- **マイグレーション**: Alembic
- **主キー**: 自動インクリメント`id` + 外部参照用UUID `uuid`
- **タイムスタンプ**: Unix float形式

## 認証システム
- **プライマリ**: Clerk（本番環境推奨）
- **フォールバック**: Email/Password（開発環境）
- **制御**: `NEXT_PUBLIC_AUTH_SYSTEM`環境変数
- **Google OAuth**: ユーザーごとの個別トークンテーブル

## デプロイメント
- **コンテナ化**: Docker
- **ローカル開発**: Docker Compose
- **パッケージ管理**:
  - Backend: `uv`
  - Frontend: `npm`

## 必須依存関係

### バックエンド
- `fastapi[standard]`
- `sqlmodel`
- `alembic`
- `clerk-backend-api`
- `openai`

### フロントエンド
- `@clerk/nextjs`
- `react-hook-form`
- `zod`
- `tailwindcss`## テスト環境


### バックエンドテスト
- **フレームワーク**: pytest
- **カバレッジ**: pytest-cov
- **モック**: unittest.mock
- **非同期テスト**: pytest-asyncio

### フロントエンドテスト
- **フレームワーク**: Vitest
- **テストライブラリ**: @testing-library/react
- **E2Eテスト**: Playwright（設定済み）
- **カバレッジ**: Vitest内蔵

## AI統合システム

### ハブ・スポーク構造
- **ハブ**: 中央オーケストレーター
- **スポーク**: プラグイン式サービス統合
- **自動発見**: フォルダベースの動的ロード
- **基底クラス**: `BaseSpoke`による統一インターフェース

### 実装済み統合
- Gmail API
- Google Calendar API
- タスク管理システム
- TODOリスト管理