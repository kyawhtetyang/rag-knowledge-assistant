const themeToggleEl = document.querySelector("#theme-toggle");
const reloadPageEl = document.querySelector("#reload-page");
const apiBaseEl = document.querySelector("#apiBase");
const fileInputEl = document.querySelector("#fileInput");
const uploadBtnEl = document.querySelector("#uploadBtn");
const refreshJobBtnEl = document.querySelector("#refreshJobBtn");
const jobIdEl = document.querySelector("#jobId");
const questionEl = document.querySelector("#question");
const topKEl = document.querySelector("#topK");
const askBtnEl = document.querySelector("#askBtn");
const statusOutputEl = document.querySelector("#statusOutput");
const answerOutputEl = document.querySelector("#answerOutput");
const citationsOutputEl = document.querySelector("#citationsOutput");

const DEFAULT_THEME = "dark";
const API_STORAGE_KEY = "ragApiBase";
let pollTimer = null;

const getStoredTheme = () => {
  try {
    const storedTheme = window.localStorage.getItem("theme");
    return storedTheme === "light" || storedTheme === "dark" ? storedTheme : DEFAULT_THEME;
  } catch {
    return DEFAULT_THEME;
  }
};

let currentTheme = getStoredTheme();

const applyTheme = (theme) => {
  const root = document.documentElement;
  root.classList.toggle("dark", theme === "dark");

  if (themeToggleEl) {
    const nextTheme = theme === "dark" ? "light" : "dark";
    themeToggleEl.setAttribute("aria-label", `Switch to ${nextTheme} mode`);
    themeToggleEl.setAttribute("title", `Switch to ${nextTheme} mode`);
  }

  try {
    window.localStorage.setItem("theme", theme);
  } catch {
    // Ignore storage errors.
  }
};

const getConfiguredBase = () => {
  const configured = window.RAG_CONFIG?.apiBaseUrl?.trim();
  if (configured) {
    return configured.replace(/\/$/, "");
  }
  return "";
};

const getApiBase = () => {
  const value = (apiBaseEl?.value || "").trim();
  if (!value) {
    return "";
  }
  return value.replace(/\/$/, "");
};

const persistApiBase = () => {
  const value = getApiBase();
  try {
    if (value) {
      window.localStorage.setItem(API_STORAGE_KEY, value);
    } else {
      window.localStorage.removeItem(API_STORAGE_KEY);
    }
  } catch {
    // Ignore storage errors.
  }
};

const buildUrl = (path) => `${getApiBase()}${path}`;

const setStatus = (value) => {
  if (statusOutputEl) {
    statusOutputEl.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
  }
};

const setAnswer = (value) => {
  if (answerOutputEl) {
    answerOutputEl.textContent = value;
  }
};

const renderCitations = (items) => {
  if (!citationsOutputEl) return;

  if (!Array.isArray(items) || items.length === 0) {
    citationsOutputEl.innerHTML = "<p>No citations yet.</p>";
    return;
  }

  citationsOutputEl.innerHTML = items
    .map((item) => {
      const source = item.source || "unknown";
      const chunkIndex = item.chunk_index ?? "?";
      const score = typeof item.score === "number" ? item.score.toFixed(4) : item.score ?? "n/a";
      const preview = item.preview || "";
      return `
        <article class="citation-card">
          <strong>${source}</strong>
          <span>chunk ${chunkIndex} | score ${score}</span>
          <p>${preview}</p>
        </article>
      `;
    })
    .join("");
};

const request = async (path, options = {}) => {
  persistApiBase();
  const response = await fetch(buildUrl(path), options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || `HTTP ${response.status}`);
  }
  return data;
};

const fetchJob = async (jobId) => {
  const data = await request(`/api/jobs/${jobId}`);
  setStatus(data);

  if (data.status === "done") {
    window.clearInterval(pollTimer);
    pollTimer = null;
  }

  return data;
};

const startPollingJob = (jobId) => {
  if (!jobId) return;
  if (pollTimer) {
    window.clearInterval(pollTimer);
  }
  pollTimer = window.setInterval(() => {
    fetchJob(jobId).catch((error) => {
      setStatus(`Job refresh failed: ${error.message}`);
      window.clearInterval(pollTimer);
      pollTimer = null;
    });
  }, 2500);
};

applyTheme(currentTheme);

const savedApiBase = (() => {
  try {
    return window.localStorage.getItem(API_STORAGE_KEY) || "";
  } catch {
    return "";
  }
})();

if (apiBaseEl) {
  apiBaseEl.value = savedApiBase || getConfiguredBase();
  apiBaseEl.addEventListener("change", persistApiBase);
  apiBaseEl.addEventListener("blur", persistApiBase);
}

renderCitations([]);

themeToggleEl?.addEventListener("click", () => {
  currentTheme = currentTheme === "dark" ? "light" : "dark";
  applyTheme(currentTheme);
});

reloadPageEl?.addEventListener("click", () => {
  window.location.reload();
});

uploadBtnEl?.addEventListener("click", async () => {
  const file = fileInputEl?.files?.[0];
  if (!file) {
    setStatus("Choose a .txt, .md, or .pdf file first.");
    return;
  }

  uploadBtnEl.disabled = true;
  setStatus("Uploading file for async ingestion...");
  setAnswer("No answer yet.");
  renderCitations([]);

  try {
    const formData = new FormData();
    formData.append("file", file);
    const data = await request("/api/ingest-file-async", {
      method: "POST",
      body: formData,
    });
    if (jobIdEl) {
      jobIdEl.value = String(data.job_id || "");
    }
    setStatus(data);
    startPollingJob(data.job_id);
  } catch (error) {
    setStatus(`Upload failed: ${error.message}`);
  } finally {
    uploadBtnEl.disabled = false;
  }
});

refreshJobBtnEl?.addEventListener("click", async () => {
  const jobId = Number(jobIdEl?.value || 0);
  if (!jobId) {
    setStatus("Enter a valid job id first.");
    return;
  }

  refreshJobBtnEl.disabled = true;
  try {
    await fetchJob(jobId);
  } catch (error) {
    setStatus(`Job refresh failed: ${error.message}`);
  } finally {
    refreshJobBtnEl.disabled = false;
  }
});

askBtnEl?.addEventListener("click", async () => {
  const question = (questionEl?.value || "").trim();
  const topK = Number(topKEl?.value || 5);

  if (!question) {
    setStatus("Enter a question first.");
    return;
  }

  askBtnEl.disabled = true;
  setAnswer("Running retrieval + answer generation...");
  renderCitations([]);

  try {
    const data = await request("/api/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question, top_k: topK }),
    });
    setStatus({ question: data.question, top_k: data.top_k, citations: (data.citations || []).length });
    setAnswer(data.answer || "(empty answer)");
    renderCitations(data.citations || []);
  } catch (error) {
    setAnswer(`Ask failed: ${error.message}`);
    setStatus(`Ask failed: ${error.message}`);
  } finally {
    askBtnEl.disabled = false;
  }
});
