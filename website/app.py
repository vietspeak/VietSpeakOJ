import io

from flask import Flask, flash, redirect, request
from sqlalchemy.orm import Session

from model.model import AudioFile, FileSource, engine

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1000 * 1000


@app.route("/", methods=["GET", "POST"])
def upload_file():
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
                row = AudioFile(source=FileSource.WEBSITE, content=blob_file.getvalue())
                session.add(row)
                session.commit()

    return """
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    """
