---
inclusion: always
---

# Product Domain & Business Rules

Task management application with AI assistant capabilities and Google services integration via hub-and-spoke architecture.

## Core Domain Model

### Tasks (Primary Entity)
- **Required**: `uuid`, `title`, `status`, `expiration_date`, `source_type`
- **Status flow**: `pending` → `in_progress` → `completed` | `expired`
- **Source types**: `manual`, `email`, `calendar`, `ai_generated`
- **Timestamps**: Unix float for `created_at`/`updated_at`

### AI Hub-and-Spoke System
- **Hub**: Central orchestrator at `backend/app/services/ai/`
- **Spokes**: Auto-discovered plugins at `backend/app/services/ai/spokes/[name]/`
- **Requirements**: Each spoke needs `actions.json` + `spoke.py` inheriting `BaseSpoke`
- **Discovery**: Creating folder triggers automatic registration

## Mandatory Business Rules

### Task Management
- **NEVER** create tasks without expiration dates (use defaults)
- **ALWAYS** track task source for data lineage
- **VALIDATE** status transitions (no skipping: pending → in_progress → completed)
- **BLOCK** expired tasks from moving to in_progress

### AI Assistant Behavior
- Process ALL requests through hub-and-spoke system
- Require user confirmation for destructive operations
- Provide clear context about service access
- Maintain conversation context for follow-ups

### Authentication System
- **Dual mode**: Clerk (production) or email/password (development)
- **Control**: `NEXT_PUBLIC_AUTH_SYSTEM` environment variable
- **OAuth**: Per-user tokens in separate table
- **Protection**: Next.js middleware for all protected routes

### Service Integration
- **Per-user** OAuth connections (not global)
- **Graceful degradation** on service failures
- **Visible status** indicators for users
- **Auto-refresh** OAuth tokens

## Implementation Patterns

### Task Creation Flow
1. **Manual**: Form → validation → immediate feedback
2. **AI-Assisted**: Natural language → structured data → user confirmation
3. **Auto-Generated**: External service → task proposal → user review
4. **Bulk Import**: Deduplication by title/source → batch creation

### Error Handling Strategy
- **User-facing**: Friendly messages with actionable steps
- **Server-side**: Detailed logging with request context
- **Service failures**: Clear status indicators with retry options
- **Validation**: Field-specific feedback with correction hints

### Data Validation Rules
- Validate at **service layer** (business logic), not just API
- Use **Pydantic models** for request/response validation
- **Soft deletes** for user data (add `deleted_at` field)
- **Hard delete** only system/temporary data

## Development Guidelines

### AI Spoke Development
- Maintain backward compatibility when adding capabilities
- Implement error boundaries for service failures
- Update hub logic when adding new spoke actions
- Test with realistic natural language scenarios

### Feature Development Priority
1. **Core task management** functionality first
2. **Integration compatibility** with existing spokes
3. **Natural language** accessibility for AI interaction
4. **Data provenance** tracking for transparency
5. **User control** with confirmation for important actions