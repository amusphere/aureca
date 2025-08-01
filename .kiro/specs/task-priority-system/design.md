# 設計書

## 概要

タスク管理システムに優先度機能を追加する設計書です。既存のアーキテクチャを維持しながら、High、Middle、Low の3段階の優先度を設定可能にし、一覧表示時の優先度ソート機能、AI による自動優先度判定機能を実装します。

## アーキテクチャ

### データベース設計

#### 優先度Enum定義
```python
class TaskPriority(int, Enum):
    HIGH = 1
    MIDDLE = 2
    LOW = 3
```

**設計理由：**
- `int` ベースのEnumにより、CASE文を使わない効率的なソートが可能
- データベースインデックスが最適化される
- 将来的な優先度レベル追加時も順序値の調整のみで対応可能

#### Tasksテーブル拡張
既存の `Tasks` テーブルに以下のカラムを追加：
- `priority: TaskPriority | None` - 優先度（nullable、デフォルトnull）
- インデックス: `priority` カラムにインデックスを追加してソートパフォーマンスを向上

#### マイグレーション戦略
1. 新しいenum型 `TaskPriority` を定義
2. `tasks` テーブルに `priority` カラムを追加（nullable）
3. 既存データは `priority = null` として保持
4. パフォーマンス向上のため `priority` カラムにインデックスを作成

### バックエンド設計

#### 1. スキーマ層 (schema.py)
```python
class TaskPriority(str, Enum):
    HIGH = "high"
    MIDDLE = "middle"
    LOW = "low"

class Tasks(SQLModel, table=True):
    # 既存フィールド...
    priority: TaskPriority | None = Field(default=None, nullable=True, index=True)
```

#### 2. モデル層 (models/task.py)
```python
class TaskModel(BaseModel):
    # 既存フィールド...
    priority: TaskPriority | None = None

class CreateTaskRequest(BaseModel):
    # 既存フィールド...
    priority: TaskPriority | None = None

class UpdateTaskRequest(BaseModel):
    # 既存フィールド...
    priority: TaskPriority | None = None
```

#### 3. リポジトリ層 (repositories/tasks.py)
```python
def find_tasks(
    session: Session,
    user_id: int,
    completed: bool = False,
    expires_at: float | None = None,
    order_by_priority: bool = True,  # 新規パラメータ
) -> list[Tasks]:
    stmt = select(Tasks).where(
        Tasks.user_id == user_id,
        Tasks.completed == completed,
    )

    if expires_at is not None:
        stmt = stmt.where(Tasks.expires_at >= expires_at)

    if order_by_priority:
        # 効率的な優先度ソート: 1(High) -> 2(Middle) -> 3(Low) -> NULL
        stmt = stmt.order_by(
            Tasks.priority.asc().nullslast(),
            Tasks.expires_at.asc().nullslast()
        )
    else:
        stmt = stmt.order_by(Tasks.expires_at.asc().nullslast())

    return session.exec(stmt).all()
```

#### 4. API層 (routers/api/tasks.py)
```python
@router.get("/", response_model=List[TaskModel])
async def get_tasks(
    completed: bool = False,
    order_by_priority: bool = True,  # 新規クエリパラメータ
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    tasks = find_tasks(
        session=session,
        user_id=current_user.id,
        completed=completed,
        order_by_priority=order_by_priority,
    )
    return [TaskModel.from_orm(task) for task in tasks]
```

### フロントエンド設計

#### 1. 型定義 (types/Task.ts)
```typescript
export type TaskPriority = "high" | "middle" | "low";

export interface Task {
  // 既存フィールド...
  priority?: TaskPriority;
}

export interface CreateTaskRequest {
  // 既存フィールド...
  priority?: TaskPriority;
}

export interface UpdateTaskRequest {
  // 既存フィールド...
  priority?: TaskPriority;
}
```

#### 2. 優先度表示コンポーネント
```typescript
// components/components/tasks/TaskPriorityBadge.tsx
interface TaskPriorityBadgeProps {
  priority?: TaskPriority;
  size?: "sm" | "md";
}

// 優先度別の色とアイコンを定義
const PRIORITY_CONFIG = {
  high: { color: "destructive", icon: AlertTriangle, label: "高" },
  middle: { color: "warning", icon: AlertCircle, label: "中" },
  low: { color: "success", icon: Circle, label: "低" },
};
```

#### 3. フォーム拡張 (TaskForm.tsx)
```typescript
// 優先度選択フィールドを追加
<FormField
  control={form.control}
  name="priority"
  render={({ field }) => (
    <FormItem>
      <FormLabel>優先度</FormLabel>
      <FormControl>
        <Select onValueChange={field.onChange} value={field.value || ""}>
          <SelectTrigger>
            <SelectValue placeholder="優先度を選択（任意）" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">設定しない</SelectItem>
            <SelectItem value="high">高</SelectItem>
            <SelectItem value="middle">中</SelectItem>
            <SelectItem value="low">低</SelectItem>
          </SelectContent>
        </Select>
      </FormControl>
    </FormItem>
  )}
/>
```

### AI統合設計

#### 1. AIタスクサービス拡張 (services/ai_task_service.py)
```python
class TaskGenerationResponse(BaseModel):
    title: str
    description: str
    expires_at: float | None = None
    priority: TaskPriority | None = None  # 新規フィールド

# プロンプト拡張
PRIORITY_ANALYSIS_PROMPT = """
優先度判定基準：
- High: 緊急性が高い（今日中、明日まで、ASAP、緊急、重要な会議・締切）
- Middle: 中程度の重要性（今週中、来週まで、重要だが緊急ではない）
- Low: 低優先度（時間に余裕がある、参考情報、定期的なタスク）
- None: 判断できない場合

キーワード例：
- High: "緊急", "ASAP", "今日中", "明日まで", "至急", "重要な会議"
- Middle: "今週中", "来週まで", "重要", "確認してください"
- Low: "時間があるときに", "参考まで", "定期的に"
"""
```

#### 2. AI Spoke拡張 (spokes/tasks/spoke.py)
```python
async def action_add_task(self, parameters: Dict[str, Any]) -> SpokeResponse:
    # 既存のバリデーション...

    task = create_task(
        session=self.session,
        user_id=self.current_user.id,
        title=parameters["title"],
        description=parameters.get("description"),
        expires_at=parameters.get("expires_at"),
        priority=parameters.get("priority"),  # 新規パラメータ
    )
```

## コンポーネントとインターフェース

### 新規コンポーネント

#### 1. TaskPriorityBadge
- 優先度の視覚的表示
- 色分け（高：赤、中：黄、低：緑）
- アイコン表示
- レスポンシブ対応

#### 2. TaskPrioritySelect
- 優先度選択用のセレクトボックス
- フォーム統合
- アクセシビリティ対応

### 既存コンポーネント拡張

#### 1. TaskCard
- 優先度バッジの表示
- 優先度による視覚的強調
- ホバー効果の調整

#### 2. TaskForm
- 優先度選択フィールドの追加
- バリデーション対応
- デフォルト値の処理

#### 3. TaskList
- 優先度ソートオプションの追加
- フィルタリング機能の拡張

## データモデル

### 優先度値の定義
```typescript
// フロントエンド用の文字列型（表示用）
export type TaskPriority = "high" | "middle" | "low";

// バックエンドとの整合性（参考）
const PRIORITY_VALUES = {
  high: 1,
  middle: 2,
  low: 3
} as const;
```

### ソート順序
1. 優先度: 1(High) → 2(Middle) → 3(Low) → NULL
2. セカンダリ: 期限日時（expires_at）昇順
3. ターシャリ: 作成日時（created_at）昇順

**最適化ポイント：**
- int型Enumにより数値ソートで高速処理
- NULLSLASTにより優先度未設定タスクは最後に表示

### データベースインデックス戦略
```sql
-- 効率的な複合インデックス（int型enumによる最適化）
CREATE INDEX idx_tasks_user_priority_expires ON tasks(user_id, priority, expires_at);
CREATE INDEX idx_tasks_user_completed_priority ON tasks(user_id, completed, priority);

-- 優先度ソート専用インデックス
CREATE INDEX idx_tasks_priority_sort ON tasks(user_id, completed, priority, expires_at);
```

**パフォーマンス最適化：**
- `int` 型Enumにより、CASE文を使わない直接的なソートが可能
- 標準的なBTreeインデックスが効率的に動作
- 大量データでも高速なソート処理を実現

## エラーハンドリング

### バックエンド
- 無効な優先度値のバリデーション
- データベース制約エラーの処理
- マイグレーション失敗時のロールバック

### フロントエンド
- 優先度選択時のエラー表示
- API通信エラーの適切な処理
- フォームバリデーションエラーの表示

## テスト戦略

### バックエンドテスト
1. **単体テスト**
   - 優先度enum値のバリデーション
   - ソート機能の正確性
   - AI優先度判定ロジック

2. **統合テスト**
   - API エンドポイントの動作確認
   - データベースマイグレーションの検証

### フロントエンドテスト
1. **コンポーネントテスト**
   - TaskPriorityBadge の表示確認
   - TaskForm の優先度選択機能
   - TaskCard の優先度表示

2. **E2Eテスト**
   - 優先度設定から表示までの一連の流れ
   - ソート機能の動作確認

### AIテスト
1. **優先度判定テスト**
   - 様々なメール・カレンダー内容での判定精度
   - エッジケースの処理確認

## パフォーマンス考慮事項

### データベース最適化
- 優先度カラムへのインデックス追加
- 複合インデックスによるソート最適化
- クエリプランの分析と最適化

### フロントエンド最適化
- 優先度バッジのアイコンキャッシュ
- 仮想スクロール（大量タスク対応）
- レスポンシブデザインの最適化

### AI処理最適化
- 優先度判定プロンプトの効率化
- バッチ処理での優先度設定
- キャッシュ機能の活用

## セキュリティ考慮事項

### データ保護
- 優先度情報のユーザー間分離
- API アクセス制御の維持
- 入力値のサニタイゼーション

### プライバシー
- 優先度判定時のデータ最小化
- ログ出力時の機密情報除外