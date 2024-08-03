import os

from website.add_task_app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=os.environ.get("ADMIN_PORT", 4000))
