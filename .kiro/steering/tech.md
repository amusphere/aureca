---
inclusion: always
---

# Technology Stack & Development Guidelines

## Backend Stack (Python 3.12+)
- **Framework**: FastAPI with async/await patterns
- **ORM**: SQLModel (SQLAlchemy-based) - MUST use for all database models
- **Database**: PostgreSQL with UUID primary keys
- **Migrations**: Alembic - REQUIRED for all schema changes
- **Authentication**: Dual system - Clerk SDK (default) + email/password fallback
- **AI/LLM**: OpenAI API integration via `backend/app/utils/llm.py`
- **Google APIs**: Calendar/Gmail via `google-api-python-client`
- **Package Manager**: `uv` - use `uv run` for all Python commands
- **Code Style**: Black formatting - run before commits

## Frontend Stack (Next.js 15)
- **Framework**: Next.js App Router - use `app/` directory structure
- **Language**: TypeScript - MANDATORY for all new code
- **Styling**: Tailwind CSS with shadcn/ui components
- **Authentication**: `@clerk/nextjs` with middleware protection
- **State**: Custom React hooks in `components/hooks/`
- **Forms**: React Hook Form + Zod validation
- **Package Manager**: npm

## Critical Development Patterns

### Backend Code Conventions
```python
# ALWAYS use async/await
async def get_tasks(user_id: str) -> List[Task]:
    return await task_repository.get_by_user(user_id)

# ALWAYS use SQLModel for database models
class Task(SQLModel, table=True):
    id: int = Field(primary_key=True)
    uuid: str = Field(default_factory=lambda: str(uuid4()))

# ALWAYS use repositories for database access
# Service -> Repository -> Database (NEVER skip layers)
```

### Frontend Code Conventions
```typescript
// ALWAYS use TypeScript interfaces
interface TaskProps {
  task: Task;
  onUpdate: (task: Task) => void;
}

// ALWAYS use custom hooks for state management
const { tasks, loading, error } = useTasks();

// ALWAYS use shadcn/ui components
import { Button } from "@/components/ui/button";
```

### Database Patterns
- **Primary Keys**: Auto-increment `id` + UUID `uuid` for external refs
- **Timestamps**: Unix timestamps (float) for `created_at`/`updated_at`
- **Migrations**: `alembic revision --autogenerate -m "description"`
- **Relationships**: Use SQLModel relationships with proper foreign keys

## Essential Commands

### Development Workflow
```bash
# Start full stack
docker compose up

# Backend only (with hot reload)
cd backend && uv run fastapi dev --host 0.0.0.0

# Frontend only (with hot reload)
cd frontend && npm run dev

# Database migrations
docker compose run --rm backend alembic upgrade head
docker compose run --rm backend alembic revision --autogenerate -m "add_feature"

# Code formatting
cd backend && uv run black .
cd frontend && npm run lint
```

### Testing & Quality
```bash
# Backend formatting (REQUIRED before commits)
cd backend && uv run black .

# Frontend type checking
cd frontend && npm run build

# Container rebuild after dependency changes
docker compose build --no-cache
```

## Package Management Rules

### Backend Dependencies
- **Core**: `fastapi[standard]`, `sqlmodel`, `alembic`
- **Auth**: `clerk-backend-api` for Clerk integration
- **AI**: `openai` for LLM features
- **Google**: `google-api-python-client`, `google-auth`
- **Add new**: `cd backend && uv add package-name`

### Frontend Dependencies
- **Core**: `@clerk/nextjs`, `@radix-ui/*`, `react-hook-form`, `zod`
- **UI**: `tailwindcss`, `@tailwindcss/typography`
- **Add new**: `cd frontend && npm install package-name`

## Environment Configuration
- **Backend**: `.env` file with `DATABASE_URL`, `OPENAI_API_KEY`, `CLERK_SECRET_KEY`
- **Frontend**: `.env.local` with `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
- **Auth System**: `NEXT_PUBLIC_AUTH_SYSTEM=clerk` or `email` to switch modes
- **Docker**: Uses `.env` files automatically via docker-compose.yml