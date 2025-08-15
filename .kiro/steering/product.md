---
inclusion: always
---

# Product Domain & Business Rules

Task management application with AI assistant capabilities and Google services integration via hub-and-spoke architecture.

## Core Domain Model

### Tasks (Primary Entity)
**Required Fields**: `uuid`, `title`, `status`, `expiration_date`, `source_type`

**Status Transitions** (ENFORCE STRICTLY):
```
pending → in_progress → completed
pending → expired (automatic)
```

**Source Types**: `manual`, `email`, `calendar`, `ai_generated`

**Timestamps**: Unix float format for `created_at`/`updated_at`

### AI Hub-and-Spoke System
**Hub Location**: `backend/app/services/ai/`
**Spoke Location**: `backend/app/services/ai/spokes/[name]/`
**Required Files**: `actions.json` + `spoke.py` (inherits `BaseSpoke`)
**Auto-Discovery**: Creating spoke folder triggers registration

## Critical Business Rules (NEVER VIOLATE)

### Task Management
- **MANDATORY**: All tasks MUST have expiration dates (use sensible defaults)
- **MANDATORY**: Track `source_type` for all tasks (data lineage)
- **FORBIDDEN**: Skip status transitions (e.g., pending → completed)
- **FORBIDDEN**: Move expired tasks to in_progress

### AI Assistant Behavior
- **REQUIRED**: Route ALL AI requests through hub-and-spoke system
- **REQUIRED**: User confirmation for destructive operations (delete, bulk changes)
- **REQUIRED**: Clear service access context in responses
- **REQUIRED**: Maintain conversation context for follow-up questions

### Authentication & Authorization
**Dual System**: Clerk (production) OR email/password (development)
**Control Variable**: `NEXT_PUBLIC_AUTH_SYSTEM`
**OAuth Storage**: Per-user tokens in dedicated table
**Route Protection**: Next.js middleware for `(authed)` routes

### Service Integration Rules
- **Per-user OAuth**: Never use global service connections
- **Graceful Degradation**: Handle service failures without breaking UX
- **Status Visibility**: Show connection status to users
- **Token Management**: Auto-refresh OAuth tokens

## Implementation Patterns (FOLLOW EXACTLY)

### Task Creation Flows
1. **Manual**: Form validation → immediate creation → user feedback
2. **AI-Assisted**: Natural language → structured data → user confirmation → creation
3. **Auto-Generated**: External service → task proposal → user review → creation
4. **Bulk Import**: Deduplication (title + source) → batch creation → summary

### Error Handling Requirements
- **User Messages**: Friendly language with actionable next steps
- **Server Logging**: Include request context and user ID
- **Service Failures**: Show clear status with retry buttons
- **Validation Errors**: Field-specific feedback with correction hints

### Data Validation Strategy
- **Service Layer**: Primary validation (business rules)
- **API Layer**: Secondary validation (Pydantic models)
- **Soft Deletes**: User data gets `deleted_at` timestamp
- **Hard Deletes**: Only temporary/system data

## AI Assistant Guidelines

### When Creating Tasks
- ALWAYS ask for expiration date if not provided
- ALWAYS set appropriate `source_type` (`ai_generated` for AI-created)
- ALWAYS validate against business rules before creation
- ALWAYS provide confirmation summary to user

### When Modifying Tasks
- VALIDATE status transitions before applying
- REQUIRE confirmation for bulk operations
- PRESERVE data lineage (don't change `source_type`)
- BLOCK modifications to expired tasks

### Natural Language Processing
- Parse user intent through hub-and-spoke system
- Provide structured data preview before execution
- Handle ambiguous requests with clarifying questions
- Maintain context for follow-up interactions

## Development Priorities (IN ORDER)
1. **Core Functionality**: Task CRUD operations with validation
2. **AI Integration**: Hub-and-spoke system compatibility
3. **Service Integration**: OAuth and external API connections
4. **User Experience**: Natural language interaction and feedback
5. **Data Integrity**: Audit trails and data provenance