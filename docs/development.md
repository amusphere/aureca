# 開発ガイド

## 開発フロー

### バックエンドエンドポイント作成
1. `routers/`ディレクトリに新しいファイルを作成
2. `routers/routers.py`でエンドポイントを定義

#### 開発順序（必須）
1. `schema.py`を更新 → 2. マイグレーション生成 → 3. リポジトリ作成 → 4. モデル定義 → 5. サービス実装 → 6. ルーター作成 → 7. `routers.py`に登録

### フロントエンドページ作成
1. `app/`ディレクトリに新しいファイルを作成
2. 認証が必要な場合は`(authed)/`ディレクトリに作成

#### 開発順序（必須）
1. 型定義 → 2. フック作成 → 3. コンポーネント構築 → 4. ページ作成

## データベースマイグレーション

### 新しいマイグレーション作成
1. `schema.py`でテーブルを追加または変更
2. Alembicでマイグレーションファイル作成：
   ```bash
   docker compose run --rm backend alembic revision --autogenerate -m "migration_name"
   ```
3. `migrations/versions/`ディレクトリの生成されたマイグレーションファイルを確認・調整
4. マイグレーション適用：
   ```bash
   docker compose run --rm backend alembic upgrade head
   ```

### マイグレーションのダウングレード
```bash
docker compose run --rm backend alembic downgrade -1
```

## 重要なルール

### データベース
- **スキーマ変更**: 必ずAlembicマイグレーションを使用
- **タイムスタンプ**: created_at/updated_atはUnix float形式
- **主キー**: 自動インクリメントid + 外部参照用UUID
- **リレーション**: 適切な外部キーを持つSQLModel

### 認証
- **デュアルモード**: Clerk（デフォルト）またはemail/password（フォールバック）
- **制御**: `NEXT_PUBLIC_AUTH_SYSTEM`環境変数
- **保護**: Next.jsミドルウェアによるルート保護

### コード品質（コミット前必須）
```bash
# バックエンドフォーマット
cd backend && uv run black .

# フロントエンド型チェック
cd frontend && npm run build
```

### AIスポーク作成
1. `backend/app/services/ai/spokes/[name]/`ディレクトリを作成
2. `actions.json`でアクション定義：
   ```json
   {
     "actions": [
       {
         "name": "action_name",
         "description": "Action description",
         "parameters": {
           "param1": "string",
           "param2": "number"
         }
       }
     ]
   }
   ```
3. `spoke.py`で実装：
   ```python
   from backend.app.services.ai.spokes.base import BaseSpoke

   class MySpoke(BaseSpoke):
       async def action_name(self, param1: str, param2: int):
           # 実装
           pass
   ```
4. システム再起動で自動登録

#### 開発順序（必須）
1. フォルダ作成 → 2. `actions.json`追加 → 3. `spoke.py`実装 → 4. 再起動で自動登録

## テスト実行

### バックエンドテスト
```bash
cd backend && uv run pytest
```

### フロントエンドテスト
```bash
cd frontend && npm test
```

### 統合テスト
```bash
# 全体テスト
docker compose -f docker-compose.test.yml up --build
```