import { writeFile } from "node:fs/promises";

const [, , url, output, widthText, heightText, selector] = process.argv;
const width = Number(widthText);
const height = Number(heightText);
const target = await fetch(`http://127.0.0.1:9223/json/new?${encodeURIComponent(url)}`, {
  method: "PUT",
}).then((response) => response.json());
const socket = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  socket.addEventListener("open", resolve, { once: true });
  socket.addEventListener("error", reject, { once: true });
});

let nextId = 0;
const pending = new Map();
socket.addEventListener("message", ({ data }) => {
  const message = JSON.parse(data);
  if (!message.id || !pending.has(message.id)) return;
  const { resolve, reject } = pending.get(message.id);
  pending.delete(message.id);
  if (message.error) reject(new Error(message.error.message));
  else resolve(message.result);
});

function command(method, params = {}) {
  const id = ++nextId;
  socket.send(JSON.stringify({ id, method, params }));
  return new Promise((resolve, reject) => pending.set(id, { resolve, reject }));
}

await command("Page.enable");
await command("Emulation.setDeviceMetricsOverride", {
  width,
  height,
  deviceScaleFactor: 1,
  mobile: true,
  screenWidth: width,
  screenHeight: height,
});
await command("Page.navigate", { url });
await new Promise((resolve) => setTimeout(resolve, 1800));
if (selector) {
  await command("Runtime.evaluate", {
    expression: `document.querySelector(${JSON.stringify(selector)})?.click()`,
  });
  await new Promise((resolve) => setTimeout(resolve, 250));
}
const screenshot = await command("Page.captureScreenshot", {
  format: "png",
  captureBeyondViewport: false,
});
await writeFile(output, Buffer.from(screenshot.data, "base64"));
socket.close();
