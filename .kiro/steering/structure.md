---
inclusion: always
---

# Architecture & Code Organization

## Layered Architecture (STRICT ENFORCEMENT)

### Backend: Router → Service → Repository → Database
- **Routers** (`routers/api/`): HTTP endpoints only, delegate to services
- **Services** (`services/`): Business logic only, NO direct database calls
- **Repositories** (`repositories/`): Database operations only, NO business logic
- **Models** (`models/`): Pydantic request/response validation

### Frontend: Page → Component → Hook → Utility
- **Pages** (`app/`): Route handlers, minimal logic
- **Components** (`components/components/`): Pure UI, NO business logic
- **Hooks** (`components/hooks/`): State management and API calls
- **Utils** (`utils/`): Pure functions only

## Critical File Structure

### Backend (`backend/app/`)
```
routers/api/        # FastAPI endpoints (register in routers.py)
services/           # Business logic layer
repositories/       # Database access layer
models/             # Pydantic models
schema.py           # SQLModel tables (NEVER edit directly)
database.py         # DB connection
utils/exceptions.py # Custom exceptions
```

### Frontend (`frontend/`)
```
app/(authed)/           # Protected routes
app/(public)/           # Public routes
components/hooks/       # React hooks
components/components/  # UI components
types/                 # TypeScript definitions
utils/                 # Pure functions
```

## AI Hub-and-Spoke System
- **Location**: `backend/app/services/ai/spokes/[name]/`
- **Required Files**: `actions.json` + `spoke.py` (inherits `BaseSpoke`)
- **Auto-discovery**: Folder creation triggers registration
- **Pattern**: Self-contained spokes with clear action definitions

## Code Standards (NON-NEGOTIABLE)

### Backend
- **Naming**: snake_case files/functions, PascalCase classes
- **Routes**: `/api/` prefix, domain grouping (`/api/tasks/`)
- **Async**: All service methods use `async/await`
- **Imports**: Absolute from `app.` root
- **Database**: SQLModel with `id` (auto-increment) + `uuid` fields

### Frontend
- **Naming**: PascalCase components, camelCase utilities
- **Components**: Functional with TypeScript interfaces
- **State**: Custom hooks, avoid prop drilling
- **Styling**: Tailwind only, NEVER modify shadcn/ui
- **Types**: All interfaces in `types/` directory

### Database (CRITICAL)
- **Schema Changes**: Alembic migrations ONLY
- **Command**: `alembic revision --autogenerate -m "description"`
- **Timestamps**: Unix float format
- **NEVER**: Edit `schema.py` directly

## Development Workflows

### Backend Feature
1. Update `schema.py` → Generate migration
2. Create repository methods
3. Define Pydantic models
4. Implement service logic
5. Create router endpoints
6. Register in `routers.py`

### Frontend Feature
1. Define types in `types/`
2. Create hooks in `components/hooks/`
3. Build components in `components/components/`
4. Create pages in `app/`

### AI Spoke
1. Create `spokes/[name]/` folder
2. Define `actions.json`
3. Implement `spoke.py` (inherits `BaseSpoke`)
4. Restart backend

## Authentication
- **Dual System**: Clerk OR email/password
- **Control**: `NEXT_PUBLIC_AUTH_SYSTEM` env var
- **Protection**: Next.js middleware for `(authed)` routes
- **OAuth**: Per-user token storage