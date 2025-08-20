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
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from google.oauth2.credentials import Credentials as OAuth2Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pydantic import BaseModel
from sqlmodel import Session

from app.config.auth import GoogleOAuthConfig
from app.schema import User
from app.services.google_oauth import GoogleOauthService

# Configure module logger
logger = logging.getLogger(__name__)


class AvailableTimeSlot(BaseModel):
    """利用可能な時間スロット"""

    start_time: datetime
    end_time: datetime
    duration_minutes: int


class CalendarFreeTimeResponse(BaseModel):
    """カレンダー空き時間情報"""

    available_slots: list[AvailableTimeSlot]
    search_period: str
    total_free_hours: float


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

    def __init__(self, user: User | None = None, session: Session | None = None):
        self.user = user
        self.db_session = session
        self.calendar_service = None
        self._credentials: OAuth2Credentials | None = None
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
            self.calendar_service = build("calendar", "v3", credentials=self._credentials)
            self._is_connected = True
            logger.info("Successfully connected to Google Calendar API")

        except Exception as e:
            logger.error(f"Failed to connect to Google Calendar API: {e}")
            raise GoogleCalendarServiceError(f"Connection error: {e}") from e

    async def _setup_credentials(self) -> None:
        """Set up Google OAuth credentials"""
        if not self.user or not self.db_session:
            raise GoogleCalendarAuthenticationError("User information or session information is missing")

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
                client_id=GoogleOAuthConfig.CLIENT_ID,
                client_secret=GoogleOAuthConfig.CLIENT_SECRET,
                scopes=GoogleCalendarConfig.SCOPES,
            )

        except Exception as e:
            logger.error(f"Authentication setup error: {e}")
            raise GoogleCalendarAuthenticationError(f"Failed to set up authentication: {e}") from e

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

    async def list_calendars(self) -> list[dict[str, Any]]:
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
    ) -> list[dict[str, Any]]:
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

            logger.info(f"Retrieved {len(calendar_events)} events from calendar {calendar_id}")
            return calendar_events

        except Exception as e:
            self._handle_calendar_api_error("get events", e)

    async def _process_event_data(self, event: dict[str, Any]) -> dict[str, Any]:
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
        description: str | None = None,
        location: str | None = None,
        attendees: list[str] | None = None,
        recurrence: list[str] | None = None,
    ) -> dict[str, Any]:
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
            created_event = self.calendar_service.events().insert(calendarId=calendar_id, body=event_body).execute()

            logger.info(f"Created event {created_event.get('id')} in calendar {calendar_id}")
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
        description: str | None = None,
        location: str | None = None,
        attendees: list[str] | None = None,
        recurrence: list[str] | None = None,
    ) -> dict[str, Any]:
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
            existing_event = self.calendar_service.events().get(calendarId=calendar_id, eventId=event_id).execute()

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
    ) -> dict[str, Any]:
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
            self.calendar_service.events().delete(calendarId=calendar_id, eventId=event_id).execute()

            logger.info(f"Deleted event {event_id} from calendar {calendar_id}")
            return {
                "deleted_event_id": event_id,
                "calendar_id": calendar_id,
                "status": "deleted",
            }

        except HttpError as e:
            if e.resp.status == 404:
                logger.warning(f"Event {event_id} not found in calendar {calendar_id}")
                raise GoogleCalendarAPIError("Event not found") from e
            self._handle_calendar_api_error("delete event", e)
        except Exception as e:
            self._handle_calendar_api_error("delete event", e)

    async def get_event(
        self,
        event_id: str,
        calendar_id: str = "primary",
    ) -> dict[str, Any]:
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
            event = self.calendar_service.events().get(calendarId=calendar_id, eventId=event_id).execute()

            processed_event = await self._process_event_data(event)
            logger.info(f"Retrieved event {event_id} from calendar {calendar_id}")
            return processed_event

        except Exception as e:
            self._handle_calendar_api_error("get event", e)

    async def calculate_free_time(
        self,
        start_date: datetime,
        end_date: datetime,
        calendar_id: str = "primary",
    ) -> list[dict[str, Any]]:
        """
        Calculate free time slots in the calendar within a specific date range

        Args:
            start_date: Start date for the calculation
            end_date: End date for the calculation
            calendar_id: Calendar ID (default: "primary")

        Returns:
            List of free time slot dictionaries
        """
        self._ensure_connected()

        try:
            # Normalize timezones
            start_date = self._normalize_timezone(start_date)
            end_date = self._normalize_timezone(end_date)

            # Get events within the date range
            events = await self.get_events(start_date, end_date, calendar_id)

            # Sort events by start time
            events.sort(key=lambda x: x["start_time"])

            # Calculate free time slots
            free_time_slots = []
            current_time = start_date

            for event in events:
                event_start = event["start_time"]
                event_end = event["end_time"]

                # Check for free time before the event
                if current_time < event_start:
                    free_time_slots.append(
                        {
                            "start_time": current_time,
                            "end_time": event_start,
                            "duration_minutes": int((event_start - current_time).total_seconds() / 60),
                        }
                    )

                # Move current time after the event
                current_time = max(current_time, event_end)

            # Check for free time after the last event
            if current_time < end_date:
                free_time_slots.append(
                    {
                        "start_time": current_time,
                        "end_time": end_date,
                        "duration_minutes": int((end_date - current_time).total_seconds() / 60),
                    }
                )

            logger.info(f"Calculated {len(free_time_slots)} free time slots in calendar {calendar_id}")
            return free_time_slots

        except Exception as e:
            self._handle_calendar_api_error("calculate free time", e)

    async def get_free_time(
        self,
        days_ahead: int = 7,
        min_slot_minutes: int = 30,
        work_start_hour: int = 9,
        work_end_hour: int = 18,
        calendar_id: str = "primary",
    ) -> CalendarFreeTimeResponse:
        """
        ユーザーのGoogle Calendarから空き時間を取得する

        Args:
            days_ahead: 検索する日数（デフォルト7日）
            min_slot_minutes: 最小スロット時間（分）
            work_start_hour: 業務開始時間
            work_end_hour: 業務終了時間
            calendar_id: カレンダーID（デフォルト: "primary"）

        Returns:
            空き時間情報
        """
        self._ensure_connected()

        try:
            # 検索期間を設定（現在時刻から指定日数後まで）
            jst = ZoneInfo("Asia/Tokyo")
            now = datetime.now(jst)
            start_date = now.replace(hour=work_start_hour, minute=0, second=0, microsecond=0)  # 業務開始時間から開始
            end_date = (now + timedelta(days=days_ahead)).replace(
                hour=work_end_hour, minute=0, second=0, microsecond=0
            )  # 業務終了時間まで

            # カレンダーイベントを取得
            events = await self.get_events(
                start_date=start_date,
                end_date=end_date,
                calendar_id=calendar_id,
                max_results=100,
            )

            # 既存のイベントからスロットを抽出
            occupied_slots = []
            for event in events:
                start_time = event.get("start_time")
                end_time = event.get("end_time")

                if start_time and end_time:
                    # タイムゾーンを統一
                    if start_time.tzinfo is None:
                        start_time = start_time.replace(tzinfo=jst)
                    if end_time.tzinfo is None:
                        end_time = end_time.replace(tzinfo=jst)

                    occupied_slots.append((start_time, end_time))

            # 空き時間スロットを計算
            available_slots = self._calculate_free_time_slots(
                start_date,
                end_date,
                occupied_slots,
                min_slot_minutes,
                work_start_hour,
                work_end_hour,
            )

            # 合計空き時間を計算
            total_free_hours = sum(slot.duration_minutes for slot in available_slots) / 60.0

            return CalendarFreeTimeResponse(
                available_slots=available_slots,
                search_period=f"{start_date.strftime('%Y-%m-%d')} から {end_date.strftime('%Y-%m-%d')}",
                total_free_hours=total_free_hours,
            )

        except Exception as e:
            self._handle_calendar_api_error("get free time", e)

    def _calculate_free_time_slots(
        self,
        start_date: datetime,
        end_date: datetime,
        occupied_slots: list[tuple],
        min_slot_minutes: int = 30,
        work_start_hour: int = 9,
        work_end_hour: int = 18,
    ) -> list["AvailableTimeSlot"]:
        """
        空き時間スロットを計算する

        Args:
            start_date: 検索開始日時
            end_date: 検索終了日時
            occupied_slots: 既存の予定のタイムスロット
            min_slot_minutes: 最小スロット時間（分）
            work_start_hour: 業務開始時間
            work_end_hour: 業務終了時間

        Returns:
            利用可能な時間スロットのリスト
        """
        available_slots = []
        current_date = start_date.date()
        end_date_only = end_date.date()

        # タイムゾーンを統一（JSTを使用）
        jst = ZoneInfo("Asia/Tokyo")

        while current_date <= end_date_only:
            # 平日のみ対象（土日は除外）
            if current_date.weekday() < 5:  # 0-4が月-金
                day_start = datetime.combine(current_date, datetime.min.time().replace(hour=work_start_hour)).replace(
                    tzinfo=jst
                )
                day_end = datetime.combine(current_date, datetime.min.time().replace(hour=work_end_hour)).replace(
                    tzinfo=jst
                )

                # その日の予定を取得（タイムゾーンを統一）
                day_occupied = []
                for start, end in occupied_slots:
                    # タイムゾーン情報がない場合はJSTとして扱う
                    if start.tzinfo is None:
                        start = start.replace(tzinfo=jst)
                    if end.tzinfo is None:
                        end = end.replace(tzinfo=jst)

                    # その日の範囲内の予定のみを対象とする
                    if start.date() == current_date and end > day_start and start < day_end:
                        day_occupied.append((max(start, day_start), min(end, day_end)))

                # 予定を時間順にソート
                day_occupied.sort(key=lambda x: x[0])

                # 空き時間を計算
                current_time = day_start
                for occupied_start, occupied_end in day_occupied:
                    # 空き時間があるかチェック
                    if current_time < occupied_start:
                        slot_duration = (occupied_start - current_time).total_seconds() / 60
                        if slot_duration >= min_slot_minutes:
                            available_slots.append(
                                AvailableTimeSlot(
                                    start_time=current_time,
                                    end_time=occupied_start,
                                    duration_minutes=int(slot_duration),
                                )
                            )
                    current_time = max(current_time, occupied_end)

                # 最後の予定から終業時間までの空き時間
                if current_time < day_end:
                    slot_duration = (day_end - current_time).total_seconds() / 60
                    if slot_duration >= min_slot_minutes:
                        available_slots.append(
                            AvailableTimeSlot(
                                start_time=current_time,
                                end_time=day_end,
                                duration_minutes=int(slot_duration),
                            )
                        )

            current_date += timedelta(days=1)

        return available_slots


@asynccontextmanager
async def get_google_calendar_service(user: User | None = None, session: Session | None = None):
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
        raise GoogleCalendarServiceError(f"Service creation failed: {e}") from e
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
