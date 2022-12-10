import datetime
import io
from typing import List

import pytz
from flask import Flask, render_template
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from config.config import MAX_NUMBER_OF_SUBMISSIONS_IN_QUEUE
from model.model import Submission, Task, engine, TaskLevel
from utils.timezone_converter import timezone_converter

app = Flask(__name__, template_folder="templates")

COLOR_MAP = {
    TaskLevel.YELLOW: "gold",
    TaskLevel.GREEN: "LimeGreen",
    TaskLevel.BLUE: "Aqua",
    TaskLevel.RED: "Salmon"
}

@app.route("/submission_queue")
def submission_queue():
    result: List[str] = [
        """
        <h1>Submission Queue</h1>
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

    result.append("</table>")
    html_source = "\n".join(result)
    return render_template("header.html") + html_source + render_template("footer.html")
