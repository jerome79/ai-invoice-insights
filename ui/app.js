const API_BASE = window.__CONFIG__?.API_BASE || "/api";
const MCP_BASE = window.__CONFIG__?.MCP_BASE || "/mcp";

let currentRun = null;        // selected run (single or from batch)
let currentBatch = null;      // full batch response
let currentBatchItems = [];   // normalized items for export

function el(id) { return document.getElementById(id); }

function pretty(obj) {
  try { return JSON.stringify(obj, null, 2); }
  catch { return String(obj); }
}

function setError(msg) { const n = el("error"); if (n) n.textContent = msg || ""; }
function setStatus(text, spinning = false) {
  const t = el("statusText");
  const dot = document.querySelector(".status .dot");
  if (t) t.textContent = text || "";
  if (dot) dot.classList.toggle("spinning", !!spinning);
}

function setModePill(text) {
  const p = el("modePill");
  if (p) p.textContent = text;
}

function normalizeStatus(s) {
  const v = (s || "").toString().toLowerCase();
  if (["ok", "success", "done", "completed"].includes(v)) return "ok";
  if (["warning", "warn"].includes(v)) return "running";
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
  for (const k of keys) if (result[k] != null && String(result[k]).trim() !== "") return result[k];
  return null;
}

function updateSummary(runId, resultObj, status) {
  el("runId").textContent = runId || "—";
  el("summaryVendor").textContent = getResultField(resultObj, ["vendor", "supplier", "seller", "issuer"]) || "—";
  el("summaryDate").textContent = getResultField(resultObj, ["invoice_date", "date", "issue_date"]) || "—";
  el("summaryTotal").textContent = getResultField(resultObj, ["amount_total", "total", "total_amount"]) || "—";

  const s = el("summaryStatus");
  s.textContent = status || "—";
  s.className = badgeClassFromStatus(status);
}

function enableButtons(enabledSingle, enabledAll) {
  ["copyJsonBtn", "downloadJsonBtn", "downloadCsvBtn"].forEach((id) => el(id).disabled = !enabledSingle);
  ["downloadAllJsonBtn", "downloadAllCsvBtn"].forEach((id) => el(id).disabled = !enabledAll);
}

async function httpJsonOrThrow(resp, context) {
  const text = await resp.text();
  if (!resp.ok) throw new Error(`${context} failed (${resp.status}): ${text}`);
  try { return JSON.parse(text); }
  catch { throw new Error(`${context} returned non-JSON: ${text}`); }
}

async function apiGet(path) {
  const r = await fetch(`${API_BASE}${path}`);
  return httpJsonOrThrow(r, `GET ${path}`);
}

async function apiPostAnalyze(file) {
  const fd = new FormData();
  fd.append("file", file);
  const r = await fetch(`${API_BASE}/analyze`, { method: "POST", body: fd });
  return httpJsonOrThrow(r, "POST /analyze");
}

async function apiPostAnalyzeBatch(files) {
  const fd = new FormData();
  for (const f of files) fd.append("files", f);
  const r = await fetch(`${API_BASE}/analyze/batch`, { method: "POST", body: fd });
  return httpJsonOrThrow(r, "POST /analyze/batch");
}

async function mcpPostProcess(text) {
  const r = await fetch(`${MCP_BASE}/process`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  return httpJsonOrThrow(r, "POST /process");
}

function setSelectedRun(runId, resultObj, traceObj, status = "ok") {
  currentRun = { id: runId, result: resultObj, trace: traceObj, status };

  el("result").textContent = resultObj ? pretty(resultObj) : "—";
  el("trace").textContent = traceObj ? pretty(traceObj) : "—";

  updateSummary(runId, resultObj, status);

  // enable single export
  enableButtons(!!resultObj, currentBatchItems.length > 0);
}

function clearUI() {
  currentRun = null;
  currentBatch = null;
  currentBatchItems = [];

  setModePill("Ready");
  setStatus("Ready.", false);
  setError("");

  el("runId").textContent = "—";
  el("summaryVendor").textContent = "—";
  el("summaryDate").textContent = "—";
  el("summaryTotal").textContent = "—";
  el("summaryStatus").textContent = "—";
  el("summaryStatus").className = "badge badge-neutral";

  el("result").textContent = "—";
  el("trace").textContent = "—";

  el("batchPanel").classList.add("hidden");
  el("batchGrid").innerHTML = "";
  el("batchMeta").textContent = "—";

  enableButtons(false, false);
}

function normalizeBatchPayload(payload) {
  // Expected shape:
  // { batch_id, results: [{filename, run_id, status, result, trace}], summary? }
  const results = payload?.results || [];
  return results.map((it, idx) => ({
    idx,
    filename: it.filename || `Invoice ${idx + 1}`,
    run_id: it.run_id || it.id || "—",
    status: it.status || "ok",
    result: it.result || null,
    trace: it.trace || null,
  }));
}

function renderBatch(payload) {
  currentBatch = payload;
  currentBatchItems = normalizeBatchPayload(payload);

  const panel = el("batchPanel");
  const grid = el("batchGrid");
  const meta = el("batchMeta");

  panel.classList.remove("hidden");
  grid.innerHTML = "";

  const total = currentBatchItems.length;
  const ok = currentBatchItems.filter(x => normalizeStatus(x.status) === "ok").length;
  const err = currentBatchItems.filter(x => normalizeStatus(x.status) === "error").length;
  const running = total - ok - err;

  meta.textContent = `${total} invoices • ${ok} ok • ${running} running/warn • ${err} error`;

  currentBatchItems.forEach((it, i) => {
    const card = document.createElement("div");
    card.className = "batch-card";
    card.dataset.run = it.run_id;

    const title = document.createElement("div");
    title.className = "batch-title";

    const left = document.createElement("div");
    left.className = "batch-filename";
    left.textContent = it.filename;

    const badge = document.createElement("span");
    badge.className = badgeClassFromStatus(it.status);
    badge.textContent = it.status || "—";

    title.appendChild(left);
    title.appendChild(badge);

    const metaDiv = document.createElement("div");
    metaDiv.className = "batch-meta";

    const vendor = getResultField(it.result, ["vendor", "supplier"]) || "—";
    const date = getResultField(it.result, ["invoice_date", "date"]) || "—";
    const totalAmt = getResultField(it.result, ["amount_total", "total"]) || "—";

    metaDiv.innerHTML = `
      <div>Run: <b>${it.run_id}</b></div>
      <div>Vendor: <b>${vendor}</b></div>
      <div>Date: <b>${date}</b> • Total: <b>${totalAmt}</b></div>
    `;

    card.appendChild(title);
    card.appendChild(metaDiv);

    card.onclick = () => {
      document.querySelectorAll(".batch-card").forEach(c => c.classList.remove("active"));
      card.classList.add("active");
      setSelectedRun(it.run_id, it.result, it.trace, it.status);
    };

    grid.appendChild(card);

    // auto-select first
    if (i === 0) {
      card.classList.add("active");
      setSelectedRun(it.run_id, it.result, it.trace, it.status);
    }
  });

  enableButtons(!!currentRun?.result, true);
}

async function refreshHistory() {
  try {
    const runs = await apiGet("/runs?limit=50&offset=0");
    const container = el("history");
    container.innerHTML = "";

    if (!runs || runs.length === 0) {
      container.textContent = "No runs yet.";
      return;
    }

    runs.forEach((r) => {
      const row = document.createElement("div");
      row.className = "history-row";

      const main = document.createElement("div");
      const title = document.createElement("div");
      title.className = "history-vendor";
      title.textContent = r.vendor || "Unknown vendor";

      const meta = document.createElement("div");
      meta.className = "history-meta";
      meta.textContent = `${r.created_at || ""} • ${r.amount_total || "?"} • ${r.source_filename || ""}`;

      main.appendChild(title);
      main.appendChild(meta);

      const badge = document.createElement("span");
      badge.className = badgeClassFromStatus(r.status);
      badge.textContent = r.status || "—";

      row.appendChild(main);
      row.appendChild(badge);

      row.onclick = async () => {
        setStatus("Loading run…", true);
        const details = await apiGet(`/runs/${r.id}`);
        setSelectedRun(details.id, details.result, details.trace, details.status || r.status || "ok");
        setStatus("Ready.", false);
      };

      container.appendChild(row);
    });
  } catch (e) {
    setError(e.message);
  }
}

function downloadText(filename, text, mime = "application/json") {
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

function toCsvRow(obj) {
  // minimal CSV: flatten top-level
  const keys = Object.keys(obj || {});
  const esc = (v) => `"${String(v ?? "").replaceAll('"', '""')}"`;
  return {
    header: keys.map(esc).join(","),
    row: keys.map(k => esc(obj[k])).join(","),
  };
}

function currentRunCsv() {
  const r = currentRun?.result || {};
  const { header, row } = toCsvRow(r);
  return `${header}\n${row}\n`;
}

function allRunsCsv() {
  const rows = currentBatchItems.map(it => ({ filename: it.filename, run_id: it.run_id, status: it.status, ...(it.result || {}) }));
  if (rows.length === 0) return "";
  const keys = Array.from(new Set(rows.flatMap(r => Object.keys(r))));
  const esc = (v) => `"${String(v ?? "").replaceAll('"', '""')}"`;
  const header = keys.map(esc).join(",");
  const body = rows.map(r => keys.map(k => esc(r[k])).join(",")).join("\n");
  return `${header}\n${body}\n`;
}

async function analyzeClick() {
  try {
    setError("");
    const input = el("filesInput");
    const files = Array.from(input?.files || []);
    if (files.length === 0) return setError("Please choose at least one PDF.");

    enableButtons(false, false);
    setStatus("Analyzing…", true);

    if (files.length === 1) {
      setModePill("Single");
      el("batchPanel").classList.add("hidden");
      currentBatchItems = [];

      const data = await apiPostAnalyze(files[0]);
      // accept either {run_id, result, trace} or raw result
      const runId = data.run_id || data.id || "—";
      const result = data.result || data;
      const trace = data.trace || null;
      const status = data.status || "ok";
      setSelectedRun(runId, result, trace, status);

    } else {
      setModePill(`Batch (${files.length})`);
      const data = await apiPostAnalyzeBatch(files);
      renderBatch(data);
    }

    setStatus("Done.", false);
    await refreshHistory();
  } catch (e) {
    setError(e.message);
    setStatus("Ready.", false);
  }
}

async function testMcpClick() {
  try {
    setError("");
    const text = (el("mcpText")?.value || "").trim();
    if (!text) return setError("Paste some invoice text first.");
    el("mcpOutput").textContent = "Sending…";
    const data = await mcpPostProcess(text);
    el("mcpOutput").textContent = pretty(data);
  } catch (e) {
    setError(e.message);
    el("mcpOutput").textContent = "—";
  }
}

async function copyCurrentJson() {
  if (!currentRun?.result) return;
  await navigator.clipboard.writeText(pretty(currentRun.result));
}

function init() {
  console.log("[UI] init ok");

  el("analyzeBtn").addEventListener("click", analyzeClick);
  el("clearBtn").addEventListener("click", () => {
    el("filesInput").value = "";
    clearUI();
  });

  el("refreshHistoryBtn").addEventListener("click", refreshHistory);
  el("testMcpBtn").addEventListener("click", testMcpClick);

  el("copyJsonBtn").addEventListener("click", async () => {
    try { await copyCurrentJson(); setStatus("Copied JSON to clipboard.", false); }
    catch (e) { setError(e.message); }
  });

  el("downloadJsonBtn").addEventListener("click", () => {
    if (!currentRun?.result) return;
    downloadText(`invoice_${currentRun.id}.json`, pretty(currentRun.result), "application/json");
  });

  el("downloadCsvBtn").addEventListener("click", () => {
    if (!currentRun?.result) return;
    downloadText(`invoice_${currentRun.id}.csv`, currentRunCsv(), "text/csv");
  });

  el("downloadAllJsonBtn").addEventListener("click", () => {
    if (currentBatchItems.length === 0) return;
    const payload = currentBatchItems.map(it => ({
      filename: it.filename, run_id: it.run_id, status: it.status, result: it.result, trace: it.trace
    }));
    downloadText(`batch_results.json`, pretty(payload), "application/json");
  });

  el("downloadAllCsvBtn").addEventListener("click", () => {
    if (currentBatchItems.length === 0) return;
    downloadText(`batch_results.csv`, allRunsCsv(), "text/csv");
  });

  clearUI();
  refreshHistory().catch(() => {});
}

window.addEventListener("load", () => {
  try { init(); }
  catch (e) {
    console.error("[UI] init failed", e);
    setError(`UI init failed: ${e.message}`);
  }
});
