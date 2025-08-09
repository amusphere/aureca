---
inclusion: always
---

# Architecture & Code Organization

## Layered Architecture (MANDATORY)

### Backend: Router → Service → Repository → Database
- **Routers** (`routers/api/`): HTTP only, NO business logic, delegate to services
- **Services** (`services/`): Business logic only, NEVER direct database calls
- **Repositories** (`repositories/`): Database operations only, NO business logic
- **Models** (`models/`): Pydantic validation for requests/responses

### Frontend: Page → Component → Hook → Utility
- **Pages** (`app/`): Route handlers, minimal logic
- **Components** (`components/components/`): Pure UI, NO business logic
- **Hooks** (`components/hooks/`): State management and API integration
- **Utils** (`utils/`): Pure functions only

## File Organization Rules

### Backend Structure (`backend/app/`)
```
routers/api/        # FastAPI endpoints - register in routers.py
services/           # Business logic layer
repositories/       # Database access layer
models/             # Pydantic request/response models
schema.py           # SQLModel database tables
database.py         # Database connection setup
utils/exceptions.py # Custom exception classes
```

### Frontend Structure (`frontend/`)
```
app/(authed)/           # Protected routes ONLY
app/(public)/           # Public routes ONLY
app/api/               # Next.js API routes
components/hooks/      # Custom React hooks
components/components/ # Reusable UI components
types/                # TypeScript type definitions
utils/                # Pure utility functions
```

## AI System (Hub-and-Spoke)
- **Location**: `backend/app/services/ai/spokes/[name]/`
- **Auto-discovery**: Create folder → automatic registration
- **Required**: `actions.json` + `spoke.py` inheriting `BaseSpoke`
- **Pattern**: Each spoke is self-contained with clear action definitions

## Code Conventions (ENFORCE)

### Backend Rules
- **Naming**: snake_case for files/functions, PascalCase for classes
- **Routes**: Always prefix `/api/`, group by domain (e.g., `/api/tasks/`)
- **Async**: Use `async/await` for all service methods
- **Imports**: Absolute imports from `app.` root
- **Exceptions**: Use custom exceptions from `utils/exceptions.py`
- **Database**: SQLModel with auto-increment `id` + `uuid` fields

### Frontend Rules
- **Naming**: PascalCase for components, camelCase for utilities
- **Components**: Functional components with TypeScript interfaces
- **State**: Use custom hooks for complex state, avoid prop drilling
- **Styling**: Tailwind classes only, DO NOT modify shadcn/ui components
- **Types**: Define all interfaces in `types/` directory
- **Routes**: Protected routes in `(authed)`, public in `(public)`

### Database Rules (CRITICAL)
- **Schema Changes**: ALWAYS use Alembic migrations, NEVER edit schema.py directly
- **Timestamps**: Unix float format for `created_at`/`updated_at`
- **Primary Keys**: Auto-increment `id` + UUID `uuid` for external references
- **Commands**: `alembic revision --autogenerate -m "description"`

## Development Workflows (FOLLOW ORDER)

### Adding Backend Feature
1. Update `schema.py` (if needed)
2. Generate migration: `alembic revision --autogenerate`
3. Create repository methods
4. Define Pydantic models
5. Implement service logic
6. Create router endpoints
7. Register router in `routers.py`

### Adding Frontend Feature
1. Define TypeScript types in `types/`
2. Create custom hooks in `components/hooks/`
3. Build UI components in `components/components/`
4. Create page components in `app/`

### Adding AI Spoke
1. Create folder: `spokes/[name]/`
2. Define `actions.json` with available actions
3. Implement `spoke.py` inheriting from `BaseSpoke`
4. Restart backend for auto-registration

## Authentication Patterns
- **Dual System**: Clerk (production) or email/password (development)
- **Control**: `NEXT_PUBLIC_AUTH_SYSTEM` environment variable
- **Protection**: Next.js middleware for route protection
- **OAuth**: Per-user token storage in separate database table