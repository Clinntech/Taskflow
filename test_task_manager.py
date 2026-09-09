from datetime import date, timedelta

import pytest

import storage
from task_manager import (
    add_task,
    delete_task,
    filter_tasks,
    get_all_tasks,
    get_overdue_tasks,
    get_task,
    get_task_statistics,
    reschedule_task,
    set_task_status,
    toggle_task_status,
    update_task,
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


def test_add_task():
    """A task should be created and saved."""
    task = add_task(
        title="Complete Python project",
        description="Finish the task manager tests.",
        due_date=date.today(),
        priority="High",
    )

    tasks = get_all_tasks()

    assert len(tasks) == 1
    assert task["title"] == "Complete Python project"
    assert task["priority"] == "High"
    assert task["status"] == "Pending"
    assert task["completed_at"] is None
    assert task["id"]


def test_add_task_removes_extra_spaces():
    """Extra spaces should be removed from task text."""
    task = add_task(
        title="  Write documentation  ",
        description="  Complete the README file.  ",
    )

    assert task["title"] == "Write documentation"
    assert task["description"] == "Complete the README file."


def test_add_task_requires_title():
    """An empty task title should produce an error."""
    with pytest.raises(
        ValueError,
        match="A task title is required",
    ):
        add_task(title="   ")


def test_add_task_rejects_invalid_priority():
    """An unsupported priority should produce an error."""
    with pytest.raises(
        ValueError,
        match="Priority must be one of",
    ):
        add_task(
            title="Invalid priority task",
            priority="Urgent",
        )


def test_get_existing_task():
    """A saved task should be found using its ID."""
    created_task = add_task(
        title="Review project",
    )

    saved_task = get_task(created_task["id"])

    assert saved_task is not None
    assert saved_task["id"] == created_task["id"]
    assert saved_task["title"] == "Review project"


def test_get_missing_task_returns_none():
    """Searching for a missing task should return None."""
    assert get_task("missing-task-id") is None


def test_update_task():
    """An existing task should be editable."""
    task = add_task(
        title="Old title",
        description="Old description",
        priority="Low",
    )

    new_due_date = date.today() + timedelta(days=3)

    updated_task = update_task(
        task_id=task["id"],
        title="Updated title",
        description="Updated description",
        due_date=new_due_date,
        priority="High",
    )

    assert updated_task["title"] == "Updated title"
    assert updated_task["description"] == "Updated description"
    assert updated_task["priority"] == "High"
    assert updated_task["due_date"] == new_due_date.isoformat()


def test_update_missing_task():
    """Updating a task that does not exist should fail."""
    with pytest.raises(
        ValueError,
        match="Task not found",
    ):
        update_task(
            task_id="missing-task-id",
            title="New title",
        )


def test_mark_task_as_completed():
    """A pending task should be marked as completed."""
    task = add_task(
        title="Finish testing",
    )

    completed_task = set_task_status(
        task["id"],
        "Completed",
    )

    assert completed_task["status"] == "Completed"
    assert completed_task["completed_at"] is not None


def test_reopen_completed_task():
    """A completed task should be changed back to pending."""
    task = add_task(
        title="Reopen this task",
    )

    set_task_status(
        task["id"],
        "Completed",
    )

    reopened_task = set_task_status(
        task["id"],
        "Pending",
    )

    assert reopened_task["status"] == "Pending"
    assert reopened_task["completed_at"] is None


def test_toggle_task_status():
    """Toggling should switch the task status."""
    task = add_task(
        title="Toggle task",
    )

    completed_task = toggle_task_status(task["id"])
    pending_task = toggle_task_status(task["id"])

    assert completed_task["status"] == "Completed"
    assert pending_task["status"] == "Pending"


def test_reschedule_task():
    """A task should move to a new due date."""
    task = add_task(
        title="Reschedule meeting",
        due_date=date.today(),
    )

    new_due_date = date.today() + timedelta(days=7)

    rescheduled_task = reschedule_task(
        task["id"],
        new_due_date,
    )

    assert (
        rescheduled_task["due_date"]
        == new_due_date.isoformat()
    )


def test_delete_task():
    """An existing task should be deleted."""
    task = add_task(
        title="Delete this task",
    )

    result = delete_task(task["id"])

    assert result is True
    assert get_task(task["id"]) is None
    assert get_all_tasks() == []


def test_delete_missing_task():
    """Deleting a missing task should produce an error."""
    with pytest.raises(
        ValueError,
        match="Task not found",
    ):
        delete_task("missing-task-id")


def test_filter_tasks_by_status():
    """Tasks should be filterable by completion status."""
    first_task = add_task(
        title="Completed task",
    )

    add_task(
        title="Pending task",
    )

    set_task_status(
        first_task["id"],
        "Completed",
    )

    completed_tasks = filter_tasks(
        status="Completed",
    )

    pending_tasks = filter_tasks(
        status="Pending",
    )

    assert len(completed_tasks) == 1
    assert completed_tasks[0]["title"] == "Completed task"

    assert len(pending_tasks) == 1
    assert pending_tasks[0]["title"] == "Pending task"


def test_filter_tasks_by_priority():
    """Tasks should be filterable by priority."""
    add_task(
        title="High-priority task",
        priority="High",
    )

    add_task(
        title="Low-priority task",
        priority="Low",
    )

    high_priority_tasks = filter_tasks(
        priority="High",
    )

    assert len(high_priority_tasks) == 1
    assert high_priority_tasks[0]["priority"] == "High"


def test_filter_tasks_by_date():
    """Tasks should be filterable by due date."""
    today = date.today()
    tomorrow = today + timedelta(days=1)

    add_task(
        title="Today's task",
        due_date=today,
    )

    add_task(
        title="Tomorrow's task",
        due_date=tomorrow,
    )

    today_tasks = filter_tasks(
        selected_date=today,
    )

    assert len(today_tasks) == 1
    assert today_tasks[0]["title"] == "Today's task"


def test_filter_tasks_by_search_term():
    """Search should check task titles and descriptions."""
    add_task(
        title="Prepare monthly report",
        description="Compile sales results.",
    )

    add_task(
        title="Contact supplier",
        description="Request the latest price list.",
    )

    title_results = filter_tasks(
        search_term="monthly",
    )

    description_results = filter_tasks(
        search_term="price list",
    )

    assert len(title_results) == 1
    assert title_results[0]["title"] == "Prepare monthly report"

    assert len(description_results) == 1
    assert description_results[0]["title"] == "Contact supplier"


def test_get_overdue_tasks():
    """Only pending tasks with past dates should be overdue."""
    yesterday = date.today() - timedelta(days=1)
    tomorrow = date.today() + timedelta(days=1)

    overdue_task = add_task(
        title="Overdue task",
        due_date=yesterday,
    )

    completed_overdue_task = add_task(
        title="Completed overdue task",
        due_date=yesterday,
    )

    add_task(
        title="Future task",
        due_date=tomorrow,
    )

    set_task_status(
        completed_overdue_task["id"],
        "Completed",
    )

    overdue_tasks = get_overdue_tasks()

    assert len(overdue_tasks) == 1
    assert overdue_tasks[0]["id"] == overdue_task["id"]


def test_task_statistics():
    """Task statistics should return accurate totals."""
    yesterday = date.today() - timedelta(days=1)

    completed_task = add_task(
        title="Completed task",
    )

    add_task(
        title="Pending task",
    )

    add_task(
        title="Overdue task",
        due_date=yesterday,
    )

    set_task_status(
        completed_task["id"],
        "Completed",
    )

    statistics = get_task_statistics()

    assert statistics["total"] == 3
    assert statistics["completed"] == 1
    assert statistics["pending"] == 2
    assert statistics["overdue"] == 1
    assert statistics["completion_rate"] == 33