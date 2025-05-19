import fs from "fs-extra";
import csv from "csv-parser";
import puppeteer from "puppeteer";

const csvFile = "top-1m.csv";
const datasetDir = "dataset";
const concurrencyLimit = 1;
const startFromRow = 8269; // 🔁 Change this to start from a specific row

const urls = [];

async function loadUrls() {
  return new Promise((resolve) => {
    let rowCount = 0;
    fs.createReadStream(csvFile)
      .pipe(csv({ headers: ["id", "domain"] }))
      .on("data", (row) => {
        rowCount++;
        if (rowCount < startFromRow) return;

        const id = row.id.trim();
        const domain = row.domain.trim();
        if (id && domain) {
          urls.push({ id, url: `https://${domain}` });
        }
      })
      .on("end", resolve);
  });
}

async function captureScreenshot(browser, { id, url }) {
  const page = await browser.newPage();
  const path = `${datasetDir}/${id}.png`;

  try {
    await page.setViewport({ width: 1280, height: 800 });
    await page.setUserAgent(
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
    );
    await page.goto(url, { waitUntil: "networkidle2", timeout: 15000 });
    await page.screenshot({ path });
    console.log(`✅ ${id}: ${url}`);
  } catch (err) {
    console.warn(`❌ ${id}: Failed to capture ${url} - ${err.message}`);
  } finally {
    await page.close();
  }
}

async function runWithConcurrency(browser, tasks, limit) {
  const queue = [...tasks];
  const workers = Array.from({ length: limit }).map(async () => {
    while (queue.length) {
      const task = queue.shift();
      await captureScreenshot(browser, task);
    }
  });

  await Promise.all(workers);
}

(async () => {
  await fs.ensureDir(datasetDir);
  await loadUrls();
  console.log(`📦 Loaded ${urls.length} URLs (starting from row ${startFromRow})`);

  const browser = await puppeteer.launch({
    headless: true,
    protocolTimeout: 60000,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });

  await runWithConcurrency(browser, urls, concurrencyLimit);
  await browser.close();

  console.log("🎉 All screenshots captured!");
})();