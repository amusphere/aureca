# Project Structure & Architecture

## Overall Organization

```
├── backend/           # FastAPI Python backend
├── frontend/          # Next.js TypeScript frontend
└── docker-compose.yml # Development orchestration
```

## Backend Architecture (`backend/`)

### Layered Architecture Pattern
- **Routers** → **Services** → **Repositories** → **Database**
- Clear separation of concerns with dependency injection

```
backend/
├── app/
│   ├── routers/           # API endpoints (FastAPI routers)
│   │   ├── api/          # Versioned API routes
│   │   └── routers.py    # Main router registration
│   ├── services/         # Business logic layer
│   │   └── ai/          # AI assistant hub-and-spoke system
│   ├── repositories/     # Data access layer
│   ├── models/          # Pydantic request/response models
│   ├── utils/           # Utility functions
│   ├── migrations/      # Alembic database migrations
│   ├── database.py      # Database connection setup
│   └── schema.py        # SQLModel table definitions
├── main.py              # FastAPI application entry point
└── pyproject.toml       # Dependencies and project config
```

### AI System Architecture
- **Dynamic Hub-and-Spoke**: Extensible plugin system
- **Spokes**: Independent service integrations (Gmail, Calendar, Tasks)
- **Auto-discovery**: New spokes added by creating folders in `spokes/`

## Frontend Architecture (`frontend/`)

### Next.js App Router Structure
```
frontend/
├── app/                 # Next.js App Router
│   ├── (authed)/       # Protected routes group
│   ├── api/            # API route handlers
│   ├── auth/           # Authentication pages
│   └── layout.tsx      # Root layout
├── components/         # React components
│   ├── components/     # Feature components
│   │   ├── ui/        # shadcn/ui components (DO NOT MODIFY)
│   │   ├── commons/   # Shared components
│   │   ├── forms/     # Form components
│   │   └── tasks/     # Task-specific components
│   ├── hooks/         # Custom React hooks
│   ├── lib/           # Utility libraries
│   └── pages/         # Page-level components
├── types/             # TypeScript type definitions
└── utils/             # Utility functions
```

## Key Conventions

### Backend Conventions
- **File naming**: Snake_case for Python files
- **API routes**: Prefixed with `/api`, grouped by feature
- **Database models**: Use SQLModel with UUID primary keys
- **Services**: Async/await pattern throughout
- **Error handling**: Custom exceptions in `utils/exceptions.py`

### Frontend Conventions
- **File naming**: PascalCase for components, camelCase for utilities
- **Components**: Functional components with TypeScript
- **Routing**: File-based routing with App Router
- **State**: Custom hooks for complex state management
- **Styling**: Tailwind utility classes, shadcn/ui for components

### Authentication Patterns
- **Dual system**: Supports both Clerk and email/password
- **Environment-driven**: `NEXT_PUBLIC_AUTH_SYSTEM` determines auth method
- **Middleware**: Route protection via Next.js middleware

### Database Patterns
- **Timestamps**: Use Unix timestamps (float) for created_at/updated_at
- **UUIDs**: All entities have UUID fields for external references
- **Relationships**: SQLModel relationships with proper foreign keys
- **Migrations**: Always use Alembic, never manual schema changes

## Development Workflow

### Adding New Features

#### Backend Endpoint
1. Create router in `app/routers/api/`
2. Add business logic in `app/services/`
3. Create repository methods in `app/repositories/`
4. Define models in `app/models/`
5. Register router in `app/routers/routers.py`

#### Frontend Page
1. Create page in `app/` (use `(authed)/` for protected routes)
2. Build components in `components/components/`
3. Add types in `types/`
4. Create custom hooks in `components/hooks/` if needed

#### Database Changes
1. Modify `app/schema.py`
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Review and apply: `alembic upgrade head`

### AI Spoke Development
1. Create folder in `backend/app/services/ai/spokes/`
2. Add `actions.json` with action definitions
3. Implement `spoke.py` inheriting from `BaseSpoke`
4. System auto-discovers on restart