from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID

from database import get_current_user, get_supabase_client


def _get_user_id() -> str:
    """
    Return the authenticated user's Supabase ID.
    """

    user = get_current_user()

    if user is None:
        raise RuntimeError(
            "You must sign in before managing weekly goals."
        )

    user_id = getattr(user, "id", None)

    if not user_id:
        raise RuntimeError(
            "The authenticated user's ID could not be found."
        )

    return str(user_id)


def _validate_goal_id(goal_id: str) -> str:
    """
    Confirm that a goal ID is a valid UUID.
    """

    try:
        return str(UUID(str(goal_id)))
    except (TypeError, ValueError, AttributeError) as error:
        raise ValueError("The goal ID is invalid.") from error


def _convert_to_date(value) -> date:
    """
    Convert a date, datetime, or ISO date string into a date.
    """

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError as error:
            raise ValueError(
                "The date must use the YYYY-MM-DD format."
            ) from error

    raise ValueError("Enter a valid date.")


def get_week_start(selected_date=None) -> date:
    """
    Return the Monday for the week containing the selected date.
    """

    selected_date = (
        _convert_to_date(selected_date)
        if selected_date is not None
        else date.today()
    )

    return selected_date - timedelta(
        days=selected_date.weekday()
    )


def get_week_end(selected_date=None) -> date:
    """
    Return the Sunday for the selected week.
    """

    return get_week_start(selected_date) + timedelta(days=6)


def _validate_title(title: str) -> str:
    """
    Validate and clean a goal title.
    """

    if not isinstance(title, str):
        raise ValueError("The goal title must be text.")

    cleaned_title = title.strip()

    if not cleaned_title:
        raise ValueError("Enter a weekly goal.")

    if len(cleaned_title) > 150:
        raise ValueError(
            "The goal title cannot exceed 150 characters."
        )

    return cleaned_title


def _validate_target_date(
    target_date,
    week_start: date,
) -> Optional[str]:
    """
    Confirm that the target date is within the selected week.
    """

    if target_date is None:
        return None

    converted_target = _convert_to_date(target_date)
    week_end = week_start + timedelta(days=6)

    if not week_start <= converted_target <= week_end:
        raise ValueError(
            "The target date must be within the selected week."
        )

    return converted_target.isoformat()


def add_goal(
    title: str,
    description: str = "",
    week_start=None,
    target_date=None,
) -> dict:
    """
    Create a weekly goal for the signed-in user.
    """

    user_id = _get_user_id()
    cleaned_title = _validate_title(title)

    selected_week_start = get_week_start(
        week_start if week_start is not None else date.today()
    )

    formatted_target_date = _validate_target_date(
        target_date,
        selected_week_start,
    )

    goal_data = {
        "user_id": user_id,
        "title": cleaned_title,
        "description": (description or "").strip(),
        "week_start": selected_week_start.isoformat(),
        "target_date": formatted_target_date,
        "completed": False,
    }

    try:
        client = get_supabase_client()

        response = (
            client.table("weekly_goals")
            .insert(goal_data)
            .execute()
        )

        if not response.data:
            raise RuntimeError(
                "The weekly goal could not be created."
            )

        return response.data[0]

    except ValueError:
        raise

    except Exception as error:
        if isinstance(error, RuntimeError):
            raise

        raise RuntimeError(
            f"Unable to add the weekly goal: {error}"
        ) from error


def get_goals(
    week_start=None,
    completed: Optional[bool] = None,
) -> list[dict]:
    """
    Return weekly goals belonging to the signed-in user.

    Provide a date to return goals for that week.
    Leave week_start as None to return goals from every week.
    """

    user_id = _get_user_id()

    try:
        client = get_supabase_client()

        query = (
            client.table("weekly_goals")
            .select("*")
            .eq("user_id", user_id)
        )

        if week_start is not None:
            selected_week_start = get_week_start(week_start)

            query = query.eq(
                "week_start",
                selected_week_start.isoformat(),
            )

        if completed is not None:
            query = query.eq("completed", completed)

        response = (
            query
            .order("week_start", desc=True)
            .order("target_date")
            .order("created_at")
            .execute()
        )

        return response.data or []

    except Exception as error:
        raise RuntimeError(
            f"Unable to load weekly goals: {error}"
        ) from error


def get_current_week_goals(
    completed: Optional[bool] = None,
) -> list[dict]:
    """
    Return goals for the current week.
    """

    return get_goals(
        week_start=date.today(),
        completed=completed,
    )


def get_goal(goal_id: str) -> dict:
    """
    Return one goal belonging to the signed-in user.
    """

    user_id = _get_user_id()
    validated_id = _validate_goal_id(goal_id)

    try:
        client = get_supabase_client()

        response = (
            client.table("weekly_goals")
            .select("*")
            .eq("id", validated_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

        if not response.data:
            raise ValueError(
                "The requested weekly goal does not exist."
            )

        return response.data[0]

    except ValueError:
        raise

    except Exception as error:
        raise RuntimeError(
            f"Unable to load the weekly goal: {error}"
        ) from error


def update_goal(
    goal_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    week_start=None,
    target_date=None,
    update_target_date: bool = False,
) -> dict:
    """
    Update an existing weekly goal.

    Set update_target_date=True when changing or removing the target
    date. Pass target_date=None with update_target_date=True to remove it.
    """

    user_id = _get_user_id()
    validated_id = _validate_goal_id(goal_id)
    current_goal = get_goal(validated_id)

    changes = {}

    current_week_start = _convert_to_date(
        current_goal["week_start"]
    )

    if title is not None:
        changes["title"] = _validate_title(title)

    if description is not None:
        changes["description"] = description.strip()

    if week_start is not None:
        current_week_start = get_week_start(week_start)
        changes["week_start"] = current_week_start.isoformat()

        existing_target = current_goal.get("target_date")

        if existing_target and not update_target_date:
            changes["target_date"] = _validate_target_date(
                existing_target,
                current_week_start,
            )

    if update_target_date:
        changes["target_date"] = _validate_target_date(
            target_date,
            current_week_start,
        )

    if not changes:
        raise ValueError(
            "No weekly goal changes were provided."
        )

    try:
        client = get_supabase_client()

        response = (
            client.table("weekly_goals")
            .update(changes)
            .eq("id", validated_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not response.data:
            raise ValueError(
                "The weekly goal does not exist or cannot be updated."
            )

        return response.data[0]

    except ValueError:
        raise

    except Exception as error:
        raise RuntimeError(
            f"Unable to update the weekly goal: {error}"
        ) from error


def mark_goal_completed(
    goal_id: str,
    completed: bool = True,
) -> dict:
    """
    Mark a weekly goal as completed or incomplete.
    """

    if not isinstance(completed, bool):
        raise ValueError(
            "The completed value must be True or False."
        )

    user_id = _get_user_id()
    validated_id = _validate_goal_id(goal_id)

    try:
        client = get_supabase_client()

        response = (
            client.table("weekly_goals")
            .update({"completed": completed})
            .eq("id", validated_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not response.data:
            raise ValueError(
                "The weekly goal does not exist or cannot be updated."
            )

        return response.data[0]

    except ValueError:
        raise

    except Exception as error:
        raise RuntimeError(
            f"Unable to change the goal status: {error}"
        ) from error


def toggle_goal_status(goal_id: str) -> dict:
    """
    Switch a completed goal to incomplete or an incomplete goal
    to completed.
    """

    goal = get_goal(goal_id)

    return mark_goal_completed(
        goal_id,
        not goal["completed"],
    )


def reschedule_goal(
    goal_id: str,
    new_week,
    new_target_date=None,
) -> dict:
    """
    Move a goal to another week and optionally select a target date.
    """

    return update_goal(
        goal_id=goal_id,
        week_start=new_week,
        target_date=new_target_date,
        update_target_date=True,
    )


def delete_goal(goal_id: str) -> dict:
    """
    Delete a weekly goal belonging to the signed-in user.
    """

    user_id = _get_user_id()
    validated_id = _validate_goal_id(goal_id)

    try:
        client = get_supabase_client()

        response = (
            client.table("weekly_goals")
            .delete()
            .eq("id", validated_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not response.data:
            raise ValueError(
                "The weekly goal does not exist or was already deleted."
            )

        return response.data[0]

    except ValueError:
        raise

    except Exception as error:
        raise RuntimeError(
            f"Unable to delete the weekly goal: {error}"
        ) from error


def get_goal_statistics(week_start=None) -> dict:
    """
    Calculate goal statistics for a selected week.
    """

    selected_week = (
        week_start if week_start is not None else date.today()
    )

    goals = get_goals(week_start=selected_week)

    total_goals = len(goals)

    completed_goals = sum(
        1 for goal in goals if goal.get("completed", False)
    )

    pending_goals = total_goals - completed_goals

    completion_rate = (
        round((completed_goals / total_goals) * 100)
        if total_goals
        else 0
    )

    return {
        "total": total_goals,
        "pending": pending_goals,
        "completed": completed_goals,
        "completion_rate": completion_rate,
        "week_start": get_week_start(selected_week).isoformat(),
        "week_end": get_week_end(selected_week).isoformat(),
    }