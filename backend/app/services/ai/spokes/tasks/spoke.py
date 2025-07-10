import logging
from typing import Any, Dict, List, Optional

from app.repositories.tasks import (
    complete_task,
    create_task,
    delete_task,
    find_tasks,
    incomplete_task,
    update_task,
)
from app.services.ai.models import SpokeResponse
from app.services.ai.spokes.spoke_interface import BaseSpoke


class TaskSpoke(BaseSpoke):
    """Task management spoke for creating, updating, and managing user tasks"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def _validate_user_authentication(self) -> bool:
        """Validate that user is authenticated and session is available"""
        if not self.current_user:
            self.logger.debug(f"current_user is None: {self.current_user}")
            return False
        if not self.session:
            self.logger.debug(f"session is None: {self.session}")
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

    def _create_success_response(self, data: Any, message: str) -> SpokeResponse:
        """Create a standardized success response"""
        return SpokeResponse(
            success=True,
            data=data,
            metadata={"message": message},
        )

    def _create_error_response(
        self, error_message: str, error_type: str = "general_error"
    ) -> SpokeResponse:
        """Create a standardized error response"""
        return SpokeResponse(
            success=False,
            error=error_message,
            data={"error_type": error_type},
        )

    def _validate_task_id(self, parameters: Dict[str, Any]) -> str:
        """Validate and extract task ID from parameters"""
        task_id = parameters.get("task_id")
        if not task_id:
            raise ValueError("Task ID is required")
        return task_id

    def _validate_required_parameters(
        self, parameters: Dict[str, Any], required_fields: List[str]
    ) -> None:
        """Validate that all required parameters are present and non-empty"""
        missing_fields = []
        for field in required_fields:
            if not parameters.get(field):
                missing_fields.append(field)

        if missing_fields:
            raise ValueError(
                f"Required parameters are missing: {', '.join(missing_fields)}"
            )

    def _convert_task_to_dict(self, task) -> Dict[str, Any]:
        """Convert Task object to dictionary for JSON serialization"""
        return {
            "uuid": str(task.uuid),
            "title": task.title,
            "description": task.description,
            "completed": task.completed,
            "expires_at": task.expires_at,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
        }

    def _convert_tasks_to_list(self, tasks: List[Any]) -> List[Dict[str, Any]]:
        """Convert list of Task objects to list of dictionaries"""
        return [self._convert_task_to_dict(task) for task in tasks]

    async def _get_user_tasks(
        self, completed: Optional[bool] = None, expires_at: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """Get tasks for the current user with optional filters"""
        tasks = find_tasks(
            session=self.session,
            user_id=self.current_user.id,
            completed=completed,
            expires_at=expires_at,
        )
        return self._convert_tasks_to_list(tasks)

    # =================
    # Action methods
    # =================

    async def action_get_incomplete_tasks(
        self, parameters: Dict[str, Any]
    ) -> SpokeResponse:
        """Get all incomplete tasks for the current user"""
        if not self._validate_user_authentication():
            return self._create_authentication_error_response()

        try:
            task_data = await self._get_user_tasks(completed=False)
            return self._create_success_response(
                data=task_data,
                message=f"Successfully retrieved {len(task_data)} incomplete tasks",
            )
        except Exception as e:
            self.logger.error(f"Error getting incomplete tasks: {str(e)}")
            return self._create_error_response(
                f"Error getting incomplete tasks: {str(e)}"
            )

    async def action_get_completed_tasks(
        self, parameters: Dict[str, Any]
    ) -> SpokeResponse:
        """Get all completed tasks for the current user"""
        if not self._validate_user_authentication():
            return self._create_authentication_error_response()

        try:
            task_data = await self._get_user_tasks(completed=True)
            return self._create_success_response(
                data=task_data,
                message=f"Successfully retrieved {len(task_data)} completed tasks",
            )
        except Exception as e:
            self.logger.error(f"Error getting completed tasks: {str(e)}")
            return self._create_error_response(
                f"Error getting completed tasks: {str(e)}"
            )

    async def action_search_tasks_more_than_expires_at(
        self, parameters: Dict[str, Any]
    ) -> SpokeResponse:
        """Search tasks that expire after a specified timestamp"""
        if not self._validate_user_authentication():
            return self._create_authentication_error_response()

        try:
            self._validate_required_parameters(parameters, ["expires_at"])
            expires_at = parameters["expires_at"]

            task_data = await self._get_user_tasks(
                completed=False, expires_at=expires_at
            )
            return self._create_success_response(
                data=task_data,
                message=f"Successfully found {len(task_data)} tasks expiring after timestamp",
            )
        except ValueError as e:
            return self._create_error_response(str(e), "parameter_error")
        except Exception as e:
            self.logger.error(f"Error searching tasks: {str(e)}")
            return self._create_error_response(f"Error searching tasks: {str(e)}")

    async def action_add_task(self, parameters: Dict[str, Any]) -> SpokeResponse:
        """Add a new task for the current user"""
        if not self._validate_user_authentication():
            return self._create_authentication_error_response()

        try:
            self._validate_required_parameters(parameters, ["title"])

            task = create_task(
                session=self.session,
                user_id=self.current_user.id,
                title=parameters["title"],
                description=parameters.get("description"),
                expires_at=parameters.get("expires_at"),
            )

            task_data = self._convert_task_to_dict(task)
            return self._create_success_response(
                data=task_data, message="Task created successfully"
            )
        except ValueError as e:
            return self._create_error_response(str(e), "parameter_error")
        except Exception as e:
            self.logger.error(f"Error adding task: {str(e)}")
            return self._create_error_response(f"Error adding task: {str(e)}")

    async def action_to_complete_task(
        self, parameters: Dict[str, Any]
    ) -> SpokeResponse:
        """Mark a task as completed"""
        if not self._validate_user_authentication():
            return self._create_authentication_error_response()

        try:
            task_id = self._validate_task_id(parameters)

            task = complete_task(session=self.session, id=task_id)
            task_data = self._convert_task_to_dict(task)

            return self._create_success_response(
                data=task_data, message="Task marked as completed successfully"
            )
        except ValueError as e:
            return self._create_error_response(str(e), "parameter_error")
        except Exception as e:
            self.logger.error(f"Error completing task: {str(e)}")
            return self._create_error_response(f"Error completing task: {str(e)}")

    async def action_to_incomplete_task(
        self, parameters: Dict[str, Any]
    ) -> SpokeResponse:
        """Mark a task as incomplete"""
        if not self._validate_user_authentication():
            return self._create_authentication_error_response()

        try:
            task_id = self._validate_task_id(parameters)

            task = incomplete_task(session=self.session, id=task_id)
            task_data = self._convert_task_to_dict(task)

            return self._create_success_response(
                data=task_data, message="Task marked as incomplete successfully"
            )
        except ValueError as e:
            return self._create_error_response(str(e), "parameter_error")
        except Exception as e:
            self.logger.error(f"Error marking task as incomplete: {str(e)}")
            return self._create_error_response(
                f"Error marking task as incomplete: {str(e)}"
            )

    async def action_update_user_task(
        self, parameters: Dict[str, Any]
    ) -> SpokeResponse:
        """Update an existing task"""
        if not self._validate_user_authentication():
            return self._create_authentication_error_response()

        try:
            task_id = self._validate_task_id(parameters)

            task = update_task(
                session=self.session,
                id=task_id,
                title=parameters.get("title"),
                description=parameters.get("description"),
                expires_at=parameters.get("expires_at"),
            )

            task_data = self._convert_task_to_dict(task)
            return self._create_success_response(
                data=task_data, message="Task updated successfully"
            )
        except ValueError as e:
            return self._create_error_response(str(e), "parameter_error")
        except Exception as e:
            self.logger.error(f"Error updating task: {str(e)}")
            return self._create_error_response(f"Error updating task: {str(e)}")

    async def action_delete_user_task(
        self, parameters: Dict[str, Any]
    ) -> SpokeResponse:
        """Delete a task"""
        if not self._validate_user_authentication():
            return self._create_authentication_error_response()

        try:
            task_id = self._validate_task_id(parameters)

            delete_task(session=self.session, id=task_id)

            return self._create_success_response(
                data={"deleted_task_id": task_id}, message="Task deleted successfully"
            )
        except ValueError as e:
            if "not found" in str(e).lower():
                return self._create_error_response(
                    f"Task not found: {str(e)}", "not_found_error"
                )
            return self._create_error_response(str(e), "parameter_error")
        except Exception as e:
            self.logger.error(f"Error deleting task: {str(e)}")
            return self._create_error_response(f"Error deleting task: {str(e)}")
