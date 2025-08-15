# Backend - FastAPI Application

AIアシスタント機能を持つタスク管理アプリケーションのバックエンドAPI。FastAPI + SQLModel + PostgreSQLで構築されています。

## 🚀 クイックスタート

### 開発環境セットアップ
```bash
# 依存関係のインストール
uv sync

# 環境変数設定
cp .env.example .env

# データベースマイグレーション
uv run alembic upgrade head

# 開発サーバー起動
uv run fastapi dev --host 0.0.0.0
```

### API ドキュメント
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## 🧪 テスト

### テスト実行
```bash
# 全テスト実行
uv run pytest

# 特定のテストタイプ実行
uv run pytest tests/unit/        # ユニットテスト
uv run pytest tests/integration/ # 統合テスト
uv run pytest tests/performance/ # パフォーマンステスト

# 詳細出力
uv run pytest -v

# カバレッジ付き実行
uv run pytest --cov=app
```

## 🏗 アーキテクチャ

### レイヤー構造
```
app/
├── routers/         # APIエンドポイント
├── services/        # ビジネスロジック
├── repositories/    # データアクセス層
├── models/          # Pydanticモデル
├── schema.py        # SQLModelテーブル定義
└── database.py      # データベース接続
```

### 依存性注入
サービス層では依存性注入を活用し、テスタビリティを向上させています：

```python
class AIChatUsageService:
    def __init__(
        self,
        session: Session,
        clerk_service: Optional[ClerkService] = None,
        usage_repository: Optional[AIChatUsageRepository] = None
    ):
        self.session = session
        self.clerk_service = clerk_service or get_clerk_service()
        self.usage_repository = usage_repository or AIChatUsageRepository()
```

## 🔧 開発ツール

### コード品質
```bash
# フォーマット
uv run ruff format .

# リント
uv run ruff check . --fix

# 型チェック
uv run mypy app/
```

### データベース
```bash
# マイグレーション作成
uv run alembic revision --autogenerate -m "description"

# マイグレーション適用
uv run alembic upgrade head

# マイグレーション履歴
uv run alembic history
```

## 📝 開発ガイドライン

### 新機能開発フロー
1. スキーマ更新（必要に応じて）
2. マイグレーション生成
3. リポジトリメソッド実装
4. サービスロジック実装
5. APIエンドポイント作成
6. テスト作成（ユニット→統合→パフォーマンス）

### テスト作成時の注意点
1. **本番コードにテスト固有の処理を含めない**
2. **依存性注入を活用してテスタブルな設計にする**
3. **FastAPIの依存性オーバーライド機能を使用する**
4. **テストユーティリティを活用してDRYを保つ**
5. **テスト間の分離を確保する**

詳細なテストパターンは [バックエンドテスト仕様書](../docs/backend-testing.md) を参照してください。

## 🚀 パフォーマンス

### 最適化ポイント
- データベースインデックスの適切な設計
- 非同期処理の活用
- キャッシュ戦略
- バッチ処理の実装

### モニタリング
- パフォーマンステストによる継続的な監視
- データベースクエリの最適化
- メモリ使用量の監視