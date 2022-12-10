import io

from flask import Flask, flash, redirect, render_template, request
from sqlalchemy.orm import Session

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
