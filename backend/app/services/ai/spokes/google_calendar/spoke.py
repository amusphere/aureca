from datetime import datetime
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

from app.schema import User
from app.services.ai.models import SpokeResponse
from app.services.ai.spokes.spoke_interface import BaseSpoke
from app.services.google_oauth import GoogleOauthService
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlmodel import Session


class GoogleCalendarSpoke(BaseSpoke):
    """Google Calendar操作を提供するスポーク"""

    def __init__(
        self,
        session: Optional[Session] = None,
        current_user: Optional[User] = None,
    ):
        super().__init__(session=session, current_user=current_user)
        try:
            self.oauth_service = GoogleOauthService(session)
        except ValueError as e:
            # 環境変数が設定されていない場合の処理
            self.oauth_service = None
            self._initialization_error = str(e)

    def _get_calendar_service(self, user_id: int):
        """Google Calendar APIサービスを取得"""
        if self.oauth_service is None:
            raise ValueError(
                f"Google OAuth Service initialization failed: {getattr(self, '_initialization_error', 'Unknown error')}"
            )

        credentials = self.oauth_service.get_credentials(user_id)
        if not credentials:
            raise ValueError("Google認証情報が見つかりません")
        return build("calendar", "v3", credentials=credentials)

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

            # タイムゾーンが設定されていない場合は日本時間として扱う
            jst = ZoneInfo("Asia/Tokyo")
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=jst)
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=jst)

            # Google Calendar APIサービスを取得
            service = self._get_calendar_service(self.current_user.id)

            # RFC3339形式でタイムスタンプを作成
            time_min = start_date.isoformat()
            time_max = end_date.isoformat()

            # イベントを取得
            events_result = (
                service.events()
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

            # CalendarEventモデルに変換
            calendar_events = []
            for event in events:
                start = event["start"].get("dateTime", event["start"].get("date"))
                end = event["end"].get("dateTime", event["end"].get("date"))

                # 日付のみの場合の処理
                if "T" not in start:
                    start += "T00:00:00"
                if "T" not in end:
                    end += "T23:59:59"

                # Z suffixを適切に処理
                if start.endswith("Z"):
                    start = start[:-1] + "+00:00"
                if end.endswith("Z"):
                    end = end[:-1] + "+00:00"

                attendees = []
                if "attendees" in event:
                    attendees = [
                        attendee.get("email", "") for attendee in event["attendees"]
                    ]

                calendar_event = {
                    "id": event.get("id"),
                    "summary": event.get("summary", ""),
                    "description": event.get("description"),
                    "start_time": datetime.fromisoformat(start),
                    "end_time": datetime.fromisoformat(end),
                    "location": event.get("location"),
                    "attendees": attendees if attendees else None,
                    "recurrence": event.get("recurrence"),
                }
                calendar_events.append(calendar_event)

            return SpokeResponse(
                success=True,
                data=calendar_events,
                metadata={
                    "total_events": len(calendar_events),
                    "period": f"{start_date.date()} to {end_date.date()}",
                },
            )

        except HttpError as e:
            # より詳細なエラー情報をログに出力
            error_details = {
                "status_code": e.resp.status,
                "reason": e.reason,
                "content": e.content.decode() if e.content else None,
                "parameters": parameters,
            }

            return SpokeResponse(
                success=False,
                error=f"Google Calendar API error: {e.reason}",
                metadata={"status_code": e.resp.status, "details": error_details},
            )
        except ValueError as e:
            return SpokeResponse(success=False, error=f"Authentication error: {str(e)}")
        except Exception as e:
            return SpokeResponse(success=False, error=f"Unexpected error: {str(e)}")

    async def action_create_calendar_event(
        self, parameters: Dict[str, Any]
    ) -> SpokeResponse:
        """カレンダーイベント作成アクション"""
        try:
            service = self._get_calendar_service(self.current_user.id)
            calendar_id = parameters.get("calendar_id", "primary")

            # イベントデータを構築
            start_dt = datetime.fromisoformat(parameters["start_time"])
            end_dt = datetime.fromisoformat(parameters["end_time"])

            # タイムゾーンが設定されていない場合は日本時間として扱う
            jst = ZoneInfo("Asia/Tokyo")
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=jst)
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=jst)

            event_body = {
                "summary": parameters["summary"],
                "start": {
                    "dateTime": start_dt.isoformat(),
                    "timeZone": "Asia/Tokyo",
                },
                "end": {
                    "dateTime": end_dt.isoformat(),
                    "timeZone": "Asia/Tokyo",
                },
            }

            if parameters.get("description"):
                event_body["description"] = parameters["description"]

            if parameters.get("location"):
                event_body["location"] = parameters["location"]

            if parameters.get("attendees"):
                event_body["attendees"] = [
                    {"email": email} for email in parameters["attendees"]
                ]

            if parameters.get("recurrence"):
                event_body["recurrence"] = parameters["recurrence"]

            # イベントを作成
            created_event = (
                service.events()
                .insert(calendarId=calendar_id, body=event_body)
                .execute()
            )

            return SpokeResponse(
                success=True,
                data={
                    "event_id": created_event.get("id"),
                    "html_link": created_event.get("htmlLink"),
                },
                metadata={"calendar_id": calendar_id},
            )

        except HttpError as e:
            return SpokeResponse(
                success=False,
                error=f"Google Calendar API error: {e.reason}",
                metadata={"status_code": e.resp.status},
            )
        except ValueError as e:
            return SpokeResponse(success=False, error=f"Authentication error: {str(e)}")
        except Exception as e:
            return SpokeResponse(success=False, error=f"Unexpected error: {str(e)}")

    async def action_update_calendar_event(
        self, parameters: Dict[str, Any]
    ) -> SpokeResponse:
        """カレンダーイベント更新アクション"""
        try:
            service = self._get_calendar_service(self.current_user.id)
            calendar_id = parameters.get("calendar_id", "primary")
            event_id = parameters["event_id"]

            # 既存のイベントを取得
            existing_event = (
                service.events().get(calendarId=calendar_id, eventId=event_id).execute()
            )

            # イベントデータを更新
            start_dt = datetime.fromisoformat(parameters["start_time"])
            end_dt = datetime.fromisoformat(parameters["end_time"])

            # タイムゾーンが設定されていない場合は日本時間として扱う
            jst = ZoneInfo("Asia/Tokyo")
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=jst)
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=jst)

            existing_event["summary"] = parameters["summary"]
            existing_event["start"] = {
                "dateTime": start_dt.isoformat(),
                "timeZone": "Asia/Tokyo",
            }
            existing_event["end"] = {
                "dateTime": end_dt.isoformat(),
                "timeZone": "Asia/Tokyo",
            }

            if parameters.get("description") is not None:
                existing_event["description"] = parameters["description"]

            if parameters.get("location") is not None:
                existing_event["location"] = parameters["location"]

            if parameters.get("attendees") is not None:
                existing_event["attendees"] = [
                    {"email": email} for email in parameters["attendees"]
                ]

            if parameters.get("recurrence") is not None:
                existing_event["recurrence"] = parameters["recurrence"]

            # イベントを更新
            updated_event = (
                service.events()
                .update(
                    calendarId=calendar_id,
                    eventId=event_id,
                    body=existing_event,
                )
                .execute()
            )

            return SpokeResponse(
                success=True,
                data={
                    "event_id": updated_event.get("id"),
                    "html_link": updated_event.get("htmlLink"),
                },
                metadata={"calendar_id": calendar_id},
            )

        except HttpError as e:
            return SpokeResponse(
                success=False,
                error=f"Google Calendar API error: {e.reason}",
                metadata={"status_code": e.resp.status},
            )
        except ValueError as e:
            return SpokeResponse(success=False, error=f"Authentication error: {str(e)}")
        except Exception as e:
            return SpokeResponse(success=False, error=f"Unexpected error: {str(e)}")

    async def action_delete_calendar_event(
        self, parameters: Dict[str, Any]
    ) -> SpokeResponse:
        """カレンダーイベント削除アクション"""
        try:
            service = self._get_calendar_service(self.current_user.id)
            calendar_id = parameters.get("calendar_id", "primary")
            event_id = parameters["event_id"]

            # イベントを削除
            service.events().delete(calendarId=calendar_id, eventId=event_id).execute()

            return SpokeResponse(
                success=True,
                data={"deleted_event_id": event_id},
                metadata={"calendar_id": calendar_id},
            )

        except HttpError as e:
            if e.resp.status == 404:
                return SpokeResponse(
                    success=False,
                    error="Event not found",
                    metadata={"status_code": 404},
                )
            return SpokeResponse(
                success=False,
                error=f"Google Calendar API error: {e.reason}",
                metadata={"status_code": e.resp.status},
            )
        except ValueError as e:
            return SpokeResponse(success=False, error=f"Authentication error: {str(e)}")
        except Exception as e:
            return SpokeResponse(success=False, error=f"Unexpected error: {str(e)}")

    async def action_list_calendars(self, _: Dict[str, Any]) -> SpokeResponse:
        """カレンダーリスト取得アクション（新しいアクションの例）"""
        try:
            service = self._get_calendar_service(self.current_user.id)

            # カレンダーリストを取得
            calendars_result = service.calendarList().list().execute()
            calendars = calendars_result.get("items", [])

            calendar_list = []
            for calendar in calendars:
                calendar_info = {
                    "id": calendar.get("id"),
                    "summary": calendar.get("summary"),
                    "description": calendar.get("description"),
                    "primary": calendar.get("primary", False),
                    "access_role": calendar.get("accessRole"),
                }
                calendar_list.append(calendar_info)

            return SpokeResponse(
                success=True,
                data=calendar_list,
                metadata={"total_calendars": len(calendar_list)},
            )

        except Exception as e:
            return SpokeResponse(
                success=False, error=f"Error listing calendars: {str(e)}"
            )
