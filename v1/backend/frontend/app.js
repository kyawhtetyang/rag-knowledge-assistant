const healthText = document.querySelector("#healthText");
const uploadForm = document.querySelector("#uploadForm");
const fileInput = document.querySelector("#fileInput");
const jobStatus = document.querySelector("#jobStatus");
const askForm = document.querySelector("#askForm");
const questionInput = document.querySelector("#questionInput");
const answerText = document.querySelector("#answerText");
const citations = document.querySelector("#citations");

async function getJson(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || `Request failed: ${response.status}`);
  }
  return data;
}

async function refreshHealth() {
  try {
    const data = await getJson("/health");
    healthText.textContent = `Healthy - ${data.settings.embeddings_provider}, ${data.settings.retrieval_mode} retrieval`;
  } catch (error) {
    healthText.textContent = `Service unavailable - ${error.message}`;
  }
}

function renderCitations(items) {
  citations.innerHTML = "";
  for (const item of items || []) {
    const node = document.createElement("article");
    node.className = "citation";
    const title = document.createElement("strong");
    title.textContent = `${item.source} - chunk ${item.chunk_index} - score ${Number(item.score).toFixed(4)}`;
    const preview = document.createElement("span");
    preview.textContent = item.preview;
    node.append(title, preview);
    citations.appendChild(node);
  }
}

async function pollJob(jobId) {
  for (let attempt = 0; attempt < 90; attempt += 1) {
    const data = await getJson(`/api/jobs/${jobId}`);
    jobStatus.textContent = `Job ${jobId}: ${data.status}`;
    if (data.status === "done" || data.status === "error") {
      return data;
    }
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  throw new Error(`Job ${jobId} did not finish in time`);
}

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = fileInput.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);
  jobStatus.textContent = "Uploading...";

  try {
    const queued = await getJson("/api/ingest-file-async", {
      method: "POST",
      body: formData,
    });
    jobStatus.textContent = `Job ${queued.job_id}: ${queued.status}`;
    const done = await pollJob(queued.job_id);
    if (done.status === "error") {
      throw new Error(done.error || "Worker failed");
    }
    jobStatus.textContent = `Job ${queued.job_id}: done`;
  } catch (error) {
    jobStatus.textContent = `Upload failed: ${error.message}`;
  }
});

askForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  answerText.textContent = "Thinking...";
  renderCitations([]);

  try {
    const data = await getJson("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: questionInput.value, top_k: 5 }),
    });
    answerText.textContent = data.answer;
    renderCitations(data.citations);
  } catch (error) {
    answerText.textContent = `Ask failed: ${error.message}`;
  }
});

refreshHealth();
