# Aureca

AIアシスタント機能を持つタスク管理アプリケーション。Next.js + FastAPIのフルスタック構成で、Googleサービスとの統合によるスマートなタスク管理を提供します。

## 🚀 クイックスタート

### 1. 環境変数設定
```bash
# 環境別設定スクリプトを使用（推奨）
./scripts/setup-environment.sh development

# または手動でコピー
cp frontend/.env.example frontend/.env
cp backend/.env.example backend/.env
```

**重要**: `.env`ファイルを編集して実際のAPIキーを設定してください。

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
- [環境変数設定](./docs/environment-configuration.md)
- [バックエンドテスト仕様](./docs/backend-testing.md)

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
