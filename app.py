from website.app import app
import os

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=os.environ.get("USER_PORT", 5000))
