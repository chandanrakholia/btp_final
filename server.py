from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
import os
import re
import base64
from main import detect_phishing_from_screenshot 
import time

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "screenshots"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def sanitize_filename(url):
    """Convert URL into a safe filename."""
    filename = re.sub(r"[^\w.-]", "_", url)
    return filename + ".png"

@app.route("/upload", methods=["POST"])
def upload_screenshot():
    try:
        start_time = time.time()
        data = request.get_json()
        image_data = data.get("image")
        url = data.get("url")
        filename = sanitize_filename(url)
        screenshot_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(screenshot_path, "wb") as f:
            f.write(base64.b64decode(image_data.split(",")[1]))

        print(f"Screenshot saved: {screenshot_path}\n")

        result = detect_phishing_from_screenshot(url, screenshot_path)

        print(result)
        end_time = time.time()
        print(f"Total Processing Time {end_time - start_time:.2f} seconds.\n")

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/", methods=["GET"])
def get():
    return jsonify(message="GET Welcome"), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3001, debug=True)