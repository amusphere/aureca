---
inclusion: always
---

# Technology Stack & Development Guidelines

## Core Technologies

### Backend (Python 3.12+)
- **Framework**: FastAPI with async/await (REQUIRED)
- **ORM**: SQLModel (MANDATORY for all models)
- **Database**: PostgreSQL with `id` (auto-increment) + `uuid` (external refs)
- **Migrations**: Alembic (NEVER edit schema.py directly)
- **Package Manager**: `uv` (use `uv run` for all commands)
- **Auth**: Clerk SDK + email/password fallback
- **AI**: OpenAI API via `backend/app/utils/llm.py`

### Frontend (Next.js 15)
- **Framework**: Next.js App Router (`app/` directory)
- **Language**: TypeScript (MANDATORY)
- **Styling**: Tailwind CSS + shadcn/ui (DO NOT modify ui components)
- **Auth**: `@clerk/nextjs` with middleware
- **State**: Custom hooks in `components/hooks/`
- **Forms**: React Hook Form + Zod validation

## Critical Code Patterns

### Backend (ENFORCE)
```python
# ALWAYS async/await
async def get_tasks(user_id: str) -> List[Task]:
    return await task_repository.get_by_user(user_id)

# ALWAYS SQLModel with standard fields
class Task(SQLModel, table=True):
    id: int = Field(primary_key=True)
    uuid: str = Field(default_factory=lambda: str(uuid4()))
    created_at: float = Field(default_factory=time.time)

# NEVER skip service layer: Router → Service → Repository → Database
```

### Frontend (ENFORCE)
```typescript
// ALWAYS TypeScript interfaces
interface TaskProps {
  task: Task;
  onUpdate: (task: Task) => void;
}

// ALWAYS custom hooks for state
const { tasks, loading, error } = useTasks();

// ALWAYS shadcn/ui components
import { Button } from "@/components/ui/button";
```

## Database Rules (CRITICAL)
- **Schema Changes**: Use Alembic migrations ONLY
- **Migration Command**: `alembic revision --autogenerate -m "description"`
- **Timestamps**: Unix float format
- **Primary Keys**: Auto-increment `id` + UUID `uuid`

## Essential Commands

### Development
```bash
# Full stack
docker compose up

# Backend only
cd backend && uv run fastapi dev --host 0.0.0.0

# Frontend only
cd frontend && npm run dev
```

### Database
```bash
# Apply migrations
docker compose run --rm backend alembic upgrade head

# Create migration
docker compose run --rm backend alembic revision --autogenerate -m "feature"
```

### Code Quality (REQUIRED)
```bash
# Backend
cd backend && uv run black .

# Frontend
cd frontend && npm run build
```

## Package Management
```bash
# Backend
cd backend && uv add package-name

# Frontend
cd frontend && npm install package-name
```

## Environment Variables
- **Backend**: `DATABASE_URL`, `OPENAI_API_KEY`, `CLERK_SECRET_KEY`
- **Frontend**: `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
- **Auth Control**: `NEXT_PUBLIC_AUTH_SYSTEM=clerk|email`