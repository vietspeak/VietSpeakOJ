import datetime
import io
from typing import List
import os

import pytz
from flask import Flask, render_template, request, session, redirect, url_for
from sqlalchemy import desc, select, and_
from sqlalchemy.orm import Session
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    current_user,
    login_required,
    logout_user,
)

from config.config import MAX_NUMBER_OF_SUBMISSIONS_IN_QUEUE
from model.model import Submission, Task, TaskLevel, engine, User
from utils.timezone_converter import timezone_converter

app = Flask(__name__, template_folder="templates")
app.secret_key = bytes(
    os.environ.get("SECRET_KEY", '_5#y2L"F4Q8z\n\xec]/'), encoding="utf-8"
)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id: str):
    return User.get(user_id)


BUTTON_MAP = {
    TaskLevel.YELLOW: "warning",
    TaskLevel.GREEN: "success",
    TaskLevel.BLUE: "primary",
    TaskLevel.RED: "danger",
}

TASK_STR_MAP = {
    TaskLevel.YELLOW: "Yellow",
    TaskLevel.GREEN: "Green",
    TaskLevel.BLUE: "Blue",
    TaskLevel.RED: "Red",
}


def get_max_task_number():
    with Session(engine) as session:
        stmt = """
            SELECT MAX(task_number)
            FROM tasks;
        """

        result = next(session.execute(stmt))
        return result[0]


def check_if_task_is_available(task_number):
    with Session(engine) as session:
        stmt = select(Task).where(Task.task_number == task_number)
        result = next(session.scalars(stmt), None)
        return result is not None


@app.route("/")
def home_page():
    return (
        render_template("header.html", page_title="Home")
        + render_template("home_body.html")
        + render_template("footer.html")
    )


@app.route("/tasks", methods=["GET"])
def tasks_page():
    task_number = int(request.values.get("number", get_max_task_number()))

    previous_task_link = (
        f"""
        <a href="/tasks?number={task_number-1}">&#8592; Task {task_number-1}</a>
    """
        if check_if_task_is_available(task_number - 1)
        else ""
    )

    next_task_link = (
        f"""
        <a href="/tasks?number={task_number+1}">Task {task_number+1} &rarr;</a>
    """
        if check_if_task_is_available(task_number + 1)
        else ""
    )

    task_level_str = request.values.get("level", "Yellow")
    task_level = TaskLevel._member_map_.get(task_level_str.upper(), TaskLevel.YELLOW)

    with Session(engine) as session:
        task_stmt = select(Task).where(
            and_(Task.task_number == task_number, Task.level == task_level)
        )
        task_info: Task = session.scalar(task_stmt)

        task_transcript = (
            "".join(f"<p>{x}</p>" for x in task_info.sample_transcript.split("\n"))
            if task_info
            else ""
        )
        task_link = task_info.audio_link if task_info and task_info.audio_link else ""
        task_title = task_info.title if task_info and task_info.title else ""

        for_login_user = []

        if current_user.is_authenticated:
            submission_stmt = (
                select(Submission)
                .where(
                    and_(
                        Submission.user_id == current_user.id,
                        Submission.task_id == task_info.id,
                    )
                )
                .order_by(desc(Submission.id))
                .limit(5)
            )
            result = session.scalars(submission_stmt)
            if result:
                for_login_user.append("""
                    <h2>Your Recent Submissions</h2>
                    <table class="table">
                        <tr>
                            <th>#</th>
                            <th>Score</th>
                            <th>When</th>
                        </tr>
                """)
                for sub in result:
                    sub: Submission

                    for_login_user.append(
                        f"""
                        <tr>
                            <td>{sub.id}</td>
                            <td>{(sub.score * 100):.2f}</td>
                            <td>{timezone_converter(str(sub.created_time))}</td>
                        </tr>
                    """
                    )

                for_login_user.append("</table>")
        for_login_user = "".join(for_login_user)

        return (
            render_template(
                "header.html",
                page_title=f"Task {task_number} {task_level_str} - {task_title}",
            )
            + render_template(
                "tasks_body.html",
                task_number=str(task_number),
                previous_task_link=previous_task_link,
                next_task_link=next_task_link,
                task_level=task_level_str,
                task_link=task_link,
                task_transcript=task_transcript,
                task_title=task_title,
                for_login_user=for_login_user,
            )
            + render_template("footer.html")
        )


@app.route("/status")
def submission_queue():
    result: List[str] = [
        """
        <div class="container"><h1>Status</h1>
        <table class="table">
            <tr>
                <th>#</th>
                <th>Task</th>
                <th>When</th>
            </tr>
    """
    ]
    with Session(engine) as session:
        find_submission_stmt = (
            select(Submission)
            .order_by(desc(Submission.id))
            .limit(MAX_NUMBER_OF_SUBMISSIONS_IN_QUEUE)
        )
        rows: List[Submission] = list(session.scalars(find_submission_stmt))
        for submission in rows:
            if submission.task_id:
                find_task_stmt = select(Task).where(Task.id == submission.task_id)
                task_info: Task = session.scalar(find_task_stmt)
                task_button: str = BUTTON_MAP[task_info.level]
            else:
                task_info: Task = None
                task_button: str = "secondary"

            result.append(
                f"""
            <tr>
                <td>{submission.id}</td>
            """
            )

            button_label = "UNKNOWN"
            if task_info:
                button_label = (
                    f"{str(task_info.level).split('.')[1]} {task_info.task_number}"
                )

            button_link = ""
            if task_info:
                button_link = f"/tasks?number={task_info.task_number}&level={TASK_STR_MAP[task_info.level]}"

            result.append(
                f"""
                    <td><a type="button" class="btn btn-{task_button}" href="{button_link}">{button_label}</a></td>
                """
            )

            result.append(
                f"""
                <td>{timezone_converter(str(submission.created_time))}</td>
            </tr>
            """
            )

    result.append("</table></div>")
    html_source = "\n".join(result)
    return (
        render_template("header.html", page_title="Status")
        + html_source
        + render_template("footer.html")
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    user_id = int(request.values.get("id", 0))
    password = request.values.get("password", "")

    with Session(engine) as session:
        user_stmt = select(User).where(
            and_(
                User.id == user_id,
                and_(User.password == password, User.is_eliminated == False),
            )
        )
        user: User = session.scalar(user_stmt)
        if user:
            login_user(user)

    return redirect(url_for("home_page"))


@app.route("/logout")
@login_required
def logout():
    with Session(engine) as session:
        user_stmt: User = select(User).where(User.id == current_user.id)
        user: User = session.scalar(user_stmt)
        user.password = User.generate_password()
        session.commit()
    logout_user()
    return redirect(url_for("home_page"))
