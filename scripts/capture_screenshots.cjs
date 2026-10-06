/** Maintainer browser verification. Requires Playwright; never changes app source. */
const { chromium } = require("playwright");
const fs = require("node:fs");
const path = require("node:path");
const { spawn } = require("node:child_process");
const readline = require("node:readline");

const root = path.resolve(__dirname, "..");
const origin = process.env.SCREENSHOT_URL || "http://127.0.0.1:5000";
const output = path.join(root, "screenshots");
let activeBrowser;
let bridge;

async function main() {
  fs.mkdirSync(output, { recursive: true });
  const options = { headless: true };
  if (process.env.PLAYWRIGHT_CHANNEL) options.channel = process.env.PLAYWRIGHT_CHANNEL;
  const browser = await chromium.launch(options);
  activeBrowser = browser;
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 },
    deviceScaleFactor: 1, reducedMotion: "reduce" });
  const page = await context.newPage();
  if (process.env.FLASK_BRIDGE_PYTHON) {
    bridge = spawn(process.env.FLASK_BRIDGE_PYTHON,
      [path.join(__dirname, "browser_wsgi_bridge.py")], { cwd: root, windowsHide: true });
    bridge.stderr.on("data", (chunk) => process.stderr.write(chunk));
    const lines = readline.createInterface({ input: bridge.stdout });
    const pending = new Map();
    let sequence = 0;
    await new Promise((resolve, reject) => {
      lines.once("line", (line) => JSON.parse(line).ready ? resolve() : reject(new Error(line)));
      bridge.once("error", reject);
      bridge.once("exit", (code) => reject(new Error(`WSGI bridge exited: ${code}`)));
    });
    lines.on("line", (line) => {
      const result = JSON.parse(line);
      pending.get(result.id)?.(result);
      pending.delete(result.id);
    });
    await page.route(`${origin}/**`, async (route) => {
      const request = route.request();
      const url = new URL(request.url());
      const id = sequence++;
      const response = new Promise((resolve) => pending.set(id, resolve));
      const payload = { id, path: url.pathname + url.search, method: request.method(),
        headers: await request.allHeaders(), body: (request.postDataBuffer() || Buffer.alloc(0)).toString("base64") };
      bridge.stdin.write(JSON.stringify(payload) + "\n");
      const result = await response;
      await route.fulfill({ status: result.status, headers: result.headers,
        body: Buffer.from(result.body, "base64") });
    });
  }
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => { if (message.type() === "error") errors.push(message.text()); });
  page.on("response", (response) => {
    if (response.status() >= 400) errors.push(`${response.status()}: ${response.url()}`);
  });
  async function visit(route) {
    await page.goto(`${origin}${route}`, { waitUntil: "networkidle" });
    await page.evaluate(() => document.fonts.ready);
  }
  async function capture(name) {
    await page.screenshot({ path: path.join(output, `${name}.png`), fullPage: true });
    console.log(`Captured screenshots/${name}.png`);
  }
  async function verifyWidth(label) {
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
    if (overflow) {
      errors.push(`${label}: horizontal page overflow at ${page.viewportSize().width}px`);
      const elements = await page.evaluate(() => [...document.querySelectorAll("body *")]
        .filter((element) => element.getBoundingClientRect().right > window.innerWidth + 1)
        .slice(0, 10).map((element) => ({ tag: element.tagName, class: element.className,
          right: element.getBoundingClientRect().right })));
      console.log(`Overflow detail ${label}: ${JSON.stringify(elements)}`);
    }
    if (page.viewportSize().width === 390 && ["/admin", "/admin/predictions"].includes(label)) {
      fs.mkdirSync(path.join(root, ".local"), { recursive: true });
      await page.screenshot({ path: path.join(root, ".local",
        label === "/admin" ? "mobile-dashboard.png" : "mobile-predictions.png"), fullPage: true });
    }
  }
  await visit("/");
  await verifyWidth("Home");
  await capture("home");
  await visit("/predict");
  await capture("prediction");
  await page.locator("#fill-example").click();
  await page.locator('#prediction-form button[type="submit"]').click();
  await page.waitForURL("**/prediction-result");
  await page.waitForLoadState("networkidle");
  if (!await page.locator(".result-card").isVisible()) throw new Error("Prediction did not produce a result");
  await capture("result");
  for (const width of [768, 390]) {
    await page.setViewportSize({ width, height: 844 });
    await verifyWidth("Prediction result");
  }
  await page.setViewportSize({ width: 1440, height: 1000 });
  await visit("/admin/login");
  await capture("admin-login");
  await page.locator("#username").fill("admin");
  await page.locator("#password").fill("Admin@123");
  await page.locator('button[type="submit"]').click();
  await page.waitForURL(/\/admin\/?$/);
  await page.waitForLoadState("networkidle");
  await page.waitForFunction(() => typeof Chart !== "undefined" &&
    ["timeline-chart", "risk-chart", "age-chart"].every((id) => !!Chart.getChart(id)));
  await capture("admin-dashboard");
  for (const width of [768, 390]) {
    await page.setViewportSize({ width, height: 844 });
    for (const route of ["/", "/predict", "/about", "/model-info",
                         "/admin", "/admin/predictions", "/admin/model-performance"]) {
      await visit(route);
      await verifyWidth(route);
    }
    await visit("/admin");
    await page.locator(".sidebar-toggle").click();
    if (!await page.locator("#admin-sidebar").isVisible()) errors.push("Mobile sidebar unavailable");
    await page.locator('button[aria-label="Logout"]').click();
    await page.waitForURL("**/admin/login");
    await verifyWidth("Login");
    // Re-authenticate for the next viewport's protected routes.
    await page.locator("#username").fill("admin");
    await page.locator("#password").fill("Admin@123");
    await page.locator('button[type="submit"]').click();
    await page.waitForURL(/\/admin\/?$/);
  }
  await page.setViewportSize({ width: 1440, height: 1000 });
  await visit("/admin/predictions");
  await page.selectOption("#risk", "1");
  await page.locator('button[aria-label="Apply filters"]').click();
  await page.waitForLoadState("networkidle");
  if (await page.locator("tbody .risk-low").count()) errors.push("Risk filter showed lower risk rows");
  await page.locator('a[aria-label^="View prediction"]').first().click();
  await page.waitForLoadState("networkidle");
  if (!await page.locator(".input-summary").isVisible()) errors.push("Record detail missing");
  await page.locator('button[aria-label="Logout"]').click();
  await page.waitForURL("**/admin/login");
  if (!await page.locator("#username").isVisible()) errors.push("Logout did not return to login");
  await browser.close();
  bridge?.kill();
  const report = { desktop: 1440, tablet: 768, mobile: 390, screenshots: 5,
    transport: bridge ? "Flask WSGI over stdio (loopback-restricted sandbox)" : "HTTP",
    checked: ["Public pages", "Prediction submission", "Admin login", "Three Chart.js charts",
      "Filters", "Details", "Logout", "Responsive page width", "Browser console", "Asset responses"],
    errors: [...new Set(errors)] };
  const local = path.join(root, ".local");
  fs.mkdirSync(local, { recursive: true });
  fs.writeFileSync(path.join(local, "browser-verification.json"), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  if (errors.length) process.exitCode = 1;
}

main().catch(async (error) => {
  console.error(error);
  await activeBrowser?.close();
  bridge?.kill();
  process.exitCode = 1;
});
