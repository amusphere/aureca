---
inclusion: always
---

# Architecture & Code Organization

## Layered Architecture Rules

### Backend: Router → Service → Repository → Database
- **NEVER** put business logic in routers - only request/response handling
- **ALWAYS** use services for business logic and orchestration
- **ALWAYS** use repositories for database operations
- **NEVER** access database directly from services

### Frontend: Page → Component → Hook → Utility
- **ALWAYS** use custom hooks for complex state management
- **NEVER** put business logic directly in components
- **ALWAYS** use TypeScript for type safety

## Critical File Locations

### Backend Structure
```
backend/app/
├── routers/api/        # FastAPI endpoints - register in routers.py
├── services/           # Business logic layer
├── repositories/       # Database access layer
├── models/            # Pydantic request/response models
├── schema.py          # SQLModel database tables
└── database.py        # Database connection
```

### Frontend Structure
```
frontend/
├── app/(authed)/      # Protected routes ONLY
├── app/api/           # API route handlers
├── components/components/ui/  # shadcn/ui - DO NOT MODIFY
├── components/hooks/  # Custom React hooks
├── types/            # TypeScript definitions
└── utils/            # Utility functions
```

## AI System Architecture
- **Hub-and-Spoke**: Extensible plugin system in `backend/app/services/ai/spokes/`
- **Auto-discovery**: New spokes auto-register by folder creation
- **Required files**: `actions.json` + `spoke.py` inheriting `BaseSpoke`

## Mandatory Coding Conventions

### Backend Rules
- **File naming**: snake_case for Python files
- **API routes**: MUST be prefixed with `/api/` and grouped by feature
- **Database models**: MUST use SQLModel with UUID primary keys
- **Services**: MUST use async/await pattern throughout
- **Error handling**: MUST use custom exceptions from `utils/exceptions.py`
- **Imports**: MUST use absolute imports from app root

### Frontend Rules
- **File naming**: PascalCase for components, camelCase for utilities
- **Components**: MUST be functional components with TypeScript
- **Protected routes**: MUST be in `app/(authed)/` directory
- **State management**: MUST use custom hooks for complex state
- **Styling**: MUST use Tailwind classes, shadcn/ui components
- **Types**: MUST define interfaces in `types/` directory

### Database Rules
- **Timestamps**: MUST use Unix timestamps (float) for created_at/updated_at
- **Primary keys**: MUST use UUIDs for external references
- **Migrations**: MUST use Alembic - NEVER manual schema changes
- **Relationships**: MUST use SQLModel relationships with proper foreign keys

### Authentication Rules
- **Dual system**: Clerk (default) or email/password (fallback)
- **Environment control**: `NEXT_PUBLIC_AUTH_SYSTEM` determines active method
- **Route protection**: MUST use Next.js middleware for protected routes
- **Google OAuth**: Store tokens separately in google_oauth_tokens table

## Development Patterns

### Backend Endpoint Creation (REQUIRED ORDER)
1. **Schema**: Define/update SQLModel tables in `app/schema.py`
2. **Migration**: Generate with `alembic revision --autogenerate -m "description"`
3. **Repository**: Create data access methods in `app/repositories/`
4. **Models**: Define Pydantic request/response models in `app/models/`
5. **Service**: Implement business logic in `app/services/`
6. **Router**: Create FastAPI endpoints in `app/routers/api/`
7. **Registration**: Add router to `app/routers/routers.py`

### Frontend Feature Creation (REQUIRED ORDER)
1. **Types**: Define TypeScript interfaces in `types/`
2. **Hooks**: Create custom hooks in `components/hooks/` for state/API
3. **Components**: Build UI components in `components/components/`
4. **Pages**: Create page components in `app/` (use `(authed)/` for protected)

### AI Spoke Development (AUTO-DISCOVERY)
1. **Folder**: Create in `backend/app/services/ai/spokes/[spoke_name]/`
2. **Actions**: Define capabilities in `actions.json`
3. **Implementation**: Create `spoke.py` inheriting from `BaseSpoke`
4. **Auto-registration**: System discovers on restart

### Database Migration Rules
- **NEVER** modify schema.py without creating migration
- **ALWAYS** review auto-generated migrations before applying
- **MUST** use descriptive migration messages
- **REQUIRED** command: `alembic upgrade head` to apply