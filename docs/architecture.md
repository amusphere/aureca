# アーキテクチャ

## ディレクトリ構造

### Backend
```
backend/
├── app/                   # アプリケーションソースコード
│   ├── constants/         # 定数定義
│   ├── migrations/        # データベースマイグレーション
│   ├── models/            # データモデル定義 (Pydanticによるリクエスト/レスポンススキーマ)
│   ├── repositories/      # データベースアクセス層
│   ├── routers/           # APIルート定義
│   ├── services/          # ビジネスロジック層
│   │   └── ai/            # AIハブ・スポークシステム
│   │       ├── core/      # AIコア機能
│   │       ├── spokes/    # AIサービス統合プラグイン
│   │       │   ├── gmail/           # Gmail統合
│   │       │   ├── google_calendar/ # Googleカレンダー統合
│   │       │   ├── tasks/           # タスク管理
│   │       │   └── todo_list/       # TODOリスト
│   │       └── utils/     # AI関連ユーティリティ
│   ├── utils/             # 汎用ユーティリティ関数
│   ├── config.py          # アプリケーション設定
│   ├── database.py        # データベース接続とセッション管理
│   └── schema.py          # SQLModelによるデータベーススキーマ定義
├── tests/                 # テストファイル
│   ├── integration/       # 統合テスト
│   ├── performance/       # パフォーマンステスト
│   └── unit/              # ユニットテスト
├── .env.example           # 環境変数サンプル
├── alembic.ini            # Alembic設定ファイル
├── Dockerfile             # バックエンド用Dockerfile
├── main.py                # FastAPIアプリケーションエントリーポイント
└── pyproject.toml         # uvによる環境依存関係
```

### Frontend
```
frontend/
├── app/                   # Next.jsアプリケーションソースコード
│   ├── (authed)/          # 認証が必要なルート
│   ├── (public)/          # 公開ルート
│   ├── api/               # APIルート定義
│   ├── globals.css        # グローバルCSSスタイル
│   ├── layout.tsx         # メインレイアウトコンポーネント
│   └── page.tsx           # Next.jsアプリケーションメインエントリーポイント
├── components/            # 再利用可能コンポーネント
│   ├── auth/              # 認証関連コンポーネント
│   ├── components/        # UIコンポーネント
│   │   └── ui/            # shadcn/uiコンポーネント（変更禁止）
│   ├── hooks/             # カスタムフック
│   ├── lib/               # ライブラリ関数
│   ├── pages/             # ページコンポーネント
│   └── tasks/             # タスク関連コンポーネント
├── constants/             # 定数定義
├── types/                 # TypeScript型定義
├── utils/                 # ユーティリティ関数
├── tests/                 # テストファイル
│   ├── components/        # コンポーネントテスト
│   ├── hooks/             # フックテスト
│   └── integration/       # 統合テスト
├── .env.example           # 環境変数サンプル
├── Dockerfile             # フロントエンド用Dockerfile
├── middleware.ts          # Next.jsミドルウェア
├── package.json           # Node.js依存関係
└── next.config.ts         # Next.js設定ファイル
```

## レイヤー構造

### Backend: Router → Service → Repository → Database
- **Routers**: HTTPリクエスト/レスポンスのみ処理 - ビジネスロジック禁止
- **Services**: ビジネスロジックとオーケストレーション - 直接データベースアクセス禁止
- **Repositories**: データベース操作のみ - ビジネスロジック禁止
- **Models**: Pydanticによるリクエスト/レスポンス検証

### Frontend: Page → Component → Hook → Utility
- **Pages**: `app/`ディレクトリのルートコンポーネント
- **Components**: UIコンポーネント - ビジネスロジック禁止
- **Hooks**: 状態管理とAPI呼び出し
- **Utilities**: 純粋関数とヘルパー
##
AIハブ・スポークシステム

### 概要
Aurecaは拡張可能なAIサービス統合システムを採用しています。

### 構造
- **Hub**: `backend/app/services/ai/core/` - 中央オーケストレーター
- **Spokes**: `backend/app/services/ai/spokes/[name]/` - 自動発見プラグイン
- **Base**: `backend/app/services/ai/spokes/base.py` - 全スポークの基底クラス
- **Manager**: `backend/app/services/ai/spokes/manager.py` - スポーク管理

### 実装済みスポーク
- **Gmail**: メール統合 (`spokes/gmail/`)
- **Google Calendar**: カレンダー統合 (`spokes/google_calendar/`)
- **Tasks**: タスク管理 (`spokes/tasks/`)
- **Todo List**: TODOリスト管理 (`spokes/todo_list/`)

### スポーク作成ルール
1. `spokes/[name]/`ディレクトリを作成
2. `actions.json`でアクション定義
3. `spoke.py`で`BaseSpoke`を継承して実装
4. システムが自動的に発見・登録