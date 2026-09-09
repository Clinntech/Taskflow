from datetime import date, datetime
from typing import Optional
from uuid import UUID

from database import get_current_user, get_supabase_client


VALID_PRIORITIES = {"Low", "Medium", "High"}


def _get_user_id() -> str:
    """
    Return the authenticated user's ID.
    """

    user = get_current_user()

    if user is None:
        raise RuntimeError(
            "You must sign in before managing tasks."
        )

    user_id = getattr(user, "id", None)

    if not user_id:
        raise RuntimeError(
            "The authenticated user's ID could not be found."
        )

    return str(user_id)


def _validate_task_id(task_id: str) -> str:
    """
    Confirm that a task ID is a valid UUID.
    """

    try:
        return str(UUID(str(task_id)))
    except (TypeError, ValueError, AttributeError) as error:
        raise ValueError("The task ID is invalid.") from error


def _format_date(value) -> str:
    """
    Convert a date, datetime, or ISO date string to YYYY-MM-DD.
    """

    if isinstance(value, datetime):
        return value.date().isoformat()

    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, str):
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError as error:
            raise ValueError(
                "The date must use the YYYY-MM-DD format."
            ) from error

    raise ValueError("Enter a valid due date.")


def _validate_title(title: str) -> str:
    """
    Validate and clean a task title.
    """

    if not isinstance(title, str):
        raise ValueError("The task title must be text.")

    cleaned_title = title.strip()

    if not cleaned_title:
        raise ValueError("Enter a task title.")

    if len(cleaned_title) > 150:
        raise ValueError(
            "The task title cannot exceed 150 characters."
        )

    return cleaned_title


def _validate_priority(priority: str) -> str:
    """
    Validate a task priority.
    """

    if priority not in VALID_PRIORITIES:
        raise ValueError(
            "Priority must be Low, Medium, or High."
        )

    return priority


def add_task(
    title: str,
    description: str,
    due_date,
    priority: str = "Medium",
) -> dict:
    """
    Add a new task for the currently authenticated user.
    """

    user_id = _get_user_id()
    cleaned_title = _validate_title(title)
    formatted_date = _format_date(due_date)
    validated_priority = _validate_priority(priority)

    task_data = {
        "user_id": user_id,
        "title": cleaned_title,
        "description": (description or "").strip(),
        "due_date": formatted_date,
        "priority": validated_priority,
        "completed": False,
    }

    try:
        client = get_supabase_client()

        response = (
            client.table("tasks")
            .insert(task_data)
            .execute()
        )

        if not response.data:
            raise RuntimeError(
                "The task could not be created."
            )

        return response.data[0]

    except ValueError:
        raise

    except Exception as error:
        if isinstance(error, RuntimeError):
            raise

        raise RuntimeError(
            f"Unable to add the task: {error}"
        ) from error


def get_tasks(
    completed: Optional[bool] = None,
) -> list[dict]:
    """
    Return the signed-in user's tasks.

    Pass completed=True to return completed tasks.
    Pass completed=False to return pending tasks.
    Leave completed as None to return every task.
    """

    user_id = _get_user_id()

    try:
        client = get_supabase_client()

        query = (
            client.table("tasks")
            .select("*")
            .eq("user_id", user_id)
        )

        if completed is not None:
            query = query.eq("completed", completed)

        response = (
            query
            .order("due_date")
            .order("created_at")
            .execute()
        )

        return response.data or []

    except Exception as error:
        raise RuntimeError(
            f"Unable to load tasks: {error}"
        ) from error


def get_task(task_id: str) -> dict:
    """
    Return one task belonging to the signed-in user.
    """

    user_id = _get_user_id()
    validated_id = _validate_task_id(task_id)

    try:
        client = get_supabase_client()

        response = (
            client.table("tasks")
            .select("*")
            .eq("id", validated_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

        if not response.data:
            raise ValueError(
                "The requested task does not exist."
            )

        return response.data[0]

    except ValueError:
        raise

    except Exception as error:
        raise RuntimeError(
            f"Unable to load the task: {error}"
        ) from error


def update_task(
    task_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    due_date=None,
    priority: Optional[str] = None,
) -> dict:
    """
    Update the editable fields of an existing task.
    """

    user_id = _get_user_id()
    validated_id = _validate_task_id(task_id)

    changes = {}

    if title is not None:
        changes["title"] = _validate_title(title)

    if description is not None:
        changes["description"] = description.strip()

    if due_date is not None:
        changes["due_date"] = _format_date(due_date)

    if priority is not None:
        changes["priority"] = _validate_priority(priority)

    if not changes:
        raise ValueError(
            "No task changes were provided."
        )

    try:
        client = get_supabase_client()

        response = (
            client.table("tasks")
            .update(changes)
            .eq("id", validated_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not response.data:
            raise ValueError(
                "The task does not exist or cannot be updated."
            )

        return response.data[0]

    except ValueError:
        raise

    except Exception as error:
        raise RuntimeError(
            f"Unable to update the task: {error}"
        ) from error


def mark_task_completed(
    task_id: str,
    completed: bool = True,
) -> dict:
    """
    Mark a task as completed or pending.
    """

    if not isinstance(completed, bool):
        raise ValueError(
            "The completed value must be True or False."
        )

    user_id = _get_user_id()
    validated_id = _validate_task_id(task_id)

    try:
        client = get_supabase_client()

        response = (
            client.table("tasks")
            .update({"completed": completed})
            .eq("id", validated_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not response.data:
            raise ValueError(
                "The task does not exist or cannot be updated."
            )

        return response.data[0]

    except ValueError:
        raise

    except Exception as error:
        raise RuntimeError(
            f"Unable to change the task status: {error}"
        ) from error


def toggle_task_status(task_id: str) -> dict:
    """
    Switch a completed task to pending or a pending task to completed.
    """

    task = get_task(task_id)

    return mark_task_completed(
        task_id,
        not task["completed"],
    )


def reschedule_task(
    task_id: str,
    new_due_date,
) -> dict:
    """
    Move a task to another date.
    """

    return update_task(
        task_id=task_id,
        due_date=new_due_date,
    )


def delete_task(task_id: str) -> dict:
    """
    Delete a task belonging to the signed-in user.
    """

    user_id = _get_user_id()
    validated_id = _validate_task_id(task_id)

    try:
        client = get_supabase_client()

        response = (
            client.table("tasks")
            .delete()
            .eq("id", validated_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not response.data:
            raise ValueError(
                "The task does not exist or has already been deleted."
            )

        return response.data[0]

    except ValueError:
        raise

    except Exception as error:
        raise RuntimeError(
            f"Unable to delete the task: {error}"
        ) from error


def get_tasks_due_on(selected_date) -> list[dict]:
    """
    Return tasks scheduled for a particular date.
    """

    user_id = _get_user_id()
    formatted_date = _format_date(selected_date)

    try:
        client = get_supabase_client()

        response = (
            client.table("tasks")
            .select("*")
            .eq("user_id", user_id)
            .eq("due_date", formatted_date)
            .order("created_at")
            .execute()
        )

        return response.data or []

    except Exception as error:
        raise RuntimeError(
            f"Unable to load scheduled tasks: {error}"
        ) from error


def get_overdue_tasks() -> list[dict]:
    """
    Return incomplete tasks with due dates before today.
    """

    user_id = _get_user_id()

    try:
        client = get_supabase_client()

        response = (
            client.table("tasks")
            .select("*")
            .eq("user_id", user_id)
            .eq("completed", False)
            .lt("due_date", date.today().isoformat())
            .order("due_date")
            .execute()
        )

        return response.data or []

    except Exception as error:
        raise RuntimeError(
            f"Unable to load overdue tasks: {error}"
        ) from error


def get_task_statistics() -> dict:
    """
    Calculate task statistics for the authenticated user.
    """

    tasks = get_tasks()

    total_tasks = len(tasks)

    completed_tasks = sum(
        1 for task in tasks if task.get("completed", False)
    )

    pending_tasks = total_tasks - completed_tasks

    completion_rate = (
        round((completed_tasks / total_tasks) * 100)
        if total_tasks
        else 0
    )

    return {
        "total": total_tasks,
        "pending": pending_tasks,
        "completed": completed_tasks,
        "completion_rate": completion_rate,
    }