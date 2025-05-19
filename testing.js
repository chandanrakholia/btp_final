const puppeteer = require("puppeteer");
const fs = require("fs");
const path = require("path");
const axios = require("axios");

// Add your list of URLs here
const urls = [
  "https://relaismondial-aide.info/",
  "https://relaismondial-aide.info/check/calcul.php",
  "https://diamondbk.online",
  "https://relaismondial-aide.com/",
  "https://relaismondial-aide.com/check/calcul.php"
];

async function captureAndSend(url) {
  let browser;
  try {
    browser = await puppeteer.launch({
      headless: true,
      args: ["--no-sandbox", "--disable-setuid-sandbox"]
    });

    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 720 });

    console.log(`⏳ Opening ${url}`);
    await page.goto(url, { waitUntil: "networkidle2", timeout: 20000 });

    const screenshotBuffer = await page.screenshot({ type: "png" });

    const base64Image = `data:image/png;base64,${screenshotBuffer.toString("base64")}`;

    const res = await axios.post("http://localhost:3001/upload", {
      url,
      image: base64Image
    });

    console.log(`✅ ${url} => ${res.data.verification_result}`);
  } catch (err) {
    console.error(`❌ Error processing ${url}:`, err.message);
  } finally {
    if (browser) await browser.close();
  }
}

(async () => {
  for (const url of urls) {
    await captureAndSend(url);
  }
})();