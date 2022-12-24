from website.admin_app import app
import os

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=os.environ.get("ADMIN_PORT", 4000))
