---
inclusion: always
---

# Technology Stack & Development Guidelines

## Stack Overview
- **Backend**: FastAPI + SQLModel + PostgreSQL + Alembic + `uv`
- **Frontend**: Next.js 15 + TypeScript + Tailwind + shadcn/ui
- **Auth**: Clerk SDK with email/password fallback
- **AI**: OpenAI API via `backend/app/utils/llm.py`

## Critical Rules (NON-NEGOTIABLE)

### Backend Patterns
```python
# MANDATORY: All functions async/await
async def get_tasks(user_id: str) -> List[Task]:
    return await task_repository.get_by_user(user_id)

# MANDATORY: SQLModel with standard fields
class Task(SQLModel, table=True):
    id: int = Field(primary_key=True)
    uuid: str = Field(default_factory=lambda: str(uuid4()))
    created_at: float = Field(default_factory=time.time)

# MANDATORY: Layer separation - Router → Service → Repository
```

### Frontend Patterns
```typescript
// MANDATORY: TypeScript interfaces for all props
interface TaskProps {
  task: Task;
  onUpdate: (task: Task) => void;
}

// MANDATORY: Custom hooks for state management
const { tasks, loading, error } = useTasks();

// MANDATORY: Use shadcn/ui components (NEVER modify)
import { Button } from "@/components/ui/button";
```

### Database Rules
- **NEVER** edit `schema.py` directly - use Alembic migrations only
- **ALWAYS** use Unix float timestamps (`time.time()`)
- **ALWAYS** include both `id` (auto-increment) and `uuid` fields
- **Migration Command**: `alembic revision --autogenerate -m "description"`

## Essential Commands

### Development
```bash
# Full stack
docker compose up

# Backend only (use uv for all Python commands)
cd backend && uv run fastapi dev --host 0.0.0.0

# Frontend only
cd frontend && npm run dev

# Database migrations
docker compose run --rm backend alembic upgrade head
```

### Package Management
```bash
# Backend (ALWAYS use uv)
cd backend && uv add package-name

# Frontend
cd frontend && npm install package-name
```

## Code Quality Standards
- **Backend**: Use `uv run black .` for formatting
- **Frontend**: TypeScript strict mode, build must pass
- **Testing**: Run tests before commits
- **Imports**: Absolute imports from `app.` root (backend)

## Environment Variables
```bash
# Backend
DATABASE_URL=postgresql://...
OPENAI_API_KEY=sk-...
CLERK_SECRET_KEY=sk_...

# Frontend
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_...
NEXT_PUBLIC_AUTH_SYSTEM=clerk  # or 'email'
```

## File Structure Conventions
- **Backend**: `routers/` → `services/` → `repositories/` → `models/`
- **Frontend**: `app/` → `components/` → `hooks/` → `utils/`
- **Naming**: snake_case (Python), camelCase (TypeScript), PascalCase (components)