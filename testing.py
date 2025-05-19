import pandas as pd
import requests
import base64
import time
from io import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Load your CSV
df = pd.read_csv("verified_online.csv")

# Ensure 'response' column exists
if 'response' not in df.columns:
    df['response'] = ""

# Set up headless Chrome browser
options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--window-size=1280,720')

driver = webdriver.Chrome(options=options)

def capture_screenshot(url):
    try:
        driver.get(url)
        time.sleep(6)  # Adjust if pages load slowly

        screenshot = driver.get_screenshot_as_png()
        image = Image.open(BytesIO(screenshot))
        
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return "data:image/png;base64," + img_base64
    except Exception as e:
        print(f"Screenshot error for {url}: {e}")
        return None

for idx, row in df.iterrows():
    # Skip if response already exists
    if pd.notna(row['response']) and str(row['response']).strip() != "":
        print(f"Skipping {row['url']} (already processed)")
        continue

    url = row['url']
    print(f"Processing {url}...")

    image_data = capture_screenshot(url)
    if not image_data:
        df.at[idx, 'response'] = "error"
        continue

    try:
        res = requests.post(
            "http://localhost:3001/upload",
            json={"image": image_data, "url": url},
            timeout=10
        )
        res.raise_for_status()
        result = res.json()
        df.at[idx, 'response'] = result.get("verification_result", "unknown")
    except Exception as e:
        print(f"Error uploading screenshot for {url}: {e}")
        df.at[idx, 'response'] = "error"

# Clean up browser
driver.quit()

# Save to file
df.to_csv("phish_data_with_screenshot_response.csv", index=False)
print("✔ Done! Results saved to phish_data_with_screenshot_response.csv")