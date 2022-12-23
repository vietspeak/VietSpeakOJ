import io

from flask import Flask, flash, redirect, render_template, request
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from model.model import FileSource, Submission, Task, TaskLevel, engine

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
            task = session.scalar(stmt)
            if task:
                task.task_number = int(request.values.get("task_number", 0))
                task.level = TaskLevel._member_map_[request.values.get("task_level")]
                task.title = request.values.get("task_title", "")
                task.sample_transcript = request.values.get("transcript", "")
            session.commit()
        
        return "Done!"

            
    result = ["<html>"]
    with Session(engine) as session:
        stmt = select(Task).order_by(desc(Task.task_number))
        
        for task in session.scalars(stmt):
            task: Task
            result.append(f"""
                <form id="form{task.id}" action="/edit_tasks" method="post">
                    ID: <input type="text" name="task_id" value="{task.id}"></input><br>
                    Task number: <input type="text" name="task_number" value="{task.task_number if task.task_number is not None else ''}"></input><br>
                    Level: <input type="text" name="task_level" value="{str(task.level).split(".")[1]}"></input><br>
                    Title: <input type="text" name="task_title" value="{task.title if task.title is not None else ''}"></input><br>
                    Sample transcript: <textarea name="transcript" form="form{task.id}">{task.sample_transcript if task.sample_transcript is not None else ''}</textarea><br>
                    <input type="submit" value="Edit Task ID {task.id}"></input>
                </form>
            """)

    result.append("</html>")
    return "".join(result)