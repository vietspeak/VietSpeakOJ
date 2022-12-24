import io
from typing import List

from flask import Flask, flash, redirect, render_template, request
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from config.config import MAX_NUMBER_OF_SUBMISSIONS_IN_QUEUE
from model.model import FileSource, Submission, Task, TaskLevel, User, engine
from utils.timezone_converter import timezone_converter
from website.app import COLOR_MAP

app = Flask(__name__, template_folder="templates")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1000 * 1000


@app.route("/test_submission", methods=["GET", "POST"])
def test_submission():
    if request.method == "POST":
        # check if the post request has the file part
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files["file"]
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)
        if file:
            blob_file = io.BytesIO()
            file.save(blob_file)

            with Session(engine) as session:
                row = Submission(
                    source=FileSource.WEBSITE, audio_file=blob_file.getvalue()
                )
                session.add(row)
                session.commit()

    return render_template("test_submission.html")


@app.route("/test_task", methods=["GET", "POST"])
def test_task():
    if request.method == "POST":
        # check if the post request has the file part
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files["file"]
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        task_number = int(request.values["task_number"])
        level = getattr(TaskLevel, request.values["level"].upper())
        title = request.values.get("task_title", "")
        audio_link = request.values.get("task_audio_link", "")
        sample_transcript = request.values["sample_transcript"]

        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)
        if file:
            blob_file = io.BytesIO()
            file.save(blob_file)

            with Session(engine) as session:
                row = Task(
                    task_number=task_number,
                    level=level,
                    sample_transcript=sample_transcript,
                    audio_file=blob_file.getvalue(),
                    audio_link=audio_link,
                    title=title
                )
                session.add(row)
                session.commit()

    return render_template("test_task.html")


@app.route("/edit_tasks", methods=["GET", "POST"])
def edit_tasks():
    if request.method == "POST":
        task_id = int(request.values.get("task_id", 0))
        with Session(engine) as session:
            stmt = select(Task).where(Task.id == task_id)
            task: Task = session.scalar(stmt)
            if task:
                task.task_number = int(request.values.get("task_number", 0))
                task.level = TaskLevel._member_map_[request.values.get("task_level")]
                task.title = request.values.get("task_title", "")
                task.sample_transcript = request.values.get("transcript", "")
                task.audio_link = request.values.get("task_audio_link", "")
            session.commit()

        return "Done!"

    result = ["<html>"]
    with Session(engine) as session:
        stmt = select(Task).order_by(desc(Task.task_number))

        for task in session.scalars(stmt):
            task: Task
            result.append(
                f"""
                <form id="form{task.id}" action="/edit_tasks" method="post">
                    ID: <input type="text" name="task_id" value="{task.id}"></input><br>
                    Task number: <input type="text" name="task_number" value="{task.task_number if task.task_number is not None else ''}"></input><br>
                    Level: <input type="text" name="task_level" value="{str(task.level).split(".")[1]}"></input><br>
                    Title: <input type="text" name="task_title" value="{task.title if task.title is not None else ''}"></input><br>
                    Audio Link: <input type="text" name="task_audio_link" value="{task.audio_link if task.audio_link is not None else ""}"></input><br>
                    Sample transcript: <textarea name="transcript" form="form{task.id}">{task.sample_transcript if task.sample_transcript is not None else ''}</textarea><br>
                    <input type="submit" value="Edit Task ID {task.id}"></input>
                </form>
            """
            )

    result.append("</html>")
    return "".join(result)


@app.route("/regrade_submissions", methods=["GET", "POST"])
def regrade_submissions():
    if request.method == "POST":
        submission_id = int(request.values.get("submit").split(" ")[1])
        with Session(engine) as session:
            stmt = select(Submission).where(Submission.id == submission_id)
            submission: Submission = session.scalar(stmt)
            if submission:
                submission.transcript = None
                submission.task_id = None
                submission.score = None
            session.commit()

        return "Done!"

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
                <th>Action</th>
            </tr>
    """
    ]
    with Session(engine) as session:
        find_submission_stmt = (
            select(Submission)
            .where(Submission.source == FileSource.SLACK)
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

            find_user_stmt = select(User).where(User.id == submission.user_id)
            user: User = session.scalar(find_user_stmt)

            result.append(
                f"""
            <tr style="background-color:{task_color}">
                <td>{submission.id}</td>
                <td>{user.slack_id}</td>
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
                <td><form action="/regrade_submissions" method="post"><input type="submit" name="submit" value="Regrade {submission.id}"></form>
            </tr>
            """
            )

    result.append("</table>")
    html_source = "\n".join(result)
    return render_template("header.html") + html_source + render_template("footer.html")
