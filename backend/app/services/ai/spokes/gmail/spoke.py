from typing import Any, Dict

from app.services.ai.models import SpokeResponse
from app.services.ai.spokes.spoke_interface import BaseSpoke
from app.services.gmail_integrated import (
    GmailAPIError,
    GmailAuthenticationError,
    get_authenticated_gmail_service,
)


class GmailSpoke(BaseSpoke):
    """Gmail operations spoke"""

    def _validate_user_authentication(self) -> bool:
        """Validate that user is authenticated and available"""
        if not self.current_user:
            print(f"DEBUG: current_user is None or empty: {self.current_user}")
            return False
        if not self.session:
            print(f"DEBUG: session is None or empty: {self.session}")
            return False
        print(
            f"DEBUG: Authentication OK - user_id: {self.current_user.id if self.current_user else 'None'}"
        )
        return True

    def _get_authentication_error_response(self) -> SpokeResponse:
        """Return standard authentication error response"""
        error_details = {
            "current_user_available": self.current_user is not None,
            "session_available": self.session is not None,
        }
        if self.current_user:
            error_details["user_id"] = self.current_user.id

        return SpokeResponse(
            success=False,
            message="User authentication required. Please ensure you are logged in.",
            data={"error_type": "authentication_required", "debug": error_details},
        )

    # =================
    # Action functions
    # =================

    async def action_get_emails(self, parameters: Dict[str, Any]) -> SpokeResponse:
        """Get email list action"""
        try:
            # Validate user authentication
            if not self._validate_user_authentication():
                return self._get_authentication_error_response()

            # Extract parameters
            query = parameters.get("query", "")
            max_results = parameters.get("max_results", 10)

            # Validate max_results
            if max_results > 100:
                max_results = 100

            # Get Gmail service and retrieve emails
            async with get_authenticated_gmail_service(
                self.current_user, self.session
            ) as gmail_service:
                emails = await gmail_service.get_emails(
                    query=query, max_results=max_results
                )

            return SpokeResponse(
                success=True,
                message=f"Successfully retrieved {len(emails)} emails",
                data={"emails": emails, "count": len(emails)},
            )

        except GmailAuthenticationError as e:
            return SpokeResponse(
                success=False,
                message=f"Gmail authentication error: {str(e)}",
                data={"error_type": "authentication_error"},
            )
        except GmailAPIError as e:
            return SpokeResponse(
                success=False,
                message=f"Gmail API error: {str(e)}",
                data={"error_type": "api_error"},
            )
        except Exception as e:
            return SpokeResponse(
                success=False,
                message=f"Failed to retrieve emails: {str(e)}",
                data={"error_type": "general_error"},
            )

    async def action_get_email_content(
        self, parameters: Dict[str, Any]
    ) -> SpokeResponse:
        """Get specific email content action"""
        try:
            # Validate user authentication
            if not self._validate_user_authentication():
                return self._get_authentication_error_response()

            # Extract parameters
            email_id = parameters.get("email_id")
            if not email_id:
                return SpokeResponse(
                    success=False,
                    message="Email ID is required",
                    data={"error_type": "parameter_error"},
                )

            # Get Gmail service and retrieve email content
            async with get_authenticated_gmail_service(
                self.current_user, self.session
            ) as gmail_service:
                email_content = await gmail_service.get_email_content(email_id)

            return SpokeResponse(
                success=True,
                message="Successfully retrieved email content",
                data={"email": email_content},
            )

        except GmailAuthenticationError as e:
            return SpokeResponse(
                success=False,
                message=f"Gmail authentication error: {str(e)}",
                data={"error_type": "authentication_error"},
            )
        except GmailAPIError as e:
            return SpokeResponse(
                success=False,
                message=f"Gmail API error: {str(e)}",
                data={"error_type": "api_error"},
            )
        except Exception as e:
            return SpokeResponse(
                success=False,
                message=f"Failed to retrieve email content: {str(e)}",
                data={"error_type": "general_error"},
            )

    async def action_send_email(self, parameters: Dict[str, Any]) -> SpokeResponse:
        """Send email action"""
        try:
            # Validate user authentication
            if not self._validate_user_authentication():
                return self._get_authentication_error_response()

            # Extract required parameters
            to = parameters.get("to")
            subject = parameters.get("subject")
            body = parameters.get("body")

            if not all([to, subject, body]):
                return SpokeResponse(
                    success=False,
                    message="Required parameters are missing: to, subject, body",
                    data={"error_type": "parameter_error"},
                )

            # Extract optional parameters
            cc = parameters.get("cc")
            bcc = parameters.get("bcc")

            # Get Gmail service and send email
            async with get_authenticated_gmail_service(
                self.current_user, self.session
            ) as gmail_service:
                result = await gmail_service.send_email(
                    to=to, subject=subject, body=body, cc=cc, bcc=bcc
                )

            return SpokeResponse(
                success=True,
                message="Email sent successfully",
                data={"result": result},
            )

        except GmailAuthenticationError as e:
            return SpokeResponse(
                success=False,
                message=f"Gmail authentication error: {str(e)}",
                data={"error_type": "authentication_error"},
            )
        except GmailAPIError as e:
            return SpokeResponse(
                success=False,
                message=f"Gmail API error: {str(e)}",
                data={"error_type": "api_error"},
            )
        except Exception as e:
            return SpokeResponse(
                success=False,
                message=f"Failed to send email: {str(e)}",
                data={"error_type": "general_error"},
            )

    async def action_create_draft(self, parameters: Dict[str, Any]) -> SpokeResponse:
        """Create email draft action"""
        try:
            # Validate user authentication
            if not self._validate_user_authentication():
                return self._get_authentication_error_response()

            # Extract required parameters
            to = parameters.get("to")
            subject = parameters.get("subject")
            body = parameters.get("body")

            if not all([to, subject, body]):
                return SpokeResponse(
                    success=False,
                    message="Required parameters are missing: to, subject, body",
                    data={"error_type": "parameter_error"},
                )

            # Extract optional parameters
            cc = parameters.get("cc")
            bcc = parameters.get("bcc")

            # Get Gmail service and create draft
            async with get_authenticated_gmail_service(
                self.current_user, self.session
            ) as gmail_service:
                result = await gmail_service.create_draft(
                    to=to, subject=subject, body=body, cc=cc, bcc=bcc
                )

            return SpokeResponse(
                success=True,
                message="Draft created successfully",
                data={"result": result},
            )

        except GmailAuthenticationError as e:
            return SpokeResponse(
                success=False,
                message=f"Gmail authentication error: {str(e)}",
                data={"error_type": "authentication_error"},
            )
        except GmailAPIError as e:
            return SpokeResponse(
                success=False,
                message=f"Gmail API error: {str(e)}",
                data={"error_type": "api_error"},
            )
        except Exception as e:
            return SpokeResponse(
                success=False,
                message=f"Failed to create draft: {str(e)}",
                data={"error_type": "general_error"},
            )

    async def action_mark_as_read(self, parameters: Dict[str, Any]) -> SpokeResponse:
        """Mark email as read action"""
        try:
            # Validate user authentication
            if not self._validate_user_authentication():
                return self._get_authentication_error_response()

            # Extract parameters
            email_id = parameters.get("email_id")
            if not email_id:
                return SpokeResponse(
                    success=False,
                    message="Email ID is required",
                    data={"error_type": "parameter_error"},
                )

            # Get Gmail service and mark as read
            async with get_authenticated_gmail_service(
                self.current_user, self.session
            ) as gmail_service:
                result = await gmail_service.mark_as_read(email_id)

            return SpokeResponse(
                success=True,
                message="Email marked as read successfully",
                data={"result": result},
            )

        except GmailAuthenticationError as e:
            return SpokeResponse(
                success=False,
                message=f"Gmail authentication error: {str(e)}",
                data={"error_type": "authentication_error"},
            )
        except GmailAPIError as e:
            return SpokeResponse(
                success=False,
                message=f"Gmail API error: {str(e)}",
                data={"error_type": "api_error"},
            )
        except Exception as e:
            return SpokeResponse(
                success=False,
                message=f"Failed to mark email as read: {str(e)}",
                data={"error_type": "general_error"},
            )

    async def action_mark_as_unread(self, parameters: Dict[str, Any]) -> SpokeResponse:
        """Mark email as unread action"""
        try:
            # Validate user authentication
            if not self._validate_user_authentication():
                return self._get_authentication_error_response()

            # Extract parameters
            email_id = parameters.get("email_id")
            if not email_id:
                return SpokeResponse(
                    success=False,
                    message="Email ID is required",
                    data={"error_type": "parameter_error"},
                )

            # Get Gmail service and mark as unread
            async with get_authenticated_gmail_service(
                self.current_user, self.session
            ) as gmail_service:
                result = await gmail_service.mark_as_unread(email_id)

            return SpokeResponse(
                success=True,
                message="Email marked as unread successfully",
                data={"result": result},
            )

        except GmailAuthenticationError as e:
            return SpokeResponse(
                success=False,
                message=f"Gmail authentication error: {str(e)}",
                data={"error_type": "authentication_error"},
            )
        except GmailAPIError as e:
            return SpokeResponse(
                success=False,
                message=f"Gmail API error: {str(e)}",
                data={"error_type": "api_error"},
            )
        except Exception as e:
            return SpokeResponse(
                success=False,
                message=f"Failed to mark email as unread: {str(e)}",
                data={"error_type": "general_error"},
            )

    async def action_search_emails(self, parameters: Dict[str, Any]) -> SpokeResponse:
        """Search emails with specific criteria action"""
        try:
            # Validate user authentication
            if not self._validate_user_authentication():
                return self._get_authentication_error_response()

            # Extract parameters
            search_query = parameters.get("search_query", "")
            max_results = parameters.get("max_results", 10)

            # Build Gmail search query
            gmail_query_parts = []

            # Add search query if provided
            if search_query:
                gmail_query_parts.append(search_query)

            # Add from filter
            if parameters.get("from_email"):
                gmail_query_parts.append(f"from:{parameters['from_email']}")

            # Add to filter
            if parameters.get("to_email"):
                gmail_query_parts.append(f"to:{parameters['to_email']}")

            # Add subject filter
            if parameters.get("subject"):
                gmail_query_parts.append(f"subject:{parameters['subject']}")

            # Add has attachment filter
            if parameters.get("has_attachment"):
                gmail_query_parts.append("has:attachment")

            # Add unread filter
            if parameters.get("is_unread"):
                gmail_query_parts.append("is:unread")

            # Add date filters
            if parameters.get("after_date"):
                gmail_query_parts.append(f"after:{parameters['after_date']}")

            if parameters.get("before_date"):
                gmail_query_parts.append(f"before:{parameters['before_date']}")

            gmail_query = " ".join(gmail_query_parts)

            # Validate max_results
            if max_results > 100:
                max_results = 100

            # Get Gmail service and search emails
            async with get_authenticated_gmail_service(
                self.current_user, self.session
            ) as gmail_service:
                emails = await gmail_service.get_emails(
                    query=gmail_query, max_results=max_results
                )

            return SpokeResponse(
                success=True,
                message=f"Successfully found {len(emails)} emails matching criteria",
                data={
                    "emails": emails,
                    "count": len(emails),
                    "search_query": gmail_query,
                },
            )

        except GmailAuthenticationError as e:
            return SpokeResponse(
                success=False,
                message=f"Gmail authentication error: {str(e)}",
                data={"error_type": "authentication_error"},
            )
        except GmailAPIError as e:
            return SpokeResponse(
                success=False,
                message=f"Gmail API error: {str(e)}",
                data={"error_type": "api_error"},
            )
        except Exception as e:
            return SpokeResponse(
                success=False,
                message=f"Failed to search emails: {str(e)}",
                data={"error_type": "general_error"},
            )
