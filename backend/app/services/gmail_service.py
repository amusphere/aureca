"""
Gmail Integration Service

Provides comprehensive Gmail API integration including:
- Authentication management
- Email operations (send, receive, search)
- Label management
- Draft operations

This service uses Google OAuth2 for authentication and provides
both context manager and direct access patterns.
"""

import base64
import email.mime.text
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from app.schema import User
from app.services.google_oauth import GoogleOauthService
from google.oauth2.credentials import Credentials as OAuth2Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlmodel import Session

# Configure module logger
logger = logging.getLogger(__name__)


# Gmail API Configuration
class GmailConfig:
    """Gmail API configuration constants and limits"""

    # OAuth Scopes required for Gmail operations
    SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly",  # Read emails
        "https://www.googleapis.com/auth/gmail.send",  # Send emails
        "https://www.googleapis.com/auth/gmail.modify",  # Modify labels
    ]

    # Email headers to retrieve for metadata
    METADATA_HEADERS = ["From", "To", "Subject", "Date", "Cc", "Bcc"]

    # Supported MIME types for email body extraction
    SUPPORTED_MIME_TYPES = ["text/plain", "text/html"]

    # API request limits
    MAX_RESULTS_LIMIT = 500  # Gmail API maximum
    DEFAULT_MAX_RESULTS = 10  # Default page size

    # OAuth configuration
    OAUTH_TOKEN_URI = "https://oauth2.googleapis.com/token"


class GmailServiceError(Exception):
    """Gmail service related error"""

    pass


class GmailAuthenticationError(GmailServiceError):
    """Gmail authentication related error"""

    pass


class GmailAPIError(GmailServiceError):
    """Gmail API call related error"""

    pass


class GmailService:
    """
    Gmail API integration service

    Provides comprehensive Gmail operations including:
    - Email retrieval and search
    - Email sending and draft creation
    - Label management (read/unread status)
    - OAuth2 authentication handling

    Can be used as a context manager for automatic connection management.
    """

    def __init__(self, user: Optional[User] = None, session: Optional[Session] = None):
        self.user = user
        self.db_session = session
        self.gmail_service = None
        self._credentials: Optional[OAuth2Credentials] = None
        self._is_connected = False

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    @property
    def is_connected(self) -> bool:
        """Check if Gmail service is connected"""
        return self._is_connected and self.gmail_service is not None

    async def connect(self) -> None:
        """Connect to Gmail API service"""
        if self._is_connected:
            logger.debug("Already connected to Gmail API")
            return

        try:
            logger.info("Connecting to Gmail API...")

            if self.user and self.db_session:
                await self._setup_credentials()
                self.gmail_service = build("gmail", "v1", credentials=self._credentials)

            self._is_connected = True
            logger.info("Successfully connected to Gmail API")

        except Exception as e:
            logger.error(f"Failed to connect to Gmail API: {e}")
            raise GmailServiceError(f"Connection error: {e}")

    async def _setup_credentials(self) -> None:
        """Set up Google OAuth credentials"""
        if not self.user or not self.db_session:
            raise GmailAuthenticationError(
                "User information or session information is missing"
            )

        try:
            oauth_service = GoogleOauthService(self.db_session)
            credentials = oauth_service.get_credentials(self.user.id)

            if not credentials:
                raise GmailAuthenticationError(
                    "Google credentials not found. Re-authentication is required."
                )

            # Build OAuth2Credentials object
            self._credentials = OAuth2Credentials(
                token=credentials.token,
                refresh_token=credentials.refresh_token,
                token_uri=GmailConfig.OAUTH_TOKEN_URI,
                client_id=os.getenv("GOOGLE_CLIENT_ID"),
                client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
                scopes=GmailConfig.SCOPES,
            )

            logger.debug("Google OAuth credentials have been set")

        except Exception as e:
            logger.error(f"Authentication setup error: {e}")
            raise GmailAuthenticationError(f"Failed to set up authentication: {e}")

    async def disconnect(self) -> None:
        """Disconnect from Gmail API service"""
        self.gmail_service = None
        self._credentials = None
        self._is_connected = False
        logger.debug("Disconnected from Gmail API")

    def _ensure_connected(self) -> None:
        """Ensure Gmail service is connected and raise exception if not"""
        if not self.is_connected:
            raise GmailServiceError("Not connected to Gmail service")

    def _handle_gmail_api_error(self, operation: str, error: Exception) -> None:
        """Handle Gmail API errors consistently"""
        if isinstance(error, HttpError):
            logger.error(f"Gmail API error during {operation}: {error}")
            raise GmailAPIError(f"Failed to {operation}: {error}")
        else:
            logger.error(f"Error during {operation}: {error}")
            raise GmailServiceError(f"Failed to {operation}: {error}")

    def _extract_headers_to_dict(self, headers: List[Dict[str, str]]) -> Dict[str, str]:
        """Extract relevant headers into a dictionary"""
        result = {}
        for header in headers:
            name = header["name"].lower()
            if name in ["from", "to", "subject", "date", "cc", "bcc", "message-id"]:
                result[name] = header["value"]
        return result

    def _validate_email_parameters(self, to: str, subject: str, body: str) -> None:
        """Validate email parameters"""
        if not to:
            raise GmailServiceError("Recipient email address is required")
        if not subject:
            raise GmailServiceError("Email subject is required")
        if not body:
            raise GmailServiceError("Email body is required")

    # Gmail operation methods

    async def get_emails(
        self, query: str = "", max_results: int = GmailConfig.DEFAULT_MAX_RESULTS
    ) -> List[Dict[str, Any]]:
        """
        Retrieve email list with Gmail search syntax

        Args:
            query: Search query (Gmail search syntax)
            max_results: Maximum number of emails to retrieve

        Returns:
            List of email metadata dictionaries
        """
        self._ensure_connected()

        try:
            # Validate and limit max_results
            max_results = min(max_results, GmailConfig.MAX_RESULTS_LIMIT)

            # Get message list
            result = (
                self.gmail_service.users()
                .messages()
                .list(userId="me", q=query, maxResults=max_results)
                .execute()
            )

            messages = result.get("messages", [])
            if not messages:
                return []

            # Get details for each message
            email_list = []
            for message in messages:
                email_data = await self._get_message_metadata(message["id"])
                email_list.append(email_data)

            logger.info(f"Retrieved {len(email_list)} emails")
            return email_list

        except Exception as e:
            self._handle_gmail_api_error("retrieve emails", e)

    async def _get_message_metadata(self, message_id: str) -> Dict[str, Any]:
        """Get email message metadata efficiently"""
        msg = (
            self.gmail_service.users()
            .messages()
            .get(
                userId="me",
                id=message_id,
                format="metadata",
                metadataHeaders=GmailConfig.METADATA_HEADERS,
            )
            .execute()
        )

        # Organize metadata
        headers = msg["payload"].get("headers", [])
        email_data = {
            "id": msg["id"],
            "threadId": msg["threadId"],
            "snippet": msg.get("snippet", ""),
        }

        # Extract and merge header information
        email_data.update(self._extract_headers_to_dict(headers))
        return email_data

    async def get_email_content(self, email_id: str) -> Dict[str, Any]:
        """
        Get specific email content including body

        Args:
            email_id: Gmail message ID

        Returns:
            Dictionary containing email content and metadata
        """
        self._ensure_connected()

        try:
            msg = (
                self.gmail_service.users()
                .messages()
                .get(userId="me", id=email_id, format="full")
                .execute()
            )

            # Extract message body
            body = self._extract_message_body(msg["payload"])

            # Extract header information
            headers = msg["payload"].get("headers", [])
            headers_dict = self._extract_headers_to_dict(headers)

            email_data = {
                "id": msg["id"],
                "threadId": msg["threadId"],
                "body": body,
                "snippet": msg.get("snippet", ""),
                "headers": headers_dict,  # Add headers separately for easier access
            }

            # Merge header information into main dict for backward compatibility
            email_data.update(headers_dict)

            logger.debug(f"Retrieved content for email {email_id}")
            return email_data

        except Exception as e:
            self._handle_gmail_api_error("get email content", e)

    def _extract_message_body(self, payload: Dict[str, Any]) -> str:
        """
        Extract message body from email payload

        Prioritizes plain text content, falls back to HTML

        Args:
            payload: Gmail message payload

        Returns:
            Decoded message body text
        """
        body = ""

        def decode_data(data: str) -> str:
            """Safely decode Base64 URL-safe data"""
            try:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            except Exception as e:
                logger.warning(f"Failed to decode message data: {e}")
                return ""

        if "parts" in payload:
            # Handle multipart messages
            for part in payload["parts"]:
                mime_type = part.get("mimeType", "")
                data = part["body"].get("data")

                if data:
                    if mime_type == "text/plain":
                        body = decode_data(data)
                        break  # Prioritize plain text
                    elif mime_type == "text/html" and not body:
                        body = decode_data(data)
        else:
            # Handle simple messages
            mime_type = payload.get("mimeType", "")
            if mime_type in GmailConfig.SUPPORTED_MIME_TYPES:
                data = payload["body"].get("data")
                if data:
                    body = decode_data(data)

        return body

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an email message

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content
            cc: CC email address (optional)
            bcc: BCC email address (optional)

        Returns:
            Dictionary with send result
        """
        self._ensure_connected()
        self._validate_email_parameters(to, subject, body)

        try:
            raw_message = self._create_message(to, subject, body, cc, bcc)

            # Send email
            result = (
                self.gmail_service.users()
                .messages()
                .send(userId="me", body={"raw": raw_message})
                .execute()
            )

            logger.info(f"Email sent successfully to {to}")
            return {
                "id": result["id"],
                "threadId": result["threadId"],
                "status": "sent",
            }

        except Exception as e:
            self._handle_gmail_api_error("send email", e)

    async def create_draft(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create an email draft

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content
            cc: CC email address (optional)
            bcc: BCC email address (optional)

        Returns:
            Dictionary with draft creation result
        """
        self._ensure_connected()
        self._validate_email_parameters(to, subject, body)

        try:
            raw_message = self._create_message(to, subject, body, cc, bcc)

            # Create draft
            result = (
                self.gmail_service.users()
                .drafts()
                .create(userId="me", body={"message": {"raw": raw_message}})
                .execute()
            )

            logger.info(f"Draft created successfully for {to}")
            return {
                "id": result["id"],
                "message": result["message"],
                "status": "draft_created",
            }

        except Exception as e:
            self._handle_gmail_api_error("create draft", e)

    async def create_reply_draft(
        self,
        original_email_id: str,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a reply draft that is threaded to the original email

        Args:
            original_email_id: ID of the original email to reply to
            to: Recipient email address
            subject: Email subject
            body: Email body content
            cc: CC email address (optional)
            bcc: BCC email address (optional)

        Returns:
            Dictionary with draft creation result
        """
        self._ensure_connected()
        self._validate_email_parameters(to, subject, body)

        try:
            # Get original email details for threading
            original_email = await self.get_email_content(original_email_id)
            thread_id = original_email.get("threadId")

            # Extract Message-ID from original email for proper threading
            original_message_id = None
            original_headers = original_email.get("headers", {})
            if isinstance(original_headers, dict):
                original_message_id = original_headers.get("message-id")

            # Create message with proper threading headers
            raw_message = self._create_reply_message(
                to=to,
                subject=subject,
                body=body,
                cc=cc,
                bcc=bcc,
                original_message_id=original_message_id,
                thread_id=thread_id,
            )

            # Create draft with threadId
            draft_body = {"message": {"raw": raw_message}}
            if thread_id:
                draft_body["message"]["threadId"] = thread_id

            result = (
                self.gmail_service.users()
                .drafts()
                .create(userId="me", body=draft_body)
                .execute()
            )

            logger.info(
                f"Reply draft created successfully for {to} in thread {thread_id}"
            )
            return {
                "id": result["id"],
                "message": result["message"],
                "threadId": thread_id,
                "status": "reply_draft_created",
            }

        except Exception as e:
            self._handle_gmail_api_error("create reply draft", e)

    def _create_message(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
    ) -> str:
        """
        Create email message and encode it to Base64

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content
            cc: CC email address (optional)
            bcc: BCC email address (optional)

        Returns:
            Base64 URL-safe encoded message
        """
        message = email.mime.text.MIMEText(body, "plain", "utf-8")
        message["to"] = to
        message["subject"] = subject

        if cc:
            message["cc"] = cc
        if bcc:
            message["bcc"] = bcc

        # Base64 URL-safe encoding
        return base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

    def _create_reply_message(
        self,
        to: str,
        subject: str,
        body: str,
        original_message_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
    ) -> str:
        """
        Create reply email message with proper threading headers

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content
            original_message_id: Message-ID of the original email
            thread_id: Thread ID of the original email
            cc: CC email address (optional)
            bcc: BCC email address (optional)

        Returns:
            Base64 URL-safe encoded message with threading headers
        """
        message = email.mime.text.MIMEText(body, "plain", "utf-8")
        message["to"] = to
        message["subject"] = subject

        if cc:
            message["cc"] = cc
        if bcc:
            message["bcc"] = bcc

        # Add threading headers for proper reply chain
        if original_message_id:
            message["In-Reply-To"] = original_message_id
            message["References"] = original_message_id

        # Base64 URL-safe encoding
        return base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

    # Label operation methods

    async def mark_as_read(self, email_id: str) -> Dict[str, Any]:
        """
        Mark email as read

        Args:
            email_id: Gmail message ID

        Returns:
            Operation result dictionary
        """
        return await self._modify_labels(email_id, remove_labels=["UNREAD"])

    async def mark_as_unread(self, email_id: str) -> Dict[str, Any]:
        """
        Mark email as unread

        Args:
            email_id: Gmail message ID

        Returns:
            Operation result dictionary
        """
        return await self._modify_labels(email_id, add_labels=["UNREAD"])

    async def _modify_labels(
        self,
        email_id: str,
        add_labels: Optional[List[str]] = None,
        remove_labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Modify email labels efficiently

        Args:
            email_id: Gmail message ID
            add_labels: List of label IDs to add
            remove_labels: List of label IDs to remove

        Returns:
            Operation result dictionary
        """
        self._ensure_connected()

        if not add_labels and not remove_labels:
            raise GmailServiceError("At least one label operation must be specified")

        try:
            body = {}
            if add_labels:
                body["addLabelIds"] = add_labels
            if remove_labels:
                body["removeLabelIds"] = remove_labels

            result = (
                self.gmail_service.users()
                .messages()
                .modify(userId="me", id=email_id, body=body)
                .execute()
            )

            # Determine operation status
            status = "labels_modified"
            if remove_labels and "UNREAD" in remove_labels:
                status = "marked_as_read"
            elif add_labels and "UNREAD" in add_labels:
                status = "marked_as_unread"

            logger.debug(f"Modified labels for email {email_id}: {status}")
            return {"id": result["id"], "status": status}

        except Exception as e:
            self._handle_gmail_api_error("modify labels", e)

    async def get_drafts(
        self, max_results: int = GmailConfig.DEFAULT_MAX_RESULTS
    ) -> List[Dict[str, Any]]:
        """
        Get list of email drafts

        Args:
            max_results: Maximum number of drafts to retrieve

        Returns:
            List of draft dictionaries with metadata
        """
        self._ensure_connected()

        try:
            # Validate max_results
            max_results = min(max_results, GmailConfig.MAX_RESULTS_LIMIT)

            # Get drafts list
            result = (
                self.gmail_service.users()
                .drafts()
                .list(userId="me", maxResults=max_results)
                .execute()
            )

            drafts = result.get("drafts", [])
            drafts_data = []

            # Get metadata for each draft
            for draft in drafts:
                draft_id = draft["id"]
                draft_detail = await self._get_draft_metadata(draft_id)
                drafts_data.append(draft_detail)

            logger.info(f"Retrieved {len(drafts_data)} drafts")
            return drafts_data

        except Exception as e:
            self._handle_gmail_api_error("get drafts", e)

    async def get_draft(self, draft_id: str) -> Dict[str, Any]:
        """
        Get specific draft details

        Args:
            draft_id: Draft ID to retrieve

        Returns:
            Dictionary with complete draft information
        """
        self._ensure_connected()

        try:
            # Get draft details
            result = (
                self.gmail_service.users()
                .drafts()
                .get(userId="me", id=draft_id)
                .execute()
            )

            message = result.get("message", {})
            payload = message.get("payload", {})

            # Extract headers
            headers = self._extract_headers_to_dict(payload.get("headers", []))

            # Extract body
            body = self._extract_message_body(payload)

            draft_data = {
                "id": result["id"],
                "subject": headers.get("subject", ""),
                "body": body,
                "to": headers.get("to", ""),
                "cc": headers.get("cc", ""),
                "bcc": headers.get("bcc", ""),
                "thread_id": message.get("threadId"),
                "snippet": message.get("snippet", ""),
                "created_at": headers.get("date", ""),
                "updated_at": headers.get("date", ""),
            }

            logger.info(f"Retrieved draft {draft_id}")
            return draft_data

        except Exception as e:
            self._handle_gmail_api_error("get draft", e)

    async def _get_draft_metadata(self, draft_id: str) -> Dict[str, Any]:
        """
        Get draft metadata without full body content

        Args:
            draft_id: Draft ID to retrieve metadata for

        Returns:
            Dictionary with draft metadata
        """
        try:
            result = (
                self.gmail_service.users()
                .drafts()
                .get(userId="me", id=draft_id, format="metadata")
                .execute()
            )

            message = result.get("message", {})
            payload = message.get("payload", {})

            # Extract headers
            headers = self._extract_headers_to_dict(payload.get("headers", []))

            return {
                "id": result["id"],
                "message_id": message.get("id"),
                "thread_id": message.get("threadId"),
                "to": headers.get("to", ""),
                "from": headers.get("from", ""),
                "subject": headers.get("subject", ""),
                "date": headers.get("date", ""),
                "cc": headers.get("cc", ""),
                "snippet": message.get("snippet", ""),
            }

        except Exception as e:
            logger.error(f"Failed to get draft metadata for {draft_id}: {str(e)}")
            return {"id": draft_id, "error": str(e)}

    async def get_drafts_by_thread_id(self, thread_id: str) -> List[Dict[str, Any]]:
        """
        Get drafts for a specific thread

        Args:
            thread_id: Gmail thread ID to get drafts for

        Returns:
            List of draft dictionaries for the specified thread
        """
        self._ensure_connected()

        try:
            # Get all drafts first
            result = self.gmail_service.users().drafts().list(userId="me").execute()

            drafts = result.get("drafts", [])
            thread_drafts = []

            # Filter drafts by thread ID
            for draft in drafts:
                draft_detail = await self._get_draft_metadata(draft["id"])
                if draft_detail.get("thread_id") == thread_id:
                    # Get full draft details for thread matches
                    full_draft = await self.get_draft(draft["id"])
                    thread_drafts.append(full_draft)

            logger.info(f"Found {len(thread_drafts)} drafts for thread {thread_id}")
            return thread_drafts

        except Exception as e:
            self._handle_gmail_api_error("get drafts by thread id", e)

    async def delete_draft(self, draft_id: str) -> Dict[str, Any]:
        """
        Delete a specific draft

        Args:
            draft_id: Draft ID to delete

        Returns:
            Dictionary with deletion result
        """
        self._ensure_connected()

        try:
            # Delete the draft
            self.gmail_service.users().drafts().delete(
                userId="me", id=draft_id
            ).execute()

            logger.info(f"Draft {draft_id} deleted successfully")
            return {
                "id": draft_id,
                "status": "deleted",
                "message": "Draft deleted successfully",
            }

        except Exception as e:
            self._handle_gmail_api_error("delete draft", e)

    async def delete_drafts_by_thread_id(self, thread_id: str) -> Dict[str, Any]:
        """
        Delete all drafts for a specific thread

        Args:
            thread_id: Gmail thread ID to delete drafts for

        Returns:
            Dictionary with deletion results
        """
        self._ensure_connected()

        try:
            # Get all drafts for the thread
            thread_drafts = await self.get_drafts_by_thread_id(thread_id)

            if not thread_drafts:
                logger.info(f"No drafts found for thread {thread_id}")
                return {
                    "thread_id": thread_id,
                    "deleted_count": 0,
                    "status": "no_drafts_found",
                    "message": "No drafts found for this thread",
                }

            # Delete each draft
            deleted_draft_ids = []
            failed_deletions = []

            for draft in thread_drafts:
                try:
                    await self.delete_draft(draft["id"])
                    deleted_draft_ids.append(draft["id"])
                except Exception as e:
                    logger.error(f"Failed to delete draft {draft['id']}: {str(e)}")
                    failed_deletions.append({"id": draft["id"], "error": str(e)})

            logger.info(
                f"Deleted {len(deleted_draft_ids)} drafts for thread {thread_id}"
            )
            return {
                "thread_id": thread_id,
                "deleted_count": len(deleted_draft_ids),
                "deleted_draft_ids": deleted_draft_ids,
                "failed_deletions": failed_deletions,
                "status": "completed",
                "message": f"Deleted {len(deleted_draft_ids)} drafts successfully",
            }

        except Exception as e:
            self._handle_gmail_api_error("delete drafts by thread id", e)

    # Convenience methods for common email operations

    async def get_unread_emails(
        self, max_results: int = GmailConfig.DEFAULT_MAX_RESULTS
    ) -> List[Dict[str, Any]]:
        """
        Get unread emails

        Args:
            max_results: Maximum number of emails to retrieve

        Returns:
            List of unread email metadata
        """
        return await self.get_emails(query="is:unread", max_results=max_results)

    async def get_new_emails(
        self, max_results: int = GmailConfig.DEFAULT_MAX_RESULTS
    ) -> List[Dict[str, Any]]:
        """
        Get new emails (unread and not archived)

        Args:
            max_results: Maximum number of emails to retrieve

        Returns:
            List of new email metadata
        """
        return await self.get_emails(
            query="is:unread -label:archived", max_results=max_results
        )

    async def search_emails(
        self, query: str, max_results: int = GmailConfig.DEFAULT_MAX_RESULTS
    ) -> List[Dict[str, Any]]:
        """
        Search emails with Gmail query syntax

        Args:
            query: Gmail search query
            max_results: Maximum number of emails to retrieve

        Returns:
            List of matching email metadata
        """
        return await self.get_emails(query=query, max_results=max_results)


# Factory functions and utilities


@asynccontextmanager
async def get_gmail_service(
    user: Optional[User] = None, session: Optional[Session] = None
):
    """
    Create and manage GmailService as a context manager

    Args:
        user: User information (required for authenticated operations)
        session: Database session (required for authenticated operations)

    Yields:
        GmailService: Configured Gmail service instance

    Raises:
        GmailServiceError: If service creation or connection fails
    """
    service = GmailService(user=user, session=session)
    try:
        async with service:
            yield service
    except Exception as e:
        logger.error(f"Gmail service error: {e}")
        raise


@asynccontextmanager
async def get_authenticated_gmail_service(user: User, session: Session):
    """
    Create authenticated GmailService context manager

    Args:
        user: User information (required)
        session: Database session (required)

    Yields:
        GmailService: Authenticated Gmail service instance

    Raises:
        GmailAuthenticationError: If user or session is missing
        GmailServiceError: If service creation fails
    """
    if not user:
        raise GmailAuthenticationError("User information is required")
    if not session:
        raise GmailServiceError("Database session is required")

    async with get_gmail_service(user=user, session=session) as service:
        yield service
