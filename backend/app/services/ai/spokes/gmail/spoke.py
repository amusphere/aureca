import logging
from typing import Any, Dict

from app.services.ai.models import SpokeResponse
from app.services.ai.spokes.spoke_interface import BaseSpoke
from app.services.gmail_integrated import (
    GmailAPIError,
    GmailAuthenticationError,
    get_authenticated_gmail_service,
)


class GmailSpoke(BaseSpoke):
    """Gmail operations spoke for email management"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        # Maximum allowed results for email queries
        self.MAX_EMAIL_RESULTS = 100
        self.DEFAULT_EMAIL_RESULTS = 10

    def _validate_user_authentication(self) -> bool:
        """Validate that user is authenticated and available"""
        if not self.current_user:
            self.logger.debug(f"current_user is None or empty: {self.current_user}")
            return False
        if not self.session:
            self.logger.debug(f"session is None or empty: {self.session}")
            return False
        self.logger.debug(f"Authentication OK - user_id: {self.current_user.id}")
        return True

    def _create_authentication_error_response(self) -> SpokeResponse:
        """Create standard authentication error response"""
        error_details = {
            "current_user_available": self.current_user is not None,
            "session_available": self.session is not None,
        }
        if self.current_user:
            error_details["user_id"] = self.current_user.id

        return SpokeResponse(
            success=False,
            error="User authentication required. Please ensure you are logged in.",
            data={"error_type": "authentication_required", "debug": error_details},
        )

    def _validate_max_results(self, max_results: int) -> int:
        """Validate and normalize max_results parameter"""
        if max_results is None:
            return self.DEFAULT_EMAIL_RESULTS
        return min(max_results, self.MAX_EMAIL_RESULTS)

    def _handle_gmail_exceptions(self, action_name: str) -> SpokeResponse:
        """Common exception handler for Gmail operations"""

        def decorator(func):
            async def wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except GmailAuthenticationError as e:
                    self.logger.error(
                        f"Gmail authentication error in {action_name}: {str(e)}"
                    )
                    return SpokeResponse(
                        success=False,
                        error=f"Gmail authentication error: {str(e)}",
                        data={"error_type": "authentication_error"},
                    )
                except GmailAPIError as e:
                    self.logger.error(f"Gmail API error in {action_name}: {str(e)}")
                    return SpokeResponse(
                        success=False,
                        error=f"Gmail API error: {str(e)}",
                        data={"error_type": "api_error"},
                    )
                except Exception as e:
                    self.logger.error(f"Unexpected error in {action_name}: {str(e)}")
                    return SpokeResponse(
                        success=False,
                        error=f"Failed to {action_name}: {str(e)}",
                        data={"error_type": "general_error"},
                    )

            return wrapper

        return decorator

    def _create_success_response(
        self, data: Dict[str, Any], message: str
    ) -> SpokeResponse:
        """Create a standardized success response"""
        return SpokeResponse(
            success=True,
            data=data,
            metadata={"message": message},
        )

    def _create_parameter_error_response(self, message: str) -> SpokeResponse:
        """Create a standardized parameter error response"""
        return SpokeResponse(
            success=False,
            error=message,
            data={"error_type": "parameter_error"},
        )

    def _validate_email_id(self, parameters: Dict[str, Any]) -> str:
        """Validate email ID parameter"""
        email_id = parameters.get("email_id")
        if not email_id:
            raise ValueError("Email ID is required")
        return email_id

    async def _execute_email_action(
        self, email_id: str, action_method_name: str, success_message: str
    ) -> Dict[str, Any]:
        """Execute an email action (mark as read/unread) and return result"""
        async with get_authenticated_gmail_service(
            self.current_user, self.session
        ) as gmail_service:
            method = getattr(gmail_service, action_method_name)
            result = await method(email_id)

        return {"result": result}

    def _validate_email_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate email parameters and return validated data"""
        to = parameters.get("to")
        subject = parameters.get("subject")
        body = parameters.get("body")

        if not all([to, subject, body]):
            missing_params = [
                param
                for param, value in [("to", to), ("subject", subject), ("body", body)]
                if not value
            ]
            raise ValueError(
                f"Required parameters are missing: {', '.join(missing_params)}"
            )

        return {
            "to": to,
            "subject": subject,
            "body": body,
            "cc": parameters.get("cc"),
            "bcc": parameters.get("bcc"),
        }

    async def _execute_gmail_query(
        self, query: str, max_results: int
    ) -> Dict[str, Any]:
        """Execute Gmail query and return results with metadata"""
        async with get_authenticated_gmail_service(
            self.current_user, self.session
        ) as gmail_service:
            emails = await gmail_service.get_emails(
                query=query, max_results=max_results
            )

        return {
            "emails": emails,
            "count": len(emails),
            "query": query,
        }

    # =================
    # Action functions
    # =================

    async def action_get_emails(self, parameters: Dict[str, Any]) -> SpokeResponse:
        """Get email list action"""
        # Validate user authentication
        if not self._validate_user_authentication():
            return self._create_authentication_error_response()

        # Extract and validate parameters
        query = parameters.get("query", "")
        max_results = self._validate_max_results(
            parameters.get("max_results", self.DEFAULT_EMAIL_RESULTS)
        )

        try:
            # Execute Gmail query
            result_data = await self._execute_gmail_query(query, max_results)

            return self._create_success_response(
                data={"emails": result_data["emails"], "count": result_data["count"]},
                message=f"Successfully retrieved {result_data['count']} emails",
            )

        except GmailAuthenticationError as e:
            self.logger.error(f"Gmail authentication error in get_emails: {str(e)}")
            return SpokeResponse(
                success=False,
                error=f"Gmail authentication error: {str(e)}",
                data={"error_type": "authentication_error"},
            )
        except GmailAPIError as e:
            self.logger.error(f"Gmail API error in get_emails: {str(e)}")
            return SpokeResponse(
                success=False,
                error=f"Gmail API error: {str(e)}",
                data={"error_type": "api_error"},
            )
        except Exception as e:
            self.logger.error(f"Unexpected error in get_emails: {str(e)}")
            return SpokeResponse(
                success=False,
                error=f"Failed to retrieve emails: {str(e)}",
                data={"error_type": "general_error"},
            )

    async def action_get_email_content(
        self, parameters: Dict[str, Any]
    ) -> SpokeResponse:
        """Get specific email content action"""
        # Validate user authentication
        if not self._validate_user_authentication():
            return self._create_authentication_error_response()

        # Validate required parameters
        email_id = parameters.get("email_id")
        if not email_id:
            return self._create_parameter_error_response("Email ID is required")

        try:
            # Get Gmail service and retrieve email content
            async with get_authenticated_gmail_service(
                self.current_user, self.session
            ) as gmail_service:
                email_content = await gmail_service.get_email_content(email_id)

            return self._create_success_response(
                data={"email": email_content},
                message="Successfully retrieved email content",
            )

        except GmailAuthenticationError as e:
            self.logger.error(
                f"Gmail authentication error in get_email_content: {str(e)}"
            )
            return SpokeResponse(
                success=False,
                error=f"Gmail authentication error: {str(e)}",
                data={"error_type": "authentication_error"},
            )
        except GmailAPIError as e:
            self.logger.error(f"Gmail API error in get_email_content: {str(e)}")
            return SpokeResponse(
                success=False,
                error=f"Gmail API error: {str(e)}",
                data={"error_type": "api_error"},
            )
        except Exception as e:
            self.logger.error(f"Unexpected error in get_email_content: {str(e)}")
            return SpokeResponse(
                success=False,
                error=f"Failed to retrieve email content: {str(e)}",
                data={"error_type": "general_error"},
            )

    async def action_send_email(self, parameters: Dict[str, Any]) -> SpokeResponse:
        """Send email action"""
        # Validate user authentication
        if not self._validate_user_authentication():
            return self._create_authentication_error_response()

        try:
            # Validate email parameters
            email_params = self._validate_email_parameters(parameters)

            # Get Gmail service and send email
            async with get_authenticated_gmail_service(
                self.current_user, self.session
            ) as gmail_service:
                result = await gmail_service.send_email(
                    to=email_params["to"],
                    subject=email_params["subject"],
                    body=email_params["body"],
                    cc=email_params["cc"],
                    bcc=email_params["bcc"],
                )

            return self._create_success_response(
                data={"result": result}, message="Email sent successfully"
            )

        except ValueError as e:
            return self._create_parameter_error_response(str(e))
        except GmailAuthenticationError as e:
            self.logger.error(f"Gmail authentication error in send_email: {str(e)}")
            return SpokeResponse(
                success=False,
                error=f"Gmail authentication error: {str(e)}",
                data={"error_type": "authentication_error"},
            )
        except GmailAPIError as e:
            self.logger.error(f"Gmail API error in send_email: {str(e)}")
            return SpokeResponse(
                success=False,
                error=f"Gmail API error: {str(e)}",
                data={"error_type": "api_error"},
            )
        except Exception as e:
            self.logger.error(f"Unexpected error in send_email: {str(e)}")
            return SpokeResponse(
                success=False,
                error=f"Failed to send email: {str(e)}",
                data={"error_type": "general_error"},
            )

    async def action_create_draft(self, parameters: Dict[str, Any]) -> SpokeResponse:
        """Create email draft action"""
        # Validate user authentication
        if not self._validate_user_authentication():
            return self._create_authentication_error_response()

        try:
            # Validate email parameters
            email_params = self._validate_email_parameters(parameters)

            # Get Gmail service and create draft
            async with get_authenticated_gmail_service(
                self.current_user, self.session
            ) as gmail_service:
                result = await gmail_service.create_draft(
                    to=email_params["to"],
                    subject=email_params["subject"],
                    body=email_params["body"],
                    cc=email_params["cc"],
                    bcc=email_params["bcc"],
                )

            return self._create_success_response(
                data={"result": result}, message="Draft created successfully"
            )

        except ValueError as e:
            return self._create_parameter_error_response(str(e))
        except GmailAuthenticationError as e:
            self.logger.error(f"Gmail authentication error in create_draft: {str(e)}")
            return SpokeResponse(
                success=False,
                error=f"Gmail authentication error: {str(e)}",
                data={"error_type": "authentication_error"},
            )
        except GmailAPIError as e:
            self.logger.error(f"Gmail API error in create_draft: {str(e)}")
            return SpokeResponse(
                success=False,
                error=f"Gmail API error: {str(e)}",
                data={"error_type": "api_error"},
            )
        except Exception as e:
            self.logger.error(f"Unexpected error in create_draft: {str(e)}")
            return SpokeResponse(
                success=False,
                error=f"Failed to create draft: {str(e)}",
                data={"error_type": "general_error"},
            )

    async def action_mark_as_read(self, parameters: Dict[str, Any]) -> SpokeResponse:
        """Mark email as read action"""
        # Validate user authentication
        if not self._validate_user_authentication():
            return self._create_authentication_error_response()

        try:
            # Validate email ID
            email_id = self._validate_email_id(parameters)

            # Execute mark as read action
            result_data = await self._execute_email_action(
                email_id, "mark_as_read", "Email marked as read successfully"
            )

            return self._create_success_response(
                data=result_data, message="Email marked as read successfully"
            )

        except ValueError as e:
            return self._create_parameter_error_response(str(e))
        except GmailAuthenticationError as e:
            self.logger.error(f"Gmail authentication error in mark_as_read: {str(e)}")
            return SpokeResponse(
                success=False,
                error=f"Gmail authentication error: {str(e)}",
                data={"error_type": "authentication_error"},
            )
        except GmailAPIError as e:
            self.logger.error(f"Gmail API error in mark_as_read: {str(e)}")
            return SpokeResponse(
                success=False,
                error=f"Gmail API error: {str(e)}",
                data={"error_type": "api_error"},
            )
        except Exception as e:
            self.logger.error(f"Unexpected error in mark_as_read: {str(e)}")
            return SpokeResponse(
                success=False,
                error=f"Failed to mark email as read: {str(e)}",
                data={"error_type": "general_error"},
            )

    async def action_mark_as_unread(self, parameters: Dict[str, Any]) -> SpokeResponse:
        """Mark email as unread action"""
        # Validate user authentication
        if not self._validate_user_authentication():
            return self._create_authentication_error_response()

        try:
            # Validate email ID
            email_id = self._validate_email_id(parameters)

            # Execute mark as unread action
            result_data = await self._execute_email_action(
                email_id, "mark_as_unread", "Email marked as unread successfully"
            )

            return self._create_success_response(
                data=result_data, message="Email marked as unread successfully"
            )

        except ValueError as e:
            return self._create_parameter_error_response(str(e))
        except GmailAuthenticationError as e:
            self.logger.error(f"Gmail authentication error in mark_as_unread: {str(e)}")
            return SpokeResponse(
                success=False,
                error=f"Gmail authentication error: {str(e)}",
                data={"error_type": "authentication_error"},
            )
        except GmailAPIError as e:
            self.logger.error(f"Gmail API error in mark_as_unread: {str(e)}")
            return SpokeResponse(
                success=False,
                error=f"Gmail API error: {str(e)}",
                data={"error_type": "api_error"},
            )
        except Exception as e:
            self.logger.error(f"Unexpected error in mark_as_unread: {str(e)}")
            return SpokeResponse(
                success=False,
                error=f"Failed to mark email as unread: {str(e)}",
                data={"error_type": "general_error"},
            )

    def _build_search_query(self, parameters: Dict[str, Any]) -> str:
        """Build Gmail search query from parameters"""
        gmail_query_parts = []

        # Add search query if provided
        search_query = parameters.get("search_query", "")
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

        return " ".join(gmail_query_parts)

    async def action_search_emails(self, parameters: Dict[str, Any]) -> SpokeResponse:
        """Search emails with specific criteria action"""
        # Validate user authentication
        if not self._validate_user_authentication():
            return self._create_authentication_error_response()

        # Extract and validate parameters
        max_results = self._validate_max_results(
            parameters.get("max_results", self.DEFAULT_EMAIL_RESULTS)
        )
        gmail_query = self._build_search_query(parameters)

        try:
            # Execute Gmail search query
            result_data = await self._execute_gmail_query(gmail_query, max_results)

            return self._create_success_response(
                data={
                    "emails": result_data["emails"],
                    "count": result_data["count"],
                    "search_query": gmail_query,
                },
                message=f"Successfully found {result_data['count']} emails matching criteria",
            )

        except GmailAuthenticationError as e:
            self.logger.error(f"Gmail authentication error in search_emails: {str(e)}")
            return SpokeResponse(
                success=False,
                error=f"Gmail authentication error: {str(e)}",
                data={"error_type": "authentication_error"},
            )
        except GmailAPIError as e:
            self.logger.error(f"Gmail API error in search_emails: {str(e)}")
            return SpokeResponse(
                success=False,
                error=f"Gmail API error: {str(e)}",
                data={"error_type": "api_error"},
            )
        except Exception as e:
            self.logger.error(f"Unexpected error in search_emails: {str(e)}")
            return SpokeResponse(
                success=False,
                error=f"Failed to search emails: {str(e)}",
                data={"error_type": "general_error"},
            )

    async def action_get_unread_emails(
        self, parameters: Dict[str, Any]
    ) -> SpokeResponse:
        """Get unread emails action"""
        # Validate user authentication
        if not self._validate_user_authentication():
            return self._create_authentication_error_response()

        # Extract and validate parameters
        max_results = self._validate_max_results(
            parameters.get("max_results", self.DEFAULT_EMAIL_RESULTS)
        )
        gmail_query = "is:unread"

        try:
            # Execute Gmail query for unread emails
            result_data = await self._execute_gmail_query(gmail_query, max_results)

            return self._create_success_response(
                data={"emails": result_data["emails"], "count": result_data["count"]},
                message=f"Successfully retrieved {result_data['count']} unread emails",
            )

        except GmailAuthenticationError as e:
            self.logger.error(
                f"Gmail authentication error in get_unread_emails: {str(e)}"
            )
            return SpokeResponse(
                success=False,
                error=f"Gmail authentication error: {str(e)}",
                data={"error_type": "authentication_error"},
            )
        except GmailAPIError as e:
            self.logger.error(f"Gmail API error in get_unread_emails: {str(e)}")
            return SpokeResponse(
                success=False,
                error=f"Gmail API error: {str(e)}",
                data={"error_type": "api_error"},
            )
        except Exception as e:
            self.logger.error(f"Unexpected error in get_unread_emails: {str(e)}")
            return SpokeResponse(
                success=False,
                error=f"Failed to retrieve unread emails: {str(e)}",
                data={"error_type": "general_error"},
            )

    async def action_get_new_emails(self, parameters: Dict[str, Any]) -> SpokeResponse:
        """Get new emails (unread and not archived) action"""
        # Validate user authentication
        if not self._validate_user_authentication():
            return self._create_authentication_error_response()

        # Extract and validate parameters
        max_results = self._validate_max_results(
            parameters.get("max_results", self.DEFAULT_EMAIL_RESULTS)
        )
        gmail_query = "is:unread -is:archived"

        try:
            # Execute Gmail query for new emails
            result_data = await self._execute_gmail_query(gmail_query, max_results)

            return self._create_success_response(
                data={"emails": result_data["emails"], "count": result_data["count"]},
                message=f"Successfully retrieved {result_data['count']} new emails",
            )

        except GmailAuthenticationError as e:
            self.logger.error(f"Gmail authentication error in get_new_emails: {str(e)}")
            return SpokeResponse(
                success=False,
                error=f"Gmail authentication error: {str(e)}",
                data={"error_type": "authentication_error"},
            )
        except GmailAPIError as e:
            self.logger.error(f"Gmail API error in get_new_emails: {str(e)}")
            return SpokeResponse(
                success=False,
                error=f"Gmail API error: {str(e)}",
                data={"error_type": "api_error"},
            )
        except Exception as e:
            self.logger.error(f"Unexpected error in get_new_emails: {str(e)}")
            return SpokeResponse(
                success=False,
                error=f"Failed to retrieve new emails: {str(e)}",
                data={"error_type": "general_error"},
            )
