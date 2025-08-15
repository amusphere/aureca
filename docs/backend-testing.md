# Backend Test Specification

## 概要

Aurecaバックエンドのテスト仕様書。FastAPIのベストプラクティスに従った依存性注入ベースのテスト設計を採用し、本番コードからテスト固有の処理を完全に分離したクリーンなアーキテクチャを実現しています。

## テスト実行

### 基本コマンド
```bash
# 全テスト実行
cd backend && uv run pytest

# 特定のテストタイプ実行
uv run pytest tests/unit/        # ユニットテスト
uv run pytest tests/integration/ # 統合テスト
uv run pytest tests/performance/ # パフォーマンステスト

# 詳細出力
uv run pytest -v

# カバレッジ付き実行
uv run pytest --cov=app
```

### パフォーマンス指標
- **全テスト数**: 215個
- **実行時間**: 4.32秒
- **成功率**: 99.5%（1個スキップ）

## テスト構造

### ディレクトリ構成
```
tests/
├── conftest.py              # 共通フィクスチャ
├── unit/                    # ユニットテスト
│   ├── test_ai_chat_usage_service.py
│   ├── test_clerk_service.py
│   ├── test_plan_limits.py
│   └── test_task_*.py
├── integration/             # 統合テスト
│   ├── test_ai_chat_usage_api_integration.py
│   ├── test_task_api.py
│   └── test_two_plan_e2e.py
├── performance/             # パフォーマンステスト
│   ├── test_ai_chat_usage_performance.py
│   └── test_task_priority_performance.py
└── utils/                   # テストユーティリティ
    └── test_helpers.py      # テストヘルパー関数
```

### テスト分類
- **ユニットテスト**: 34個（サービス層の単体テスト）
- **統合テスト**: API、E2E、エラーハンドリング
- **パフォーマンステスト**: メモリ、データベース、並行処理

## アーキテクチャ設計原則

### 1. 依存性注入パターン
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

### 2. 本番コードの分離
- 本番コードにテスト固有の処理は一切含まない
- 環境変数によるテスト検出は使用しない
- Mock検出ロジックは実装しない
- テスト専用メソッドは作成しない

### 3. FastAPI依存性オーバーライド
統合テストではFastAPIの依存性オーバーライド機能を活用：

```python
@pytest.fixture(autouse=True)
def setup_app_overrides(mock_clerk_service):
    app.dependency_overrides[get_clerk_service] = lambda: mock_clerk_service
    yield
    app.dependency_overrides.clear()
```

## テストユーティリティ

### TestDataFactory
テストデータオブジェクトを生成するファクトリークラス。デフォルト値とカスタマイズ可能なパラメータを提供します。

```python
from tests.utils import TestDataFactory

# デフォルト値でユーザー作成
user = TestDataFactory.create_user()

# カスタム値でユーザー作成
user = TestDataFactory.create_user(
    email="custom@example.com",
    name="Custom User"
)

# 使用量レコード作成
usage = TestDataFactory.create_usage_record(
    user_id=1,
    usage_count=5
)

# タスク作成
task = TestDataFactory.create_task(
    user_id=1,
    title="Custom Task",
    completed=True
)
```

### UserFactory
Userオブジェクト専用のファクトリーパターン実装。メモリ内作成とデータベース永続化の両方をサポートします。

```python
from tests.utils import UserFactory

# 永続化せずにオブジェクト生成
user = UserFactory.build(email="test@example.com")

# データベースに永続化して作成
user = UserFactory.create(session, email="test@example.com")

# バッチで複数ユーザー作成
users = UserFactory.create_batch(session, count=5)
```

### TestErrorScenarios
テストでの様々なエラー条件をシミュレートするユーティリティクラス。

```python
from tests.utils import TestErrorScenarios
from unittest.mock import patch

# 特定のエラーをシミュレート
clerk_error = TestErrorScenarios.simulate_clerk_api_error()
db_error = TestErrorScenarios.simulate_database_error()
http_error = TestErrorScenarios.simulate_http_exception(404, "Not found")

# モックと組み合わせて使用
with patch("app.services.clerk_service.get_user_plan", side_effect=clerk_error):
    # エラーハンドリングをテスト
    pass

# パラメータ化テスト用の共通エラーシナリオ
error_scenarios = TestErrorScenarios.get_common_error_scenarios()

@pytest.mark.parametrize("error_name,error", error_scenarios.items())
def test_error_handling(error_name, error):
    # 異なるエラータイプでテスト
    pass
```

## テストパターン

### 1. ユニットテスト - 依存性注入パターン

```python
# tests/unit/test_new_service.py
import pytest
from tests.utils import TestDataFactory, TestErrorScenarios

class TestNewService:
    @pytest.fixture
    def service_with_mocks(self, session, mock_dependencies):
        return NewService(
            session=session,
            dependency=mock_dependencies
        )

    def test_success_case(self, service_with_mocks):
        # テストデータ作成
        user = TestDataFactory.create_user()

        # テスト実行
        result = service_with_mocks.process(user)

        # アサーション
        assert result is not None

    def test_error_handling(self, service_with_mocks):
        # エラーシミュレーション
        error = TestErrorScenarios.simulate_database_error()

        with patch("service.method", side_effect=error):
            with pytest.raises(DatabaseError):
                service_with_mocks.process_with_db()
```

### 2. 統合テスト - 依存性オーバーライドパターン

```python
# tests/integration/test_new_api.py
import pytest
from tests.utils import UserFactory

class TestNewAPI:
    @pytest.fixture(autouse=True)
    def setup_dependencies(self, mock_external_service):
        app.dependency_overrides[get_external_service] = lambda: mock_external_service
        yield
        app.dependency_overrides.clear()

    def test_api_endpoint(self, client, session):
        # データベースにテストデータ作成
        user = UserFactory.create(session, email="test@example.com")

        # API呼び出し
        response = client.get(f"/api/users/{user.id}")

        # レスポンス検証
        assert response.status_code == 200
        assert response.json()["email"] == "test@example.com"
```

### 3. パフォーマンステスト

```python
# tests/performance/test_new_performance.py
import pytest
import time
from tests.utils import TestDataFactory

class TestNewPerformance:
    def test_large_dataset_performance(self, session):
        # 大量データでのパフォーマンステスト
        start_time = time.time()

        # 大量データ作成
        users = [TestDataFactory.create_user(id=i) for i in range(1000)]

        # 処理実行
        result = service.process_batch(users)

        # パフォーマンス検証
        execution_time = time.time() - start_time
        assert execution_time < 5.0  # 5秒以内
        assert len(result) == 1000
```

## テストカバレッジ要件

### エッジケース
- **境界値テスト**: 制限値ちょうど、1つ上、1つ下
- **日付境界テスト**: 午前0時前後の処理
- **エラーハンドリング**: API障害、データベース障害
- **並行処理テスト**: 複数ユーザー、同時アクセス

### 必須テストシナリオ
1. **正常系**: 期待される動作の確認
2. **異常系**: エラー条件での適切な処理
3. **境界値**: 最小値、最大値、境界条件
4. **パフォーマンス**: 応答時間、メモリ使用量

## 開発ガイドライン

### テスト作成時の必須ルール
1. **本番コードにテスト固有の処理を含めない**
2. **依存性注入を活用してテスタブルな設計にする**
3. **FastAPIの依存性オーバーライド機能を使用する**
4. **テストユーティリティを活用してDRYを保つ**
5. **テスト間の分離を確保する**

### テスト作成フロー
1. **ユニットテスト**: サービス層の単体テスト作成
2. **統合テスト**: API エンドポイントのテスト作成
3. **パフォーマンステスト**: 必要に応じて性能テスト追加
4. **エラーハンドリング**: 異常系テストの追加

### コード品質チェック
```bash
# フォーマットチェック
uv run ruff format .

# リントチェック
uv run ruff check . --fix

# テスト実行
uv run pytest -v
```

## 継続的改善

### 監視項目
- テスト実行時間の監視（目標: 5秒以内）
- カバレッジの維持・向上（目標: 90%以上）
- テスト成功率の監視（目標: 99%以上）

### 定期的な見直し
- 新しいテストパターンの文書化
- パフォーマンステストの拡充
- テストユーティリティの機能追加