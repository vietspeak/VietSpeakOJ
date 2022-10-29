from website.app import app
import os

if __name__ == "__main__":
    app.run(debug=True, port=os.environ.get("ADMIN_PORT", 5000))
