"""
Google Calendar Integration Service

Provides comprehensive Google Calendar API integration including:
- Authentication management
- Calendar operations (list, create, update, delete)
- Event operations (list, create, update, delete)
- Timezone handling

This service uses Google OAuth2 for authentication and provides
both context manager and direct access patterns.
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from app.schema import User
from app.services.google_oauth import GoogleOauthService
from google.oauth2.credentials import Credentials as OAuth2Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlmodel import Session

# Configure module logger
logger = logging.getLogger(__name__)


# Google Calendar API Configuration
class GoogleCalendarConfig:
    """Google Calendar API configuration constants and limits"""

    # OAuth Scopes required for Calendar operations
    SCOPES = [
        "https://www.googleapis.com/auth/calendar",  # Full calendar access
        "https://www.googleapis.com/auth/calendar.events",  # Events access
    ]

    # API request limits
    MAX_RESULTS_LIMIT = 2500  # Google Calendar API maximum
    DEFAULT_MAX_RESULTS = 100  # Default page size

    # Default timezone
    DEFAULT_TIMEZONE = "Asia/Tokyo"

    # OAuth configuration
    OAUTH_TOKEN_URI = "https://oauth2.googleapis.com/token"


class GoogleCalendarServiceError(Exception):
    """Google Calendar service related error"""

    pass


class GoogleCalendarAuthenticationError(GoogleCalendarServiceError):
    """Google Calendar authentication related error"""

    pass


class GoogleCalendarAPIError(GoogleCalendarServiceError):
    """Google Calendar API call related error"""

    pass


class GoogleCalendarService:
    """
    Google Calendar API integration service

    Provides comprehensive Calendar operations including:
    - Calendar list and management
    - Event CRUD operations
    - Timezone handling
    - OAuth2 authentication handling

    Can be used as a context manager for automatic connection management.
    """

    def __init__(self, user: Optional[User] = None, session: Optional[Session] = None):
        self.user = user
        self.db_session = session
        self.calendar_service = None
        self._credentials: Optional[OAuth2Credentials] = None
        self._is_connected = False

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    @property
    def is_connected(self) -> bool:
        """Check if Calendar service is connected"""
        return self._is_connected and self.calendar_service is not None

    async def connect(self) -> None:
        """Connect to Google Calendar API service"""
        if self._is_connected:
            return

        try:
            logger.info("Connecting to Google Calendar API...")

            if self.user and self.db_session:
                await self._setup_credentials()

            # Build Calendar service
            self.calendar_service = build(
                "calendar", "v3", credentials=self._credentials
            )
            self._is_connected = True
            logger.info("Successfully connected to Google Calendar API")

        except Exception as e:
            logger.error(f"Failed to connect to Google Calendar API: {e}")
            raise GoogleCalendarServiceError(f"Connection error: {e}")

    async def _setup_credentials(self) -> None:
        """Set up Google OAuth credentials"""
        if not self.user or not self.db_session:
            raise GoogleCalendarAuthenticationError(
                "User information or session information is missing"
            )

        try:
            oauth_service = GoogleOauthService(self.db_session)
            credentials = oauth_service.get_credentials(self.user.id)

            if not credentials:
                raise GoogleCalendarAuthenticationError(
                    "Google authentication credentials not found. Please authenticate first."
                )

            # Build OAuth2Credentials object
            self._credentials = OAuth2Credentials(
                token=credentials.token,
                refresh_token=credentials.refresh_token,
                token_uri=GoogleCalendarConfig.OAUTH_TOKEN_URI,
                client_id=os.getenv("GOOGLE_CLIENT_ID"),
                client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
                scopes=GoogleCalendarConfig.SCOPES,
            )

        except Exception as e:
            logger.error(f"Authentication setup error: {e}")
            raise GoogleCalendarAuthenticationError(
                f"Failed to set up authentication: {e}"
            )

    async def disconnect(self) -> None:
        """Disconnect from Google Calendar API service"""
        self.calendar_service = None
        self._credentials = None
        self._is_connected = False

    def _ensure_connected(self) -> None:
        """Ensure Calendar service is connected and raise exception if not"""
        if not self.is_connected:
            raise GoogleCalendarServiceError("Not connected to Google Calendar service")

    def _handle_calendar_api_error(self, operation: str, error: Exception) -> None:
        """Handle Google Calendar API errors consistently"""
        if isinstance(error, HttpError):
            logger.error(f"Google Calendar API error during {operation}: {error}")
            raise GoogleCalendarAPIError(f"Failed to {operation}: {error}")
        else:
            logger.error(f"Error during {operation}: {error}")
            raise GoogleCalendarServiceError(f"Failed to {operation}: {error}")

    def _normalize_timezone(self, dt: datetime) -> datetime:
        """Normalize datetime to default timezone if no timezone is set"""
        if dt.tzinfo is None:
            jst = ZoneInfo(GoogleCalendarConfig.DEFAULT_TIMEZONE)
            return dt.replace(tzinfo=jst)
        return dt

    def _format_datetime_string(self, date_str: str) -> str:
        """Format datetime string for consistent processing"""
        # Handle date-only format
        if "T" not in date_str:
            date_str += "T00:00:00"

        # Handle Z suffix
        if date_str.endswith("Z"):
            date_str = date_str[:-1] + "+00:00"

        return date_str

    # Calendar operation methods

    async def list_calendars(self) -> List[Dict[str, Any]]:
        """
        List all calendars for the authenticated user

        Returns:
            List of calendar dictionaries
        """
        self._ensure_connected()

        try:
            result = self.calendar_service.calendarList().list().execute()
            calendars = result.get("items", [])

            calendar_list = []
            for calendar in calendars:
                calendar_info = {
                    "id": calendar.get("id"),
                    "summary": calendar.get("summary"),
                    "description": calendar.get("description"),
                    "primary": calendar.get("primary", False),
                    "access_role": calendar.get("accessRole"),
                    "timezone": calendar.get("timeZone"),
                }
                calendar_list.append(calendar_info)

            logger.info(f"Retrieved {len(calendar_list)} calendars")
            return calendar_list

        except Exception as e:
            self._handle_calendar_api_error("list calendars", e)

    # Event operation methods

    async def get_events(
        self,
        start_date: datetime,
        end_date: datetime,
        calendar_id: str = "primary",
        max_results: int = GoogleCalendarConfig.DEFAULT_MAX_RESULTS,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve calendar events for a specified date range

        Args:
            start_date: Start date for event retrieval
            end_date: End date for event retrieval
            calendar_id: Calendar ID (default: "primary")
            max_results: Maximum number of events to retrieve

        Returns:
            List of event dictionaries
        """
        self._ensure_connected()

        try:
            # Validate and limit max_results
            max_results = min(max_results, GoogleCalendarConfig.MAX_RESULTS_LIMIT)

            # Normalize timezones
            start_date = self._normalize_timezone(start_date)
            end_date = self._normalize_timezone(end_date)

            # Convert to RFC3339 format
            time_min = start_date.isoformat()
            time_max = end_date.isoformat()

            # Get events from API
            events_result = (
                self.calendar_service.events()
                .list(
                    calendarId=calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])
            if not events:
                logger.info(f"No events found for calendar {calendar_id}")
                return []

            # Process events
            calendar_events = []
            for event in events:
                processed_event = await self._process_event_data(event)
                calendar_events.append(processed_event)

            logger.info(
                f"Retrieved {len(calendar_events)} events from calendar {calendar_id}"
            )
            return calendar_events

        except Exception as e:
            self._handle_calendar_api_error("get events", e)

    async def _process_event_data(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw event data from Google Calendar API"""
        start = event["start"].get("dateTime", event["start"].get("date"))
        end = event["end"].get("dateTime", event["end"].get("date"))

        # Format datetime strings
        start = self._format_datetime_string(start)
        end = self._format_datetime_string(end)

        # Handle all-day events
        if "date" in event["start"]:
            end = end.replace("T00:00:00", "T23:59:59")

        # Extract attendees
        attendees = []
        if "attendees" in event:
            attendees = [attendee.get("email", "") for attendee in event["attendees"]]

        return {
            "id": event.get("id"),
            "summary": event.get("summary", ""),
            "description": event.get("description"),
            "start_time": datetime.fromisoformat(start),
            "end_time": datetime.fromisoformat(end),
            "location": event.get("location"),
            "attendees": attendees if attendees else None,
            "recurrence": event.get("recurrence"),
            "html_link": event.get("htmlLink"),
            "status": event.get("status"),
        }

    async def create_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        calendar_id: str = "primary",
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        recurrence: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new calendar event

        Args:
            summary: Event title
            start_time: Event start time
            end_time: Event end time
            calendar_id: Calendar ID (default: "primary")
            description: Event description (optional)
            location: Event location (optional)
            attendees: List of attendee email addresses (optional)
            recurrence: List of recurrence rules (optional)

        Returns:
            Dictionary with created event information
        """
        self._ensure_connected()

        try:
            # Normalize timezones
            start_time = self._normalize_timezone(start_time)
            end_time = self._normalize_timezone(end_time)

            # Build event body
            event_body = {
                "summary": summary,
                "start": {
                    "dateTime": start_time.isoformat(),
                    "timeZone": GoogleCalendarConfig.DEFAULT_TIMEZONE,
                },
                "end": {
                    "dateTime": end_time.isoformat(),
                    "timeZone": GoogleCalendarConfig.DEFAULT_TIMEZONE,
                },
            }

            if description:
                event_body["description"] = description

            if location:
                event_body["location"] = location

            if attendees:
                event_body["attendees"] = [{"email": email} for email in attendees]

            if recurrence:
                event_body["recurrence"] = recurrence

            # Create event
            created_event = (
                self.calendar_service.events()
                .insert(calendarId=calendar_id, body=event_body)
                .execute()
            )

            logger.info(
                f"Created event {created_event.get('id')} in calendar {calendar_id}"
            )
            return {
                "event_id": created_event.get("id"),
                "html_link": created_event.get("htmlLink"),
                "status": created_event.get("status"),
            }

        except Exception as e:
            self._handle_calendar_api_error("create event", e)

    async def update_event(
        self,
        event_id: str,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        calendar_id: str = "primary",
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        recurrence: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing calendar event

        Args:
            event_id: ID of the event to update
            summary: Event title
            start_time: Event start time
            end_time: Event end time
            calendar_id: Calendar ID (default: "primary")
            description: Event description (optional)
            location: Event location (optional)
            attendees: List of attendee email addresses (optional)
            recurrence: List of recurrence rules (optional)

        Returns:
            Dictionary with updated event information
        """
        self._ensure_connected()

        try:
            # Get existing event
            existing_event = (
                self.calendar_service.events()
                .get(calendarId=calendar_id, eventId=event_id)
                .execute()
            )

            # Normalize timezones
            start_time = self._normalize_timezone(start_time)
            end_time = self._normalize_timezone(end_time)

            # Update event data
            existing_event["summary"] = summary
            existing_event["start"] = {
                "dateTime": start_time.isoformat(),
                "timeZone": GoogleCalendarConfig.DEFAULT_TIMEZONE,
            }
            existing_event["end"] = {
                "dateTime": end_time.isoformat(),
                "timeZone": GoogleCalendarConfig.DEFAULT_TIMEZONE,
            }

            if description is not None:
                existing_event["description"] = description

            if location is not None:
                existing_event["location"] = location

            if attendees is not None:
                existing_event["attendees"] = [{"email": email} for email in attendees]

            if recurrence is not None:
                existing_event["recurrence"] = recurrence

            # Update event
            updated_event = (
                self.calendar_service.events()
                .update(
                    calendarId=calendar_id,
                    eventId=event_id,
                    body=existing_event,
                )
                .execute()
            )

            logger.info(f"Updated event {event_id} in calendar {calendar_id}")
            return {
                "event_id": updated_event.get("id"),
                "html_link": updated_event.get("htmlLink"),
                "status": updated_event.get("status"),
            }

        except Exception as e:
            self._handle_calendar_api_error("update event", e)

    async def delete_event(
        self,
        event_id: str,
        calendar_id: str = "primary",
    ) -> Dict[str, Any]:
        """
        Delete a calendar event

        Args:
            event_id: ID of the event to delete
            calendar_id: Calendar ID (default: "primary")

        Returns:
            Dictionary with deletion result
        """
        self._ensure_connected()

        try:
            self.calendar_service.events().delete(
                calendarId=calendar_id, eventId=event_id
            ).execute()

            logger.info(f"Deleted event {event_id} from calendar {calendar_id}")
            return {
                "deleted_event_id": event_id,
                "calendar_id": calendar_id,
                "status": "deleted",
            }

        except HttpError as e:
            if e.resp.status == 404:
                logger.warning(f"Event {event_id} not found in calendar {calendar_id}")
                raise GoogleCalendarAPIError("Event not found")
            self._handle_calendar_api_error("delete event", e)
        except Exception as e:
            self._handle_calendar_api_error("delete event", e)

    async def get_event(
        self,
        event_id: str,
        calendar_id: str = "primary",
    ) -> Dict[str, Any]:
        """
        Get a specific calendar event

        Args:
            event_id: ID of the event to retrieve
            calendar_id: Calendar ID (default: "primary")

        Returns:
            Dictionary with event information
        """
        self._ensure_connected()

        try:
            event = (
                self.calendar_service.events()
                .get(calendarId=calendar_id, eventId=event_id)
                .execute()
            )

            processed_event = await self._process_event_data(event)
            logger.info(f"Retrieved event {event_id} from calendar {calendar_id}")
            return processed_event

        except Exception as e:
            self._handle_calendar_api_error("get event", e)


# Factory functions and utilities


@asynccontextmanager
async def get_google_calendar_service(
    user: Optional[User] = None, session: Optional[Session] = None
):
    """
    Create and manage GoogleCalendarService as a context manager

    Args:
        user: User information (required for authenticated operations)
        session: Database session (required for authenticated operations)

    Yields:
        GoogleCalendarService: Configured Calendar service instance

    Raises:
        GoogleCalendarServiceError: If service creation or connection fails
    """
    service = GoogleCalendarService(user=user, session=session)
    try:
        await service.connect()
        yield service
    except Exception as e:
        logger.error(f"Failed to create Google Calendar service: {e}")
        raise GoogleCalendarServiceError(f"Service creation failed: {e}")
    finally:
        await service.disconnect()


@asynccontextmanager
async def get_authenticated_google_calendar_service(user: User, session: Session):
    """
    Create authenticated GoogleCalendarService context manager

    Args:
        user: User information (required)
        session: Database session (required)

    Yields:
        GoogleCalendarService: Authenticated Calendar service instance

    Raises:
        GoogleCalendarAuthenticationError: If user or session is missing
        GoogleCalendarServiceError: If service creation fails
    """
    if not user:
        raise GoogleCalendarAuthenticationError("User information is required")
    if not session:
        raise GoogleCalendarAuthenticationError("Database session is required")

    async with get_google_calendar_service(user=user, session=session) as service:
        yield service
