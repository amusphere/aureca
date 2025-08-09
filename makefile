# テスト実行の最適化されたMakefile
.PHONY: test test-fast test-unit test-integration test-backend test-frontend test-all clean-test

# 高速テスト実行（並列 + unit tests only）
test-fast:
	@echo "🚀 高速テスト実行中..."
	@$(MAKE) -j2 test-backend-unit test-frontend-unit

# 単体テストのみ（最速）
test-unit:
	@echo "⚡ 単体テスト実行中..."
	@$(MAKE) -j2 test-backend-unit test-frontend-unit

# 統合テストのみ
test-integration:
	@echo "🔗 統合テスト実行中..."
	@$(MAKE) -j2 test-backend-integration test-frontend-integration

# 全テスト実行
test-all:
	@echo "🧪 全テスト実行中..."
	@$(MAKE) -j2 test-backend test-frontend

# デフォルトのテスト（高速版）
test: test-fast

# Backend テスト
test-backend:
	@echo "🐍 Backendテスト実行中..."
	cd backend && uv run pytest -x --tb=short --disable-warnings

test-backend-unit:
	@echo "⚡ Backend単体テスト実行中..."
	cd backend && uv run pytest tests/unit/ -x --tb=short --disable-warnings -q

test-backend-integration:
	@echo "🔗 Backend統合テスト実行中..."
	cd backend && uv run pytest tests/integration/ -x --tb=short --disable-warnings

test-backend-performance:
	@echo "📊 Backendパフォーマンステスト実行中..."
	cd backend && uv run pytest tests/performance/ -x --tb=short --disable-warnings

# Frontend テスト
test-frontend:
	@echo "⚛️ Frontendテスト実行中..."
	cd frontend && npm run test

test-frontend-unit:
	@echo "⚡ Frontend単体テスト実行中..."
	cd frontend && npm run test -- --run tests/components tests/hooks

test-frontend-integration:
	@echo "🔗 Frontend統合テスト実行中..."
	cd frontend && npm run test -- --run tests/integration

# テストカバレッジ
test-coverage:
	@echo "📊 テストカバレッジ計測中..."
	@$(MAKE) -j2 test-backend-coverage test-frontend-coverage

test-backend-coverage:
	cd backend && uv run pytest --cov=app --cov-report=html --cov-report=term

test-frontend-coverage:
	cd frontend && npm run test:coverage

# テストキャッシュクリア
clean-test:
	@echo "🧹 テストキャッシュクリア中..."
	cd backend && rm -rf .pytest_cache __pycache__ .coverage htmlcov
	cd frontend && rm -rf coverage node_modules/.cache

# 開発用ウォッチモード
test-watch:
	@echo "👀 テストウォッチモード開始..."
	cd frontend && npm run test:watch

# CI用テスト（GitHub Actions形式）
test-ci:
	@echo "🤖 CI用テスト実行中..."
	@$(MAKE) -j2 test-ci-backend test-ci-frontend

test-ci-backend:
	@echo "🐍 CI Backend テスト..."
	cd backend && uv run pytest tests/unit/ -x --tb=short --disable-warnings -q
	cd backend && uv run pytest tests/integration/ -x --tb=short --disable-warnings
	cd backend && uv run ruff check .
	cd backend && uv run ruff format --check .

test-ci-frontend:
	@echo "⚛️ CI Frontend テスト..."
	cd frontend && npm run test:unit:ci
	cd frontend && npm run test:integration:ci
	cd frontend && npm run lint
	cd frontend && npm run type-check

# パフォーマンステスト
test-perf:
	@echo "🏃‍♂️ パフォーマンステスト実行中..."
	@$(MAKE) test-backend-performance

# ヘルプ
help:
	@echo "🧪 利用可能なテストコマンド:"
	@echo "  test-fast          - 高速テスト（単体テストのみ、並列実行）⚡"
	@echo "  test-unit          - 単体テストのみ"
	@echo "  test-integration   - 統合テストのみ"
	@echo "  test-all           - 全テスト実行"
	@echo "  test-ci            - CI用テスト（GitHub Actions形式）🤖"
	@echo "  test-coverage      - カバレッジ付きテスト📊"
	@echo "  test-watch         - ウォッチモード👀"
	@echo "  test-perf          - パフォーマンステスト🏃‍♂️"
	@echo "  clean-test         - テストキャッシュクリア🧹"
	@echo ""
	@echo "📈 パフォーマンス目安:"
	@echo "  test-fast:    ~6秒"
	@echo "  test-unit:    ~10秒"
	@echo "  test-all:     ~30秒"
	@echo "  test-ci:      ~60秒"