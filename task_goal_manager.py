from datetime import date, timedelta

import pytest

import storage
from goal_manager import (
    add_weekly_goal,
    delete_weekly_goal,
    get_current_week_goals,
    get_goal_statistics,
    get_goals_for_week,
    get_week_start,
    get_weekly_goal,
    get_weekly_goals,
    increase_goal_progress,
    update_goal_progress,
    update_weekly_goal,
)


@pytest.fixture(autouse=True)
def temporary_storage(tmp_path, monkeypatch):
    """Use temporary JSON files during every test."""
    temporary_data_directory = tmp_path / "data"

    monkeypatch.setattr(
        storage,
        "DATA_DIRECTORY",
        temporary_data_directory,
    )

    monkeypatch.setattr(
        storage,
        "TASKS_FILE",
        temporary_data_directory / "tasks.json",
    )

    monkeypatch.setattr(
        storage,
        "GOALS_FILE",
        temporary_data_directory / "weekly_goals.json",
    )


def test_get_week_start_returns_monday():
    """A selected date should be converted to its Monday."""
    selected_date = date(2026, 9, 3)

    week_start = get_week_start(selected_date)

    assert week_start == "2026-08-31"


def test_add_weekly_goal():
    """A weekly goal should be created and saved."""
    selected_date = date(2026, 9, 3)

    goal = add_weekly_goal(
        title="Complete Python tasks",
        target=5,
        week_start=selected_date,
    )

    goals = get_weekly_goals()

    assert len(goals) == 1
    assert goal["title"] == "Complete Python tasks"
    assert goal["target"] == 5
    assert goal["progress"] == 0
    assert goal["week_start"] == "2026-08-31"
    assert goal["id"]


def test_add_goal_removes_extra_spaces():
    """Extra spaces should be removed from goal titles."""
    goal = add_weekly_goal(
        title="  Finish project documentation  ",
        target=3,
    )

    assert goal["title"] == "Finish project documentation"


def test_add_goal_requires_title():
    """An empty weekly goal title should fail."""
    with pytest.raises(
        ValueError,
        match="A weekly goal title is required",
    ):
        add_weekly_goal(
            title="   ",
            target=5,
        )


def test_add_goal_rejects_zero_target():
    """A target below one should fail."""
    with pytest.raises(
        ValueError,
        match="must be at least 1",
    ):
        add_weekly_goal(
            title="Invalid target",
            target=0,
        )


def test_add_goal_rejects_non_integer_target():
    """A weekly target must be a whole number."""
    with pytest.raises(
        TypeError,
        match="must be a whole number",
    ):
        add_weekly_goal(
            title="Invalid target type",
            target=2.5,
        )


def test_get_existing_weekly_goal():
    """A goal should be found using its unique ID."""
    created_goal = add_weekly_goal(
        title="Learn testing",
        target=4,
    )

    saved_goal = get_weekly_goal(
        created_goal["id"]
    )

    assert saved_goal is not None
    assert saved_goal["id"] == created_goal["id"]
    assert saved_goal["title"] == "Learn testing"


def test_get_missing_goal_returns_none():
    """Searching for a missing goal should return None."""
    assert get_weekly_goal("missing-goal-id") is None


def test_update_weekly_goal():
    """A weekly goal should be editable."""
    goal = add_weekly_goal(
        title="Old goal",
        target=5,
        week_start=date(2026, 9, 3),
    )

    updated_goal = update_weekly_goal(
        goal_id=goal["id"],
        title="Updated goal",
        target=8,
        week_start=date(2026, 9, 10),
    )

    assert updated_goal["title"] == "Updated goal"
    assert updated_goal["target"] == 8
    assert updated_goal["week_start"] == "2026-09-07"


def test_update_missing_goal():
    """Updating a missing goal should produce an error."""
    with pytest.raises(
        ValueError,
        match="Weekly goal not found",
    ):
        update_weekly_goal(
            goal_id="missing-goal-id",
            title="Updated title",
        )


def test_update_goal_progress():
    """Goal progress should be updated."""
    goal = add_weekly_goal(
        title="Complete five lessons",
        target=5,
    )

    updated_goal = update_goal_progress(
        goal_id=goal["id"],
        progress=3,
    )

    assert updated_goal["progress"] == 3


def test_goal_progress_cannot_be_negative():
    """Goal progress cannot be below zero."""
    goal = add_weekly_goal(
        title="Complete lessons",
        target=5,
    )

    with pytest.raises(
        ValueError,
        match="cannot be negative",
    ):
        update_goal_progress(
            goal_id=goal["id"],
            progress=-1,
        )


def test_goal_progress_cannot_exceed_target():
    """Goal progress cannot exceed its target."""
    goal = add_weekly_goal(
        title="Complete lessons",
        target=5,
    )

    with pytest.raises(
        ValueError,
        match="cannot be greater than the target",
    ):
        update_goal_progress(
            goal_id=goal["id"],
            progress=6,
        )


def test_goal_target_cannot_be_lower_than_progress():
    """A new target cannot be lower than current progress."""
    goal = add_weekly_goal(
        title="Complete lessons",
        target=10,
    )

    update_goal_progress(
        goal_id=goal["id"],
        progress=6,
    )

    with pytest.raises(
        ValueError,
        match="cannot be lower than the current progress",
    ):
        update_weekly_goal(
            goal_id=goal["id"],
            target=5,
        )


def test_increase_goal_progress():
    """Progress should increase by the selected amount."""
    goal = add_weekly_goal(
        title="Complete tasks",
        target=5,
    )

    updated_goal = increase_goal_progress(
        goal_id=goal["id"],
        amount=2,
    )

    assert updated_goal["progress"] == 2


def test_increase_goal_progress_stops_at_target():
    """Increasing progress should not exceed the target."""
    goal = add_weekly_goal(
        title="Complete tasks",
        target=5,
    )

    update_goal_progress(
        goal_id=goal["id"],
        progress=4,
    )

    updated_goal = increase_goal_progress(
        goal_id=goal["id"],
        amount=3,
    )

    assert updated_goal["progress"] == 5


def test_delete_weekly_goal():
    """An existing weekly goal should be deleted."""
    goal = add_weekly_goal(
        title="Delete this goal",
        target=2,
    )

    result = delete_weekly_goal(goal["id"])

    assert result is True
    assert get_weekly_goal(goal["id"]) is None
    assert get_weekly_goals() == []


def test_delete_missing_weekly_goal():
    """Deleting a missing goal should produce an error."""
    with pytest.raises(
        ValueError,
        match="Weekly goal not found",
    ):
        delete_weekly_goal("missing-goal-id")


def test_get_goals_for_selected_week():
    """Only goals from the selected week should be returned."""
    current_date = date.today()
    next_week_date = current_date + timedelta(days=7)

    current_goal = add_weekly_goal(
        title="Current week goal",
        target=5,
        week_start=current_date,
    )

    add_weekly_goal(
        title="Next week goal",
        target=3,
        week_start=next_week_date,
    )

    current_week_goals = get_goals_for_week(
        current_date
    )

    assert len(current_week_goals) == 1
    assert current_week_goals[0]["id"] == current_goal["id"]


def test_get_current_week_goals():
    """Current-week goals should be returned."""
    current_goal = add_weekly_goal(
        title="Current goal",
        target=4,
        week_start=date.today(),
    )

    next_week_date = date.today() + timedelta(days=7)

    add_weekly_goal(
        title="Future goal",
        target=2,
        week_start=next_week_date,
    )

    current_goals = get_current_week_goals()

    assert len(current_goals) == 1
    assert current_goals[0]["id"] == current_goal["id"]


def test_goal_statistics():
    """Weekly goal statistics should be accurate."""
    selected_date = date.today()

    first_goal = add_weekly_goal(
        title="Completed goal",
        target=5,
        week_start=selected_date,
    )

    second_goal = add_weekly_goal(
        title="Partially completed goal",
        target=5,
        week_start=selected_date,
    )

    update_goal_progress(
        first_goal["id"],
        5,
    )

    update_goal_progress(
        second_goal["id"],
        2,
    )

    statistics = get_goal_statistics(
        selected_date
    )

    assert statistics["total_goals"] == 2
    assert statistics["completed_goals"] == 1
    assert statistics["total_target"] == 10
    assert statistics["total_progress"] == 7
    assert statistics["completion_rate"] == 70


def test_empty_goal_statistics():
    """An empty week should return zero statistics."""
    statistics = get_goal_statistics(
        date.today()
    )

    assert statistics["total_goals"] == 0
    assert statistics["completed_goals"] == 0
    assert statistics["total_target"] == 0
    assert statistics["total_progress"] == 0
    assert statistics["completion_rate"] == 0