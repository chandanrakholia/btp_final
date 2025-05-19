from flask import Flask, jsonify
from flask_cors import CORS
import datetime
import os
import re
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from main import detect_phishing_from_screenshot  # Your detection logic

app = Flask(__name__)
CORS(app)  # Enable CORS

# Prepare output file
RESULTS_FILE = "phishing_detection_results.txt"
with open(RESULTS_FILE, "w") as f:
    f.write("URL\tResult\n")

# Sanitize file name for screenshot
def sanitize_filename(url):
    return re.sub(r"[^\w.-]", "_", url) + ".png"

# Take screenshot using headless Chrome
def take_screenshot(url):
    filename = sanitize_filename(url)
    output_dir = "screenshots"
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        time.sleep(2)
        driver.save_screenshot(path)
        return path
    except Exception as e:
        print(f"❌ Error capturing screenshot for {url}: {e}")
        return None
    finally:
        driver.quit()

def process_csv():
    try:
        df = pd.read_csv("verified_online.csv")
        for index, row in df.iterrows():
            url = row.get("url")
            if not url:
                continue

            print(f"⏳ Processing: {url}")
            screenshot_path = take_screenshot(url)
            if not screenshot_path:
                result_text = "screenshot_error"
            else:
                try:
                    result = detect_phishing_from_screenshot(url, screenshot_path)
                    result_text = str(result.get("verification_result", "not_detected"))
                except Exception as e:
                    print(f"❌ Detection error for {url}: {e}")
                    result_text = "detection_error"

            # Write result to text file
            with open(RESULTS_FILE, "a") as f:
                f.write(f"{url}\t{result_text}\n")

        return jsonify({"status": "completed", "output_file": RESULTS_FILE})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

process_csv()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3001, debug=True)