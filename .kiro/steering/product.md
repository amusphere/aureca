---
inclusion: always
---

# Product Overview & Development Guidelines

This is a task management application with AI assistant capabilities that integrates with Google services and other productivity tools through a dynamic hub-and-spoke architecture.

## Core Domain Concepts

- **Tasks**: Central entities with UUID, title, description, status, expiration dates, and source tracking
- **Task Sources**: Link tasks to their origin (email, calendar event, manual creation) with metadata
- **AI Hub**: Orchestrates multiple "spokes" (service integrations) for natural language task management
- **Spokes**: Independent service plugins (Gmail, Google Calendar, Tasks) that auto-register

## Product Rules & Conventions

### Task Management Rules
- Tasks MUST have expiration dates for time-sensitive actions
- Task status follows: `pending`, `in_progress`, `completed`, `expired`
- All tasks track their source (manual, email, calendar, AI-generated)
- Task UUIDs are used for external references, auto-incrementing IDs for internal operations

### AI Assistant Behavior
- Process natural language requests through the hub-and-spoke system
- Always provide context about which services are being accessed
- Maintain conversation history for context-aware responses
- Generate tasks from unstructured input (emails, calendar events, chat)

### Authentication Patterns
- Dual auth system: Clerk (default) or email/password (fallback)
- Environment variable `NEXT_PUBLIC_AUTH_SYSTEM` determines active system
- Google OAuth tokens stored separately for service integrations
- All protected routes require authentication middleware

### Service Integration Guidelines
- New spokes auto-discover by creating folder in `backend/app/services/ai/spokes/`
- Each spoke requires `actions.json` (capabilities) and `spoke.py` (implementation)
- Spokes inherit from `BaseSpoke` and implement required methods
- Service connections are per-user and stored as OAuth tokens

## User Experience Principles

### Task Creation Flow
1. **Manual**: Direct form input with validation
2. **AI-Assisted**: Natural language processing with confirmation
3. **Auto-Generated**: From emails/calendar with user review
4. **Bulk Import**: From external sources with deduplication

### Integration Connection Flow
1. User initiates OAuth flow from settings
2. Redirect to service provider (Google)
3. Store tokens securely per user
4. Enable spoke functionality automatically
5. Background sync of relevant data

### Error Handling Standards
- Always provide user-friendly error messages
- Log technical details server-side only
- Graceful degradation when services are unavailable
- Clear indication of which integrations are active/inactive

## Development Priorities

### When Adding Features
1. **Task-centric**: All features should enhance task management
2. **Integration-first**: Consider how new features work with existing spokes
3. **AI-compatible**: Ensure new functionality is accessible via natural language
4. **Source-aware**: Track origin of all data for transparency

### When Modifying AI System
- Maintain backward compatibility with existing spokes
- Update hub logic for new spoke capabilities
- Test natural language processing with realistic user inputs
- Ensure proper error handling for service failures

### Data Consistency Rules
- Use Unix timestamps for all datetime fields
- UUIDs for external references, auto-increment for internal
- Soft deletes for user data, hard deletes for system data
- Always validate data at service layer, not just API layer