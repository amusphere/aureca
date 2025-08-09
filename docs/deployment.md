# デプロイメント

## Docker環境

### 本番環境
```bash
# ビルド
docker compose build

# 実行
docker compose up -d
```

### 開発環境（ホットリロード）
```bash
# バックエンドのみ
cd backend && uv run fastapi dev --host 0.0.0.0

# フロントエンドのみ
cd frontend && npm run dev
```

## 環境変数設定

### フロントエンド（`.env`）
```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
CLERK_SECRET_KEY=your_clerk_secret_key
NEXT_PUBLIC_AUTH_SYSTEM=clerk  # または email
APP_NAME="Your App Name"
```

### バックエンド（`.env`）
```env
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
OPENAI_API_KEY=your_openai_api_key
CLERK_SECRET_KEY=your_clerk_secret_key
```

## アクセスURL

- **Web**: [http://localhost:3000](http://localhost:3000)
- **API**: [http://localhost:8000/docs](http://localhost:8000/docs)

## データベース操作

### マイグレーション適用
```bash
docker compose run --rm backend alembic upgrade head
```

### 新しいマイグレーション作成
```bash
docker compose run --rm backend alembic revision --autogenerate -m "description"
```