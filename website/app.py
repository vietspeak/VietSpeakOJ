import datetime
import io
from typing import List

import pytz
from flask import Flask, render_template, request
from sqlalchemy import desc, select, and_
from sqlalchemy.orm import Session

from config.config import MAX_NUMBER_OF_SUBMISSIONS_IN_QUEUE
from model.model import Submission, Task, TaskLevel, engine
from utils.timezone_converter import timezone_converter

app = Flask(__name__, template_folder="templates")

COLOR_MAP = {
    TaskLevel.YELLOW: "gold",
    TaskLevel.GREEN: "LimeGreen",
    TaskLevel.BLUE: "Aqua",
    TaskLevel.RED: "Salmon",
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
        render_template("header.html")
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
        task_stmt = select(Task).where(and_(Task.task_number == task_number,Task.level == task_level))
        task_info: Task = session.scalar(task_stmt)
        print(task_info)

        task_transcript = "".join(f"<p>{x}</p>" for x in task_info.sample_transcript.split("\n")) if task_info else ""

        return (
            render_template("header.html")
            + render_template(
                "tasks_body.html",
                task_number=str(task_number),
                previous_task_link=previous_task_link,
                next_task_link=next_task_link,
                task_level=task_level_str,
                task_link="",
                task_transcript=task_transcript
            ) + render_template("footer.html")
        )


@app.route("/status")
def submission_queue():
    result: List[str] = [
        """
        <div class="container"><h1>Status</h1>
        <table class="table">
            <tr>
                <th>#</th>
                <th>User ID</th>
                <th>Task</th>
                <th>Level</th>
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
                task_color: str = COLOR_MAP[task_info.level]
            else:
                task_info: Task = None
                task_color: str = "gray"

            result.append(
                f"""
            <tr style="background-color:{task_color}">
                <td>{submission.id}</td>
                <td>{submission.user_id}</td>
            """
            )

            if task_info:
                result.append(
                    f"<td>{task_info.task_number}</td><td>{str(task_info.level).split('.')[1]}</td>"
                )
            else:
                result.append("<td></td>" * 2)

            result.append(
                f"""
                <td>{timezone_converter(str(submission.created_time))}</td>
            </tr>
            """
            )

    result.append("</table></div>")
    html_source = "\n".join(result)
    return render_template("header.html") + html_source + render_template("footer.html")
