// -------------------- Config --------------------
const API_BASE = "http://localhost:8080";
const MCP_BASE = "http://localhost:8000";

// -------------------- Helpers --------------------
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

function setSelectedRun(runId, resultObj, traceObj) {
  el("runId").textContent = runId || "—";
  el("result").textContent = resultObj ? pretty(resultObj) : "—";
  el("trace").textContent = traceObj ? pretty(traceObj) : "—";
}

// -------------------- HTTP --------------------
async function apiGet(path) {
  const r = await fetch(`${API_BASE}${path}`);
  const text = await r.text();

  if (!r.ok) {
    throw new Error(`GET ${path} failed (${r.status}): ${text}`);
  }

  try {
    return JSON.parse(text);
  } catch {
    throw new Error(`GET ${path} returned non-JSON: ${text}`);
  }
}

async function apiPostAnalyze(file) {
  const formData = new FormData();
  formData.append("file", file);

  const r = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    body: formData,
  });

  const text = await r.text();

  if (!r.ok) {
    throw new Error(`POST /analyze failed (${r.status}): ${text}`);
  }

  try {
    return JSON.parse(text);
  } catch {
    throw new Error(`POST /analyze returned non-JSON: ${text}`);
  }
}

async function mcpPostProcess(text) {
  const r = await fetch(`${MCP_BASE}/process`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });

  const raw = await r.text();

  if (!r.ok) {
    throw new Error(`POST /process failed (${r.status}): ${raw}`);
  }

  try {
    return JSON.parse(raw);
  } catch {
    throw new Error(`MCP returned non-JSON: ${raw}`);
  }
}

// -------------------- History UI --------------------
function renderHistory(items) {
  const container = el("history");
  container.innerHTML = "";

  if (!items || items.length === 0) {
    container.textContent = "No runs yet.";
    return;
  }

  const ul = document.createElement("ul");
  ul.className = "history-list";

  items.forEach((r) => {
    const li = document.createElement("li");
    li.className = "history-item";

    const label =
      `${r.created_at || ""} — ` +
      `${r.vendor || "Unknown vendor"} — ` +
      `${r.amount_total || "?"} — ` +
      `${r.status || ""}` +
      (r.source_filename ? ` — ${r.source_filename}` : "");

    li.textContent = label.trim();

    li.onclick = async () => {
      try {
        setError("");
        const details = await apiGet(`/runs/${r.id}`);
        setSelectedRun(details.id, details.result, details.trace);
      } catch (e) {
        setError(e.message);
      }
    };

    ul.appendChild(li);
  });

  container.appendChild(ul);
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
    if (!input || !input.files || input.files.length === 0) {
      setError("Please choose a PDF file first.");
      return;
    }

    const file = input.files[0];

    // immediate feedback
    setSelectedRun("—", { status: "Uploading & analyzing..." }, null);

    const data = await apiPostAnalyze(file);

    // Expected shape: { run_id, result, trace }
    const runId = data.run_id || data.id || "—";
    const resultObj = data.result || data;
    const traceObj = data.trace || null;

    setSelectedRun(runId, resultObj, traceObj);

    await refreshHistory();
  } catch (e) {
    setError(e.message);
  }
}

async function testMcpClick() {
  try {
    setError("");
    const text = el("mcpText").value || "";
    if (!text.trim()) {
      setError("Paste some invoice text first.");
      return;
    }

    el("mcpOutput").textContent = "Sending to MCP…";
    const data = await mcpPostProcess(text);
    el("mcpOutput").textContent = pretty(data);
  } catch (e) {
    setError(e.message);
    el("mcpOutput").textContent = "—";
  }
}

// -------------------- Boot --------------------
document.addEventListener("DOMContentLoaded", () => {
  el("analyzeBtn").addEventListener("click", analyzeClick);
  el("refreshHistoryBtn").addEventListener("click", refreshHistory);
  el("testMcpBtn").addEventListener("click", testMcpClick);

  // initial load
  refreshHistory().catch(() => {});
});
