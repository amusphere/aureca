from datetime import datetime
from typing import Any, Dict, Optional

from app.schema import User
from app.services.ai.core.models import SpokeResponse
from app.services.ai.spokes.base import BaseSpoke
from app.services.google_calendar_service import (
    GoogleCalendarAPIError,
    GoogleCalendarAuthenticationError,
    GoogleCalendarService,
    GoogleCalendarServiceError,
)
from sqlmodel import Session


class GoogleCalendarSpoke(BaseSpoke):
    """Google Calendar操作を提供するスポーク"""

    def __init__(
        self,
        session: Optional[Session] = None,
        current_user: Optional[User] = None,
    ):
        super().__init__(session=session, current_user=current_user)

    async def _get_calendar_service(self) -> GoogleCalendarService:
        """Google Calendar APIサービスを取得"""
        service = GoogleCalendarService(user=self.current_user, session=self.session)
        await service.connect()
        return service

    # =================
    # アクション関数群
    # =================

    async def action_get_calendar_events(
        self, parameters: Dict[str, Any]
    ) -> SpokeResponse:
        """カレンダーイベント取得アクション"""
        try:
            # パラメータから日付を解析
            start_date = datetime.fromisoformat(parameters["start_date"])
            end_date = datetime.fromisoformat(parameters["end_date"])
            calendar_id = parameters.get("calendar_id", "primary")
            max_results = parameters.get("max_results", 100)

            # Google Calendar APIサービスを取得
            service = await self._get_calendar_service()

            try:
                # イベントを取得
                calendar_events = await service.get_events(
                    start_date=start_date,
                    end_date=end_date,
                    calendar_id=calendar_id,
                    max_results=max_results,
                )

                return SpokeResponse(
                    success=True,
                    data=calendar_events,
                    metadata={
                        "total_events": len(calendar_events),
                        "period": f"{start_date.date()} to {end_date.date()}",
                    },
                )

            finally:
                await service.disconnect()

        except GoogleCalendarAuthenticationError as e:
            return SpokeResponse(success=False, error=f"Authentication error: {str(e)}")
        except GoogleCalendarAPIError as e:
            return SpokeResponse(
                success=False, error=f"Google Calendar API error: {str(e)}"
            )
        except GoogleCalendarServiceError as e:
            return SpokeResponse(
                success=False, error=f"Calendar service error: {str(e)}"
            )
        except Exception as e:
            return SpokeResponse(success=False, error=f"Unexpected error: {str(e)}")

    async def action_create_calendar_event(
        self, parameters: Dict[str, Any]
    ) -> SpokeResponse:
        """カレンダーイベント作成アクション"""
        try:
            calendar_id = parameters.get("calendar_id", "primary")
            start_dt = datetime.fromisoformat(parameters["start_time"])
            end_dt = datetime.fromisoformat(parameters["end_time"])

            # Google Calendar APIサービスを取得
            service = await self._get_calendar_service()

            try:
                # イベントを作成
                result = await service.create_event(
                    summary=parameters["summary"],
                    start_time=start_dt,
                    end_time=end_dt,
                    calendar_id=calendar_id,
                    description=parameters.get("description"),
                    location=parameters.get("location"),
                    attendees=parameters.get("attendees"),
                    recurrence=parameters.get("recurrence"),
                )

                return SpokeResponse(
                    success=True,
                    data=result,
                    metadata={"calendar_id": calendar_id},
                )

            finally:
                await service.disconnect()

        except GoogleCalendarAuthenticationError as e:
            return SpokeResponse(success=False, error=f"Authentication error: {str(e)}")
        except GoogleCalendarAPIError as e:
            return SpokeResponse(
                success=False, error=f"Google Calendar API error: {str(e)}"
            )
        except GoogleCalendarServiceError as e:
            return SpokeResponse(
                success=False, error=f"Calendar service error: {str(e)}"
            )
        except Exception as e:
            return SpokeResponse(success=False, error=f"Unexpected error: {str(e)}")

    async def action_update_calendar_event(
        self, parameters: Dict[str, Any]
    ) -> SpokeResponse:
        """カレンダーイベント更新アクション"""
        try:
            calendar_id = parameters.get("calendar_id", "primary")
            event_id = parameters["event_id"]
            start_dt = datetime.fromisoformat(parameters["start_time"])
            end_dt = datetime.fromisoformat(parameters["end_time"])

            # Google Calendar APIサービスを取得
            service = await self._get_calendar_service()

            try:
                # イベントを更新
                result = await service.update_event(
                    event_id=event_id,
                    summary=parameters["summary"],
                    start_time=start_dt,
                    end_time=end_dt,
                    calendar_id=calendar_id,
                    description=parameters.get("description"),
                    location=parameters.get("location"),
                    attendees=parameters.get("attendees"),
                    recurrence=parameters.get("recurrence"),
                )

                return SpokeResponse(
                    success=True,
                    data=result,
                    metadata={"calendar_id": calendar_id},
                )

            finally:
                await service.disconnect()

        except GoogleCalendarAuthenticationError as e:
            return SpokeResponse(success=False, error=f"Authentication error: {str(e)}")
        except GoogleCalendarAPIError as e:
            return SpokeResponse(
                success=False, error=f"Google Calendar API error: {str(e)}"
            )
        except GoogleCalendarServiceError as e:
            return SpokeResponse(
                success=False, error=f"Calendar service error: {str(e)}"
            )
        except Exception as e:
            return SpokeResponse(success=False, error=f"Unexpected error: {str(e)}")

    async def action_delete_calendar_event(
        self, parameters: Dict[str, Any]
    ) -> SpokeResponse:
        """カレンダーイベント削除アクション"""
        try:
            calendar_id = parameters.get("calendar_id", "primary")
            event_id = parameters["event_id"]

            # Google Calendar APIサービスを取得
            service = await self._get_calendar_service()

            try:
                # イベントを削除
                result = await service.delete_event(
                    event_id=event_id,
                    calendar_id=calendar_id,
                )

                return SpokeResponse(
                    success=True,
                    data=result,
                    metadata={"calendar_id": calendar_id},
                )

            finally:
                await service.disconnect()

        except GoogleCalendarAuthenticationError as e:
            return SpokeResponse(success=False, error=f"Authentication error: {str(e)}")
        except GoogleCalendarAPIError as e:
            if "Event not found" in str(e):
                return SpokeResponse(
                    success=False,
                    error="Event not found",
                    metadata={"status_code": 404},
                )
            return SpokeResponse(
                success=False, error=f"Google Calendar API error: {str(e)}"
            )
        except GoogleCalendarServiceError as e:
            return SpokeResponse(
                success=False, error=f"Calendar service error: {str(e)}"
            )
        except Exception as e:
            return SpokeResponse(success=False, error=f"Unexpected error: {str(e)}")

    async def action_list_calendars(self, _: Dict[str, Any]) -> SpokeResponse:
        """カレンダーリスト取得アクション"""
        try:
            # Google Calendar APIサービスを取得
            service = await self._get_calendar_service()

            try:
                # カレンダーリストを取得
                calendar_list = await service.list_calendars()

                return SpokeResponse(
                    success=True,
                    data=calendar_list,
                    metadata={"total_calendars": len(calendar_list)},
                )

            finally:
                await service.disconnect()

        except GoogleCalendarAuthenticationError as e:
            return SpokeResponse(success=False, error=f"Authentication error: {str(e)}")
        except GoogleCalendarAPIError as e:
            return SpokeResponse(
                success=False, error=f"Google Calendar API error: {str(e)}"
            )
        except GoogleCalendarServiceError as e:
            return SpokeResponse(
                success=False, error=f"Calendar service error: {str(e)}"
            )
        except Exception as e:
            return SpokeResponse(success=False, error=f"Unexpected error: {str(e)}")
