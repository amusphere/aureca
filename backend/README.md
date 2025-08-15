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

### テストアーキテクチャ

#### 2024年1月 - テスト改善実装
本番コードからテスト固有の処理を完全に分離し、FastAPIのベストプラクティスに従ったテスト設計を実現しました。

**主な改善点:**
- ✅ 本番コードからPYTEST_CURRENT_TEST環境変数チェックを除去
- ✅ unittest.mockの動的インポートを除去
- ✅ 依存性注入を活用したテスト設計
- ✅ FastAPIの依存性オーバーライド機能を活用
- ✅ 再利用可能なテストユーティリティの作成

#### テスト構造
```
tests/
├── conftest.py              # 共通フィクスチャ
├── unit/                    # ユニットテスト
│   ├── test_ai_chat_usage_service.py
│   ├── test_clerk_service.py
│   └── ...
├── integration/             # 統合テスト
│   ├── test_ai_chat_usage_api_integration.py
│   └── ...
├── performance/             # パフォーマンステスト
│   └── ...
└── utils/                   # テストユーティリティ
    ├── test_helpers.py      # テストヘルパー関数
    └── README.md           # テストユーティリティ使用方法
```

#### テストパターン

**1. ユニットテスト - 依存性注入パターン**
```python
@pytest.fixture
def service_with_mocks(session, mock_clerk_service, mock_usage_repository):
    return AIChatUsageService(
        session=session,
        clerk_service=mock_clerk_service,
        usage_repository=mock_usage_repository
    )

def test_get_user_plan_success(service_with_mocks, mock_clerk_service):
    # テスト実装
    pass
```

**2. 統合テスト - 依存性オーバーライドパターン**
```python
@pytest.fixture(autouse=True)
def setup_app_overrides(mock_clerk_service):
    app.dependency_overrides[get_clerk_service] = lambda: mock_clerk_service
    yield
    app.dependency_overrides.clear()

def test_api_endpoint(client):
    response = client.get("/api/usage")
    assert response.status_code == 200
```

**3. テストデータファクトリーパターン**
```python
# テストデータの生成
user = TestDataFactory.create_user(
    clerk_sub="test_user_123",
    email="test@example.com"
)

usage_record = TestDataFactory.create_usage_record(
    user_id=user.id,
    usage_date="2024-01-15",
    usage_count=5
)
```

### テストユーティリティ

詳細な使用方法は [tests/utils/README.md](./tests/utils/README.md) を参照してください。

**主要なユーティリティ:**
- `TestDataFactory`: テストデータ生成
- `UserFactory`: ユーザーオブジェクト生成
- `TestErrorScenarios`: エラーシナリオシミュレーション

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

### テスト作成時の注意点
1. **本番コードにテスト固有の処理を含めない**
2. **依存性注入を活用してテスタブルな設計にする**
3. **FastAPIの依存性オーバーライド機能を使用する**
4. **テストユーティリティを活用してDRYを保つ**
5. **テスト間の分離を確保する**

### 新機能開発フロー
1. スキーマ更新（必要に応じて）
2. マイグレーション生成
3. リポジトリメソッド実装
4. サービスロジック実装
5. APIエンドポイント作成
6. テスト作成（ユニット→統合→パフォーマンス）

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