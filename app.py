from datetime import date, datetime
from html import escape
from pathlib import Path

import streamlit as st

from auth import require_authentication, show_account_menu
from goal_manager import (
    add_goal,
    delete_goal,
    get_goal_statistics,
    get_goals,
    get_week_end,
    get_week_start,
    mark_goal_completed,
    reschedule_goal,
    update_goal,
)
from task_manager import (
    add_task,
    delete_task,
    get_overdue_tasks,
    get_task_statistics,
    get_tasks,
    get_tasks_due_on,
    mark_task_completed,
    reschedule_task,
    update_task,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="TaskFlow",
    page_icon="T",
    layout="wide",
    initial_sidebar_state="collapsed",
)


BASE_DIR = Path(__file__).resolve().parent
CSS_FILE = BASE_DIR / "assets" / "style.css"

PRIORITY_OPTIONS = ["Low", "Medium", "High"]


# =========================================================
# GENERAL HELPERS
# =========================================================

def load_css(file_path: Path) -> None:
    """Load the custom CSS file."""

    try:
        with open(file_path, encoding="utf-8") as css_file:
            st.markdown(
                f"<style>{css_file.read()}</style>",
                unsafe_allow_html=True,
            )

    except FileNotFoundError:
        st.warning(
            f"The custom stylesheet could not be found at "
            f"{file_path}."
        )


def render_html(html_content: str) -> None:
    """
    Render multiline HTML without Streamlit displaying
    individual tags as code.
    """

    cleaned_html = " ".join(
        line.strip()
        for line in html_content.splitlines()
        if line.strip()
    )

    st.markdown(
        cleaned_html,
        unsafe_allow_html=True,
    )


def parse_date(date_value) -> date:
    """Convert a saved value into a date object."""

    if isinstance(date_value, datetime):
        return date_value.date()

    if isinstance(date_value, date):
        return date_value

    if isinstance(date_value, str):
        try:
            return date.fromisoformat(date_value[:10])
        except ValueError:
            return date.today()

    return date.today()


def save_flash_message(
    message: str,
    message_type: str = "success",
) -> None:
    """Save a message to display after an application rerun."""

    st.session_state["flash_message"] = {
        "message": message,
        "type": message_type,
    }


def display_flash_message() -> None:
    """Display and remove the saved flash message."""

    flash_message = st.session_state.pop(
        "flash_message",
        None,
    )

    if flash_message is None:
        return

    message = flash_message["message"]
    message_type = flash_message["type"]

    if message_type == "error":
        st.error(message)

    elif message_type == "warning":
        st.warning(message)

    else:
        st.success(message)


def run_action(
    action,
    success_message: str,
    message_type: str = "success",
) -> None:
    """Run a database action and handle its feedback."""

    try:
        action()

        save_flash_message(
            success_message,
            message_type,
        )

        st.rerun()

    except (
        ValueError,
        RuntimeError,
        TypeError,
    ) as error:
        st.error(str(error))


# =========================================================
# TASK CARD
# =========================================================

def display_task_card(task: dict) -> None:
    """Display one task and its management controls."""

    task_id = task["id"]

    task_title = escape(
        task.get("title", "Untitled task")
    )

    task_description = escape(
        task.get("description", "")
    )

    task_priority = task.get(
        "priority",
        "Medium",
    )

    task_completed = task.get(
        "completed",
        False,
    )

    task_due_date = parse_date(
        task.get("due_date")
    )

    if task_completed:
        status_text = "Completed"
        status_class = "completed"

    else:
        status_text = "Pending"
        status_class = "pending"

    if (
        not task_completed
        and task_due_date < date.today()
    ):
        date_text = (
            "Overdue since "
            f"{task_due_date.strftime('%d %b %Y')}"
        )

        date_class = "overdue"

    elif task_due_date == date.today():
        date_text = "Due today"
        date_class = "today"

    else:
        date_text = (
            f"Due {task_due_date.strftime('%d %b %Y')}"
        )

        date_class = "upcoming"

    if task_description:
        description_html = (
            '<p class="task-description">'
            f"{task_description}"
            "</p>"
        )

    else:
        description_html = (
            '<p class="task-description empty">'
            "No description provided."
            "</p>"
        )

    render_html(
        f"""
        <div class="task-card">
            <div class="task-card-header">
                <div class="task-title-area">
                    <h3>{task_title}</h3>
                    {description_html}
                </div>

                <span class="status-badge {status_class}">
                    {status_text}
                </span>
            </div>

            <div class="task-meta">
                <span class="priority-badge
                    {task_priority.lower()}">
                    {task_priority} priority
                </span>

                <span class="date-badge {date_class}">
                   ">
                    {date_text}
                </span>
            </div>
        </div>
        """
    )

    status_column, date_column, reschedule_column = st.columns(
        [1, 1.3, 1],
        gap="small",
    )

    with status_column:
        status_button_text = (
            "Reopen task"
            if task_completed
            else "Mark complete"
        )

        if st.button(
            status_button_text,
            key=f"task_status_{task_id}",
            type=(
                "secondary"
                if task_completed
                else "primary"
            ),
            use_container_width=True,
        ):
            run_action(
                lambda: mark_task_completed(
                    task_id,
                    not task_completed,
                ),
                (
                    "Task reopened successfully."
                    if task_completed
                    else "Task marked as completed."
                ),
            )

    with date_column:
        new_due_date = st.date_input(
            "New task date",
            value=task_due_date,
            key=f"reschedule_date_{task_id}",
            label_visibility="collapsed",
        )

    with reschedule_column:
        if st.button(
            "Reschedule",
            key=f"reschedule_task_{task_id}",
            use_container_width=True,
        ):
            run_action(
                lambda: reschedule_task(
                    task_id,
                    new_due_date,
                ),
                "Task rescheduled successfully.",
            )

    with st.expander("Edit or delete task"):
        with st.form(f"edit_task_form_{task_id}"):
            edited_title = st.text_input(
                "Task title",
                value=task.get("title", ""),
                max_chars=150,
                key=f"edit_title_{task_id}",
            )

            edited_description = st.text_area(
                "Description",
                value=task.get("description", ""),
                max_chars=500,
                key=f"edit_description_{task_id}",
            )

            edit_date_column, edit_priority_column = st.columns(
                2
            )

            with edit_date_column:
                edited_due_date = st.date_input(
                    "Due date",
                    value=task_due_date,
                    key=f"edit_due_date_{task_id}",
                )

            with edit_priority_column:
                if task_priority in PRIORITY_OPTIONS:
                    priority_index = (
                        PRIORITY_OPTIONS.index(
                            task_priority
                        )
                    )
                else:
                    priority_index = 1

                edited_priority = st.selectbox(
                    "Priority",
                    PRIORITY_OPTIONS,
                    index=priority_index,
                    key=f"edit_priority_{task_id}",
                )

            save_changes = st.form_submit_button(
                "Save changes",
                type="primary",
                use_container_width=True,
            )

        if save_changes:
            run_action(
                lambda: update_task(
                    task_id=task_id,
                    title=edited_title,
                    description=edited_description,
                    due_date=edited_due_date,
                    priority=edited_priority,
                ),
                "Task updated successfully.",
            )

        render_html(
            '<div class="delete-divider"></div>'
        )

        st.warning(
            "Deleting this task is permanent."
        )

        confirm_delete = st.checkbox(
            "I want to delete this task.",
            key=f"confirm_task_delete_{task_id}",
        )

        if st.button(
            "Delete task",
            key=f"delete_task_{task_id}",
            disabled=not confirm_delete,
            use_container_width=True,
        ):
            run_action(
                lambda: delete_task(task_id),
                "Task deleted successfully.",
                "warning",
            )


# =========================================================
# GOAL CARD
# =========================================================

def display_goal_card(goal: dict) -> None:
    """Display one weekly goal and its controls."""

    goal_id = goal["id"]

    goal_title = escape(
        goal.get("title", "Untitled goal")
    )

    goal_description = escape(
        goal.get("description", "")
    )

    goal_completed = goal.get(
        "completed",
        False,
    )

    goal_week_start = parse_date(
        goal.get("week_start")
    )

    if goal.get("target_date"):
        goal_target_date = parse_date(
            goal["target_date"]
        )
    else:
        goal_target_date = None

    if goal_completed:
        goal_status = "Completed"
        goal_status_class = "completed"

    else:
        goal_status = "In progress"
        goal_status_class = "pending"

    if goal_target_date:
        target_text = (
            "Target date: "
            f"{goal_target_date.strftime('%A, %d %b %Y')}"
        )

    else:
        target_text = "No target date selected"

    if goal_description:
        description_html = (
            f"<p>{goal_description}</p>"
        )

    else:
        description_html = (
            "<p>No description provided.</p>"
        )

    render_html(
        f"""
        <div class="goal-card">
            <div class="goal-card-header">
                <div>
                    <h3>{goal_title}</h3>
                    {description_html}
                </div>

                <span class="status-badge
                    {goal_status_class}">
                    {goal_status}
                </span>
            </div>

            <div class="goal-meta">
                <span>
                    Week beginning
                    {goal_week_start.strftime('%d %b %Y')}
                </span>

                <span>{target_text}</span>
            </div>
        </div>
        """
    )

    status_column, schedule_column = st.columns(
        2,
        gap="small",
    )

    with status_column:
        status_button_text = (
            "Mark incomplete"
            if goal_completed
            else "Mark complete"
        )

        if st.button(
            status_button_text,
            key=f"goal_status_{goal_id}",
            type=(
                "secondary"
                if goal_completed
                else "primary"
            ),
            use_container_width=True,
        ):
            run_action(
                lambda: mark_goal_completed(
                    goal_id,
                    not goal_completed,
                ),
                (
                    "Goal marked as incomplete."
                    if goal_completed
                    else "Goal completed successfully."
                ),
            )

    with schedule_column:
        with st.popover(
            "Reschedule goal",
            use_container_width=True,
        ):
            new_goal_week = st.date_input(
                "Select a date in the new week",
                value=goal_week_start,
                key=f"new_goal_week_{goal_id}",
            )

            new_week_start = get_week_start(
                new_goal_week
            )

            new_week_end = get_week_end(
                new_goal_week
            )

            new_target_date = st.date_input(
                "New target date",
                value=new_week_start,
                min_value=new_week_start,
                max_value=new_week_end,
                key=f"new_goal_target_{goal_id}",
            )

            if st.button(
                "Confirm reschedule",
                key=(
                    f"confirm_goal_reschedule_"
                    f"{goal_id}"
                ),
                type="primary",
                use_container_width=True,
            ):
                run_action(
                    lambda: reschedule_goal(
                        goal_id,
                        new_goal_week,
                        new_target_date,
                    ),
                    "Weekly goal rescheduled.",
                )

    with st.expander("Edit or delete goal"):
        with st.form(f"edit_goal_form_{goal_id}"):
            edited_goal_title = st.text_input(
                "Goal title",
                value=goal.get("title", ""),
                max_chars=150,
                key=f"edit_goal_title_{goal_id}",
            )

            edited_goal_description = st.text_area(
                "Description",
                value=goal.get("description", ""),
                max_chars=500,
                key=f"edit_goal_description_{goal_id}",
            )

            save_goal_changes = st.form_submit_button(
                "Save changes",
                type="primary",
                use_container_width=True,
            )

        if save_goal_changes:
            run_action(
                lambda: update_goal(
                    goal_id=goal_id,
                    title=edited_goal_title,
                    description=edited_goal_description,
                ),
                "Weekly goal updated successfully.",
            )

        render_html(
            '<div class="delete-divider"></div>'
        )

        st.warning(
            "Deleting this weekly goal is permanent."
        )

        confirm_goal_delete = st.checkbox(
            "I want to delete this weekly goal.",
            key=f"confirm_goal_delete_{goal_id}",
        )

        if st.button(
            "Delete weekly goal",
            key=f"delete_goal_{goal_id}",
            disabled=not confirm_goal_delete,
            use_container_width=True,
        ):
            run_action(
                lambda: delete_goal(goal_id),
                "Weekly goal deleted.",
                "warning",
            )


# =========================================================
# START APPLICATION
# =========================================================

load_css(CSS_FILE)

require_authentication()
show_account_menu()


# =========================================================
# HEADER
# =========================================================

render_html(
    """
    <div class="app-header">
        <div class="header-content">
            <span class="eyebrow">
                PERSONAL PRODUCTIVITY
            </span>

            <h1>TaskFlow</h1>

            <p>
                Plan your tasks, manage your week,
                and track your progress.
            </p>
        </div>
    </div>
    """
)

display_flash_message()


# =========================================================
# DASHBOARD STATISTICS
# =========================================================

try:
    statistics = get_task_statistics()
    overdue_tasks = get_overdue_tasks()
    statistics["overdue"] = len(overdue_tasks)

except (
    ValueError,
    RuntimeError,
    TypeError,
) as error:
    st.error(
        f"Your task data could not be loaded: {error}"
    )
    st.stop()


metric_one, metric_two, metric_three, metric_four = st.columns(
    4
)

with metric_one:
    st.metric(
        "Total tasks",
        statistics["total"],
    )

with metric_two:
    st.metric(
        "Pending",
        statistics["pending"],
    )

with metric_three:
    st.metric(
        "Completed",
        statistics["completed"],
    )

with metric_four:
    st.metric(
        "Completion rate",
        f'{statistics["completion_rate"]}%',
    )


# =========================================================
# NAVIGATION
# =========================================================

dashboard_tab, tasks_tab, goals_tab = st.tabs(
    [
        "Dashboard",
        "Manage tasks",
        "Weekly goals",
    ]
)


# =========================================================
# DASHBOARD TAB
# =========================================================

with dashboard_tab:
    form_column, summary_column = st.columns(
        [1.25, 0.75],
        gap="large",
    )

    with form_column:
        st.markdown(
            '<p class="section-label">'
            "ADD A NEW TASK"
            "</p>",
            unsafe_allow_html=True,
        )

        with st.form(
            "add_task_form",
            clear_on_submit=True,
        ):
            task_title = st.text_input(
                "Task title",
                placeholder="What needs to be completed?",
                max_chars=150,
            )

            task_description = st.text_area(
                "Description",
                placeholder="Add useful task details.",
                max_chars=500,
            )

            due_date_column, priority_column = st.columns(
                2
            )

            with due_date_column:
                task_due_date = st.date_input(
                    "Due date",
                    value=date.today(),
                )

            with priority_column:
                task_priority = st.selectbox(
                    "Priority",
                    PRIORITY_OPTIONS,
                    index=1,
                )

            create_task = st.form_submit_button(
                "Add task",
                type="primary",
                use_container_width=True,
            )

        if create_task:
            run_action(
                lambda: add_task(
                    title=task_title,
                    description=task_description,
                    due_date=task_due_date,
                    priority=task_priority,
                ),
                "Task added successfully.",
            )

    with summary_column:
        st.markdown(
            '<p class="section-label">'
            "TODAY"
            "</p>",
            unsafe_allow_html=True,
        )

        try:
            today_tasks = get_tasks_due_on(
                date.today()
            )

        except (
            ValueError,
            RuntimeError,
            TypeError,
        ) as error:
            st.error(str(error))
            today_tasks = []

        pending_today = sum(
            1
            for task in today_tasks
            if not task.get("completed", False)
        )

        completed_today = sum(
            1
            for task in today_tasks
            if task.get("completed", False)
        )

        render_html(
            f"""
            <div class="today-card">
                <span class="today-date">
                    {date.today().strftime('%A, %d %B')}
                </span>

                <strong>{pending_today}</strong>

                <p>
                    {
                        "task"
                        if pending_today == 1
                        else "tasks"
                    }
                    remaining today
                </p>

                <div class="today-card-footer">
                    <span>
                        {completed_today} completed
                    </span>

                    <span>
                        {len(today_tasks)} scheduled
                    </span>
                </div>
            </div>
            """
        )

        if statistics["overdue"] > 0:
            overdue_word = (
                "task"
                if statistics["overdue"] == 1
                else "tasks"
            )

            st.warning(
                f'{statistics["overdue"]} overdue '
                f"{overdue_word} require attention."
            )

        else:
            st.success(
                "You have no overdue tasks."
            )

    st.markdown(
        '<p class="section-label upcoming-heading">'
        "UPCOMING TASKS"
        "</p>",
        unsafe_allow_html=True,
    )

    try:
        pending_tasks = get_tasks(
            completed=False
        )

        upcoming_tasks = [
            task
            for task in pending_tasks
            if parse_date(
                task.get("due_date")
            ) >= date.today()
        ][:5]

    except (
        ValueError,
        RuntimeError,
        TypeError,
    ) as error:
        st.error(str(error))
        upcoming_tasks = []

    if upcoming_tasks:
        for task in upcoming_tasks:
            upcoming_title = escape(
                task.get(
                    "title",
                    "Untitled task",
                )
            )

            upcoming_priority = escape(
                task.get(
                    "priority",
                    "Medium",
                )
            )

            upcoming_date = parse_date(
                task.get("due_date")
            ).strftime("%d %b %Y")

            render_html(
                f"""
                <div class="upcoming-task">
                    <div>
                        <strong>
                            {upcoming_title}
                        </strong>

                        <span>
                            {upcoming_date}
                        </span>
                    </div>

                    <span class="priority-badge
                        {upcoming_priority.lower()}">
                        {upcoming_priority}
                    </span>
                </div>
                """
            )

    else:
        st.info(
            "No upcoming tasks. "
            "Add a task to begin planning."
        )


# =========================================================
# MANAGE TASKS TAB
# =========================================================

with tasks_tab:
    st.markdown(
        '<p class="section-label">'
        "FIND AND MANAGE TASKS"
        "</p>",
        unsafe_allow_html=True,
    )

    search_term = st.text_input(
        "Search tasks",
        placeholder="Search by title or description",
        label_visibility="collapsed",
    )

    status_column, priority_column, date_column = st.columns(
        3
    )

    with status_column:
        status_filter = st.selectbox(
            "Status",
            [
                "All",
                "Pending",
                "Completed",
            ],
        )

    with priority_column:
        priority_filter = st.selectbox(
            "Priority",
            [
                "All",
                *PRIORITY_OPTIONS,
            ],
        )

    with date_column:
        filter_by_date = st.checkbox(
            "Filter by date"
        )

        selected_date = None

        if filter_by_date:
            selected_date = st.date_input(
                "Select date",
                value=date.today(),
                key="task_date_filter",
            )

    try:
        all_tasks = get_tasks()
        filtered_tasks = []

        for task in all_tasks:
            task_completed = task.get(
                "completed",
                False,
            )

            task_priority = task.get(
                "priority",
                "Medium",
            )

            task_date = parse_date(
                task.get("due_date")
            )

            searchable_text = (
                f'{task.get("title", "")} '
                f'{task.get("description", "")}'
            ).lower()

            status_matches = (
                status_filter == "All"
                or (
                    status_filter == "Completed"
                    and task_completed
                )
                or (
                    status_filter == "Pending"
                    and not task_completed
                )
            )

            priority_matches = (
                priority_filter == "All"
                or task_priority == priority_filter
            )

            date_matches = (
                selected_date is None
                or task_date == selected_date
            )

            search_matches = (
                not search_term.strip()
                or search_term.strip().lower()
                in searchable_text
            )

            if (
                status_matches
                and priority_matches
                and date_matches
                and search_matches
            ):
                filtered_tasks.append(task)

    except (
        ValueError,
        RuntimeError,
        TypeError,
    ) as error:
        st.error(str(error))
        filtered_tasks = []

    task_word = (
        "task"
        if len(filtered_tasks) == 1
        else "tasks"
    )

    render_html(
        f"""
        <div class="results-header">
            {len(filtered_tasks)} {task_word} found
        </div>
        """
    )

    if filtered_tasks:
        for task in filtered_tasks:
            display_task_card(task)

    else:
        st.info(
            "No tasks match the selected filters."
        )


# =========================================================
# WEEKLY GOALS TAB
# =========================================================

with goals_tab:
    goal_form_column, goal_list_column = st.columns(
        [0.8, 1.2],
        gap="large",
    )

    with goal_form_column:
        st.markdown(
            '<p class="section-label">'
            "CREATE A WEEKLY GOAL"
            "</p>",
            unsafe_allow_html=True,
        )

        with st.form(
            "add_goal_form",
            clear_on_submit=True,
        ):
            goal_title = st.text_input(
                "Goal title",
                placeholder="What do you want to achieve?",
                max_chars=150,
            )

            goal_description = st.text_area(
                "Description",
                placeholder="Describe your weekly goal.",
                max_chars=500,
            )

            selected_week_date = st.date_input(
                "Select any date in the goal week",
                value=date.today(),
            )

            selected_week_start = get_week_start(
                selected_week_date
            )

            selected_week_end = get_week_end(
                selected_week_date
            )

            goal_target_date = st.date_input(
                "Target completion date",
                value=selected_week_date,
                min_value=selected_week_start,
                max_value=selected_week_end,
            )

            st.caption(
                "Goal week: "
                f"{selected_week_start.strftime('%d %b %Y')} "
                "to "
                f"{selected_week_end.strftime('%d %b %Y')}."
            )

            create_goal = st.form_submit_button(
                "Add weekly goal",
                type="primary",
                use_container_width=True,
            )

        if create_goal:
            run_action(
                lambda: add_goal(
                    title=goal_title,
                    description=goal_description,
                    week_start=selected_week_date,
                    target_date=goal_target_date,
                ),
                "Weekly goal added successfully.",
            )

    with goal_list_column:
        st.markdown(
            '<p class="section-label">'
            "VIEW WEEKLY GOALS"
            "</p>",
            unsafe_allow_html=True,
        )

        goal_week_date = st.date_input(
            "Select a week",
            value=date.today(),
            key="goal_week_filter",
        )

        selected_start = get_week_start(
            goal_week_date
        )

        selected_end = get_week_end(
            goal_week_date
        )

        render_html(
            f"""
            <div class="week-heading">
                <span>Selected week</span>

                <strong>
                    {selected_start.strftime('%d %b')}
                    to
                    {selected_end.strftime('%d %b %Y')}
                </strong>
            </div>
            """
        )

        try:
            weekly_goals = get_goals(
                week_start=goal_week_date
            )

            goal_statistics = get_goal_statistics(
                week_start=goal_week_date
            )

        except (
            ValueError,
            RuntimeError,
            TypeError,
        ) as error:
            st.error(str(error))

            weekly_goals = []

            goal_statistics = {
                "total": 0,
                "pending": 0,
                "completed": 0,
                "completion_rate": 0,
            }

        goal_metric_one, goal_metric_two, goal_metric_three = (
            st.columns(3)
        )

        with goal_metric_one:
            st.metric(
                "Goals",
                goal_statistics["total"],
            )

        with goal_metric_two:
            st.metric(
                "Completed",
                goal_statistics["completed"],
            )

        with goal_metric_three:
            st.metric(
                "Progress",
                f'{goal_statistics["completion_rate"]}%',
            )

        if weekly_goals:
            for goal in weekly_goals:
                display_goal_card(goal)

        else:
            st.info(
                "No goals have been created "
                "for this week."
            )


# =========================================================
# FOOTER
# =========================================================

render_html(
    """
    <div class="app-footer">
        <p>
            TaskFlow Personal Productivity Application
        </p>
    </div>
    """
)