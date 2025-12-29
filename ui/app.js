// ui/app.js

const API_BASE = window.__CONFIG__?.API_BASE || "/api";
const MCP_BASE = window.__CONFIG__?.MCP_BASE || "/mcp";

let currentRun = null; // { id, result, trace }

function el(id) {
  return document.getElementById(id);
}

function pretty(obj) {
  try {
    return JSON.stringify(obj, null, 2);
  } catch {
    return String(obj);
  }
}

function setError(msg) {
  const node = el("error");
  if (!node) return;
  node.textContent = msg || "";
}

function setStatus(text, spinning = false) {
  const statusText = el("statusText");
  const dot = document.querySelector(".status .dot");
  if (statusText) statusText.textContent = text || "";
  if (dot) dot.classList.toggle("spinning", !!spinning);
}

function normalizeStatus(s) {
  const v = (s || "").toString().toLowerCase();
  if (["ok", "success", "done", "completed"].includes(v)) return "ok";
  if (["running", "processing", "queued"].includes(v)) return "running";
  if (["error", "failed", "fail"].includes(v)) return "error";
  return "neutral";
}

function badgeClassFromStatus(s) {
  const n = normalizeStatus(s);
  if (n === "ok") return "badge badge-ok";
  if (n === "running") return "badge badge-running";
  if (n === "error") return "badge badge-error";
  return "badge badge-neutral";
}

function getResultField(result, keys) {
  if (!result || typeof result !== "object") return null;
  for (const k of keys) {
    if (result[k] != null && String(result[k]).trim() !== "") return result[k];
  }
  return null;
}

function updateSummary(runId, resultObj, status) {
  if (el("runId")) el("runId").textContent = runId || "—";

  const vendor = getResultField(resultObj, ["vendor", "supplier", "seller", "issuer"]);
  const invoiceDate = getResultField(resultObj, ["invoice_date", "date", "issue_date"]);
  const total = getResultField(resultObj, ["amount_total", "total", "total_amount"]);

  if (el("summaryVendor")) el("summaryVendor").textContent = vendor || "—";
  if (el("summaryDate")) el("summaryDate").textContent = invoiceDate || "—";
  if (el("summaryTotal")) el("summaryTotal").textContent = total || "—";

  const statusEl = el("summaryStatus");
  if (statusEl) {
    statusEl.textContent = status || "—";
    statusEl.className = badgeClassFromStatus(status);
  }
}

function enableExportButtons(enabled) {
  ["copyJsonBtn", "downloadJsonBtn", "downloadCsvBtn"].forEach((id) => {
    const b = el(id);
    if (b) b.disabled = !enabled;
  });
}

function setSelectedRun(runId, resultObj, traceObj, status = "ok") {
  currentRun = { id: runId, result: resultObj, trace: traceObj, status };

  // Main viewers
  if (el("result")) el("result").textContent = resultObj ? pretty(resultObj) : "—";
  if (el("trace")) el("trace").textContent = traceObj ? pretty(traceObj) : "—";

  // Summary tiles + badge
  updateSummary(runId, resultObj, status);

  // Exports
  enableExportButtons(!!resultObj);
}

// -------------------- HTTP --------------------
async function httpJsonOrThrow(resp, context) {
  const text = await resp.text();
  if (!resp.ok) throw new Error(`${context} failed (${resp.status}): ${text}`);
  try {
    return JSON.parse(text);
  } catch {
    throw new Error(`${context} returned non-JSON: ${text}`);
  }
}

async function apiGet(path) {
  const r = await fetch(`${API_BASE}${path}`);
  return httpJsonOrThrow(r, `GET ${path}`);
}

async function apiPostAnalyze(file) {
  const formData = new FormData();
  formData.append("file", file);

  const r = await fetch(`${API_BASE}/analyze`, { method: "POST", body: formData });
  return httpJsonOrThrow(r, "POST /analyze");
}

async function mcpPostProcess(text) {
  const r = await fetch(`${MCP_BASE}/process`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  return httpJsonOrThrow(r, "POST /process");
}

// -------------------- History (HTML render + badges) --------------------
function renderHistory(items) {
  const container = el("history");
  if (!container) return;

  container.innerHTML = "";

  if (!items || items.length === 0) {
    container.textContent = "No runs yet.";
    return;
  }

  items.forEach((r) => {
    const row = document.createElement("div");
    row.className = "history-row";

    const main = document.createElement("div");
    main.className = "history-main";

    const vendor = r.vendor || "Unknown vendor";
    const title = document.createElement("div");
    title.className = "history-vendor";
    title.textContent = vendor;

    const meta = document.createElement("div");
    meta.className = "history-meta";

    const date = document.createElement("span");
    date.textContent = r.created_at || "";

    const sep1 = document.createElement("span");
    sep1.className = "dot-sep";
    sep1.textContent = "•";

    const amt = document.createElement("span");
    amt.textContent = r.amount_total || "?";

    const sep2 = document.createElement("span");
    sep2.className = "dot-sep";
    sep2.textContent = "•";

    const file = document.createElement("span");
    file.textContent = r.source_filename || "";

    meta.appendChild(date);
    meta.appendChild(sep1);
    meta.appendChild(amt);
    if (r.source_filename) {
      meta.appendChild(sep2);
      meta.appendChild(file);
    }

    main.appendChild(title);
    main.appendChild(meta);

    const badge = document.createElement("span");
    badge.className = badgeClassFromStatus(r.status);
    badge.textContent = r.status || "—";

    row.appendChild(main);
    row.appendChild(badge);

    row.onclick = async () => {
      try {
        setError("");
        setStatus("Loading run…", true);
        const details = await apiGet(`/runs/${r.id}`);

        // details expected: { id, result, trace, status }
        setSelectedRun(details.id, details.result, details.trace, details.status || r.status || "ok");
        setStatus("Ready.", false);
      } catch (e) {
        setError(e.message);
        setStatus("Ready.", false);
      }
    };

    container.appendChild(row);
  });
}

async function refreshHistory() {
  try {
    setError("");
    const runs = await apiGet("/runs?limit=50&offset=0");
    renderHistory(runs);
  } catch (e) {
    setError(e.message);
    const container = el("history");
    if (container) container.textContent = "Failed to load history.";
  }
}

// -------------------- Actions --------------------
async function analyzeClick() {
  try {
    setError("");

    const input = el("fileInput");
    if (!input?.files?.length) {
      setError("Please choose a PDF file first.");
      return;
    }

    const file = input.files[0];

    setStatus("Uploading & analyzing…", true);
    updateSummary("—", null, "running");
    enableExportButtons(false);

    const data = await apiPostAnalyze(file);

    const runId = data.run_id || data.id || "—";
    const resultObj = data.result || data;
    const traceObj = data.trace || null;
    const status = data.status || "ok";

    setSelectedRun(runId, resultObj, traceObj, status);
    setStatus("Done.", false);

    await refreshHistory();
  } catch (e) {
    setError(e.message);
    setStatus("Ready.", false);
    updateSummary("—", null, "error");
    enableExportButtons(false);
  }
}

async function testMcpClick() {
  try {
    setError("");
    const node = el("mcpText");
    const out = el("mcpOutput");
    const text = (node?.value || "").trim();

    if (!text) {
      setError("Paste some invoice text first.");
      return;
    }

    if (out) out.textContent = "Sending to MCP…";
    const data = await mcpPostProcess(text);
    if (out) out.textContent = pretty(data);
  } catch (e) {
    setError(e.message);
    const out = el("mcpOutput");
    if (out) out.textContent = "—";
  }
}

// -------------------- Exports --------------------
async function copyJsonClick() {
  if (!currentRun?.result) return;
  await navigator.clipboard.writeText(pretty(currentRun.result));
  setStatus("Copied JSON to clipboard.", false);
}

function downloadBlob(filename, mime, text) {
  const blob = new Blob([text], { type: mime });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();

  URL.revokeObjectURL(url);
}

function downloadJsonClick() {
  if (!currentRun?.result) return;
  const name = `invoice_${currentRun.id || "run"}.json`;
  downloadBlob(name, "application/json", pretty(currentRun.result));
}

function toCsvFlat(obj) {
  // Simple “single-row” CSV (good enough for MVP)
  const keys = Object.keys(obj || {});
  const esc = (v) => `"${String(v ?? "").replaceAll('"', '""')}"`;
  const header = keys.join(",");
  const row = keys.map((k) => esc(obj[k])).join(",");
  return `${header}\n${row}\n`;
}

function downloadCsvClick() {
  if (!currentRun?.result) return;
  const name = `invoice_${currentRun.id || "run"}.csv`;
  downloadBlob(name, "text/csv", toCsvFlat(currentRun.result));
}

// -------------------- Boot --------------------
document.addEventListener("DOMContentLoaded", () => {
  // Wire main actions
  const analyzeBtn = el("analyzeBtn");
  if (analyzeBtn) analyzeBtn.onclick = analyzeClick;

  const refreshBtn = el("refreshHistoryBtn");
  if (refreshBtn) refreshBtn.onclick = refreshHistory;

  const testBtn = el("testMcpBtn");
  if (testBtn) testBtn.onclick = testMcpClick;

  // Wire export buttons (they exist in your HTML but were never handled)
  const copyBtn = el("copyJsonBtn");
  if (copyBtn) copyBtn.onclick = copyJsonClick;

  const dJsonBtn = el("downloadJsonBtn");
  if (dJsonBtn) dJsonBtn.onclick = downloadJsonClick;

  const dCsvBtn = el("downloadCsvBtn");
  if (dCsvBtn) dCsvBtn.onclick = downloadCsvClick;

  // Disable exports until you have a run selected
  enableExportButtons(false);

  setStatus("Ready.", false);
  refreshHistory().catch(() => {});
});
