# Technology Stack

## Backend
- **Framework**: FastAPI with Python 3.12+
- **ORM**: SQLModel (built on SQLAlchemy)
- **Database**: PostgreSQL
- **Migrations**: Alembic
- **Authentication**: Clerk SDK + custom email/password system
- **AI/LLM**: OpenAI API
- **Google APIs**: Google Calendar, Gmail integration
- **Package Manager**: uv (modern Python package manager)
- **Code Formatting**: Black

## Frontend
- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui (Radix UI primitives)
- **Authentication**: Clerk Next.js SDK
- **State Management**: React hooks, custom hooks
- **Forms**: React Hook Form with Zod validation
- **Package Manager**: npm

## Infrastructure
- **Containerization**: Docker + Docker Compose
- **Development Database**: PostgreSQL 16 in Docker
- **Environment**: Environment variables via .env files

## Common Commands

### Development Setup
```bash
# Start entire application
docker compose up

# Build containers
docker compose build

# Database migrations
docker compose run --rm backend alembic upgrade head
docker compose run --rm backend alembic revision --autogenerate -m "migration_name"

# Backend development (without Docker)
cd backend
uv run fastapi dev --host 0.0.0.0

# Frontend development (without Docker)
cd frontend
npm run dev
```

### Code Quality
```bash
# Backend formatting
cd backend
uv run black .

# Frontend linting
cd frontend
npm run lint
```

## Key Dependencies

### Backend Critical Packages
- `fastapi[standard]` - Web framework
- `sqlmodel` - ORM and data validation
- `alembic` - Database migrations
- `clerk-backend-api` - Authentication
- `openai` - AI integration
- `google-api-python-client` - Google services

### Frontend Critical Packages
- `@clerk/nextjs` - Authentication
- `@radix-ui/*` - UI primitives
- `react-hook-form` - Form handling
- `zod` - Schema validation
- `tailwindcss` - Styling