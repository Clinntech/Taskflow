import json
from pathlib import Path
from typing import Any


# Main project and data locations
PROJECT_DIRECTORY = Path(__file__).resolve().parent
DATA_DIRECTORY = PROJECT_DIRECTORY / "data"

TASKS_FILE = DATA_DIRECTORY / "tasks.json"
GOALS_FILE = DATA_DIRECTORY / "weekly_goals.json"


def save_json(file_path: Path, data: Any) -> None:
    """Save Python data to a JSON file."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with file_path.open("w", encoding="utf-8") as json_file:
            json.dump(
                data,
                json_file,
                indent=4,
                ensure_ascii=False,
            )

    except OSError as error:
        raise OSError(
            f"Could not save data to {file_path.name}."
        ) from error


def load_json(file_path: Path, default: Any) -> Any:
    """Load data from a JSON file."""
    if not file_path.exists():
        save_json(file_path, default)
        return default

    try:
        file_content = file_path.read_text(
            encoding="utf-8"
        ).strip()

        if not file_content:
            save_json(file_path, default)
            return default

        return json.loads(file_content)

    except json.JSONDecodeError as error:
        raise ValueError(
            f"{file_path.name} contains invalid JSON."
        ) from error

    except OSError as error:
        raise OSError(
            f"Could not read data from {file_path.name}."
        ) from error


def initialize_storage() -> None:
    """Create the data directory and required files."""
    DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)

    if not TASKS_FILE.exists():
        save_json(TASKS_FILE, [])

    if not GOALS_FILE.exists():
        save_json(GOALS_FILE, [])


def load_tasks() -> list[dict]:
    """Load all tasks from storage."""
    initialize_storage()
    tasks = load_json(TASKS_FILE, [])

    if not isinstance(tasks, list):
        raise ValueError("The tasks file must contain a list.")

    return tasks


def save_tasks(tasks: list[dict]) -> None:
    """Save all tasks to storage."""
    if not isinstance(tasks, list):
        raise TypeError("Tasks must be provided as a list.")

    initialize_storage()
    save_json(TASKS_FILE, tasks)


def load_weekly_goals() -> list[dict]:
    """Load all weekly goals from storage."""
    initialize_storage()
    goals = load_json(GOALS_FILE, [])

    if not isinstance(goals, list):
        raise ValueError(
            "The weekly goals file must contain a list."
        )

    return goals


def save_weekly_goals(goals: list[dict]) -> None:
    """Save all weekly goals to storage."""
    if not isinstance(goals, list):
        raise TypeError(
            "Weekly goals must be provided as a list."
        )

    initialize_storage()
    save_json(GOALS_FILE, goals)