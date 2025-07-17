# Product Overview

This is a task management application with AI assistant capabilities that integrates with various external services like Google Calendar, Gmail, and other productivity tools.

## Core Features

- **Task Management**: Create, update, and track tasks with expiration dates
- **AI Assistant**: Natural language processing for task creation and management using a dynamic hub-and-spoke architecture
- **Service Integrations**: Google Calendar, Gmail, and extensible plugin system for additional services
- **Authentication**: Supports both Clerk and email/password authentication systems
- **Multi-source Tasks**: Tasks can be created from emails, calendar events, and other external sources

## Key User Flows

1. **Task Creation**: Users can create tasks manually or through AI assistant natural language processing
2. **Service Integration**: Connect Google accounts to automatically generate tasks from emails and calendar events
3. **AI Interaction**: Chat with AI assistant to manage tasks, schedule events, and process information
4. **Task Sources**: View and manage tasks with their original sources (email, calendar, etc.)

## Architecture Philosophy

The application follows a layered architecture with clear separation between presentation, business logic, and data access layers. The AI system uses a dynamic plugin architecture allowing easy addition of new service integrations without code changes to the core system.