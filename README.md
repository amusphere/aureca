# Aureca

AIアシスタント機能を持つタスク管理アプリケーション。Next.js + FastAPIのフルスタック構成で、Googleサービスとの統合によるスマートなタスク管理を提供します。

## 🚀 クイックスタート

### 1. 環境変数設定
```bash
# フロントエンドとバックエンドの両方で.envファイルを作成
cp frontend/.env.example frontend/.env
cp backend/.env.example backend/.env
```

### 2. アプリケーション起動
```bash
# Docker Composeで全体を起動
docker compose up
```

### 3. データベースセットアップ
```bash
# マイグレーション実行
docker compose run --rm backend alembic upgrade head
```

### 4. アクセス
- **Web**: [http://localhost:3000](http://localhost:3000)
- **API**: [http://localhost:8000/docs](http://localhost:8000/docs)

## 🛠 技術スタック

- **フロントエンド**: Next.js 15 + TypeScript + Tailwind CSS
- **バックエンド**: FastAPI + SQLModel + PostgreSQL
- **認証**: Clerk / Email認証
- **AI**: OpenAI API統合
- **デプロイ**: Docker + Docker Compose

## 📚 ドキュメント

詳細な情報は`/docs`ディレクトリを参照してください：

- [技術スタック詳細](./docs/tech-stack.md)
- [アーキテクチャ](./docs/architecture.md)
- [開発ガイド](./docs/development.md)
- [デプロイメント](./docs/deployment.md)

## 🧪 テスト

### テスト実行
```bash
# 全テスト実行
cd backend && uv run pytest

# 特定のテストタイプ
cd backend && uv run pytest tests/unit/        # ユニットテスト
cd backend && uv run pytest tests/integration/ # 統合テスト
cd backend && uv run pytest tests/performance/ # パフォーマンステスト
```

### テスト改善 (2024年1月実装)

バックエンドのテストアーキテクチャを大幅に改善し、本番コードからテスト固有の処理を完全に分離しました。

**主な改善点:**
- ✅ 本番コードの完全なクリーンアップ（PYTEST_CURRENT_TEST環境変数、unittest.mock動的インポート除去）
- ✅ 依存性注入を活用したテスタブルな設計
- ✅ FastAPIの依存性オーバーライド機能を活用した統合テスト
- ✅ 再利用可能なテストユーティリティ（TestDataFactory、UserFactory、TestErrorScenarios）
- ✅ 215個のテストが4.3秒で実行完了（高速化達成）

詳細は [backend/README.md](./backend/README.md) および [backend/tests/utils/README.md](./backend/tests/utils/README.md) を参照してください。

## 🔧 開発環境

### ホットリロード開発
```bash
# バックエンドのみ
cd backend && uv run fastapi dev --host 0.0.0.0

# フロントエンドのみ
cd frontend && npm run dev
```

### コード品質チェック
```bash
# バックエンド
cd backend && uv run ruff format .  # フォーマット
cd backend && uv run ruff check . --fix  # リント

# フロントエンド
cd frontend && npm run build  # ビルドチェック
```

### パッケージ追加
```bash
# バックエンド
cd backend && uv add package-name

# フロントエンド
cd frontend && npm install package-name
```
