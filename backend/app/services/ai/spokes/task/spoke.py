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
    """Manage Task Spoke"""

    def _task_to_dict(self, task) -> dict:
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

    async def action_get_incomplete_tasks(self, _: dict) -> SpokeResponse:
        """Get all incomplete Tasks for a user."""
        try:
            tasks = find_tasks(
                session=self.session,
                user_id=self.current_user.id,
                completed=False,
            )
            # Convert to dict for JSON serialization
            task_data = [self._task_to_dict(task) for task in tasks]
            return SpokeResponse(success=True, data=task_data)
        except Exception as e:
            return SpokeResponse(
                success=False, error=f"Error getting incomplete tasks: {str(e)}"
            )

    async def action_get_completed_tasks(self, _: dict) -> SpokeResponse:
        """Get all completed Tasks for a user."""
        try:
            tasks = find_tasks(
                session=self.session,
                user_id=self.current_user.id,
                completed=True,
            )
            # Convert to dict for JSON serialization
            task_data = [self._task_to_dict(task) for task in tasks]
            return SpokeResponse(success=True, data=task_data)
        except Exception as e:
            return SpokeResponse(
                success=False, error=f"Error getting completed tasks: {str(e)}"
            )

    async def action_search_tasks_more_than_expires_at(
        self, parameters: dict
    ) -> SpokeResponse:
        """Search Tasks that expire after a certain timestamp."""
        try:
            expires_at = parameters["expires_at"]
            tasks = find_tasks(
                session=self.session,
                user_id=self.current_user.id,
                completed=False,
                expires_at=expires_at,
            )
            # Convert to dict for JSON serialization
            task_data = [self._task_to_dict(task) for task in tasks]
            return SpokeResponse(success=True, data=task_data)
        except Exception as e:
            return SpokeResponse(
                success=False, error=f"Error searching tasks: {str(e)}"
            )

    async def action_add_task(self, parameters: dict) -> SpokeResponse:
        """Add a new Task."""
        try:
            title = parameters["title"]
            description = parameters.get("description")
            expires_at = parameters.get("expires_at")

            task = create_task(
                session=self.session,
                user_id=self.current_user.id,
                title=title,
                description=description,
                expires_at=expires_at,
            )

            # Convert to dict for JSON serialization
            task_data = self._task_to_dict(task)
            return SpokeResponse(success=True, data=task_data)
        except Exception as e:
            return SpokeResponse(success=False, error=f"Error adding task: {str(e)}")

    async def action_to_complete_task(self, parameters: dict) -> SpokeResponse:
        """Mark a Task as completed."""
        try:
            task_id = parameters["task_id"]
            task = complete_task(
                session=self.session,
                id=task_id,
            )

            # Convert to dict for JSON serialization
            task_data = self._task_to_dict(task)
            return SpokeResponse(success=True, data=task_data)
        except Exception as e:
            return SpokeResponse(
                success=False, error=f"Error completing task: {str(e)}"
            )

    async def action_to_incomplete_task(self, parameters: dict) -> SpokeResponse:
        """Mark a Task as incomplete."""
        try:
            task_id = parameters["task_id"]
            task = incomplete_task(
                session=self.session,
                id=task_id,
            )

            # Convert to dict for JSON serialization
            task_data = self._task_to_dict(task)
            return SpokeResponse(success=True, data=task_data)
        except Exception as e:
            return SpokeResponse(
                success=False, error=f"Error marking task as incomplete: {str(e)}"
            )

    async def action_update_user_task(self, parameters: dict) -> SpokeResponse:
        """Update a Task."""
        try:
            task_id = parameters["task_id"]
            title = parameters.get("title")
            description = parameters.get("description")
            expires_at = parameters.get("expires_at")

            task = update_task(
                session=self.session,
                id=task_id,
                title=title,
                description=description,
                expires_at=expires_at,
            )

            # Convert to dict for JSON serialization
            task_data = self._task_to_dict(task)
            return SpokeResponse(success=True, data=task_data)
        except Exception as e:
            return SpokeResponse(success=False, error=f"Error updating task: {str(e)}")

    async def action_delete_user_task(self, parameters: dict) -> SpokeResponse:
        """Delete a Task."""
        try:
            task_id = parameters["task_id"]
            delete_task(session=self.session, id=task_id)
            return SpokeResponse(success=True, data={"deleted_task_id": task_id})
        except ValueError as e:
            return SpokeResponse(success=False, error=f"Task not found: {str(e)}")
        except Exception as e:
            return SpokeResponse(success=False, error=f"Error deleting task: {str(e)}")
