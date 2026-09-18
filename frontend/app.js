const apiInput = document.getElementById("apiBase");
const loadBtn = document.getElementById("loadBtn");
const statusEl = document.getElementById("status");
const rowsEl = document.getElementById("rows");
const drawer = document.getElementById("drawer");
const detail = document.getElementById("detail");
const closeDrawer = document.getElementById("closeDrawer");

const stored = localStorage.getItem("thermoguardApi") || "";
apiInput.value = stored;

function apiRoot() {
  return (apiInput.value || "").trim().replace(/\/$/, "");
}

async function fetchJson(path) {
  const base = apiRoot();
  if (!base) throw new Error("Paste the Lambda Function URL first.");
  const res = await fetch(`${base}${path}`);
  const text = await res.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error("API did not return JSON. Redeploy handler.py and open /events");
  }
  if (!res.ok) throw new Error(data.error || text);
  return data;
}

function renderRows(events) {
  rowsEl.innerHTML = events
    .map(
      (e) => `<tr data-id="${e.event_id}">
        <td>${e.event_id}</td>
        <td>${e.risk_score ?? ""}</td>
        <td>${e.risk_tier ?? ""}</td>
        <td>${e.evidence_confidence ?? ""} ${e.confidence_tier ?? ""}</td>
        <td>${e.osm_primary_category ?? "—"}</td>
        <td>${e.primary_driver ?? "—"}</td>
      </tr>`
    )
    .join("");
}

async function loadList() {
  localStorage.setItem("thermoguardApi", apiRoot());
  statusEl.textContent = "Loading…";
  const data = await fetchJson("/events");
  renderRows(data.events || []);
  statusEl.textContent = `${data.count ?? 0} events (scan pages already merged by API).`;
}

async function openEvent(id) {
  drawer.hidden = false;
  detail.innerHTML = "<p>Loading…</p>";
  const item = await fetchJson(`/events/${id}`);
  const expl = item.explanation || {};
  const ranking = expl.contribution_ranking || {};
  const rec = expl.investigation_priority || {};
  detail.innerHTML = `
    <p class="score">${item.risk_score}</p>
    <p class="tier">${item.risk_tier} · confidence ${item.evidence_confidence} ${item.confidence_tier || ""}</p>
    <dl>
      <dt>Event</dt><dd>${item.event_id}</dd>
      <dt>Primary driver</dt><dd>${ranking.primary_driver?.name || item.primary_driver || "—"}</dd>
      <dt>Recommend</dt><dd>${rec.recommendation || item.investigation_recommendation || "—"}</dd>
      <dt>Land cover</dt><dd>${item.worldcover_class_name || "—"}</dd>
      <dt>OSM</dt><dd>${item.osm_primary_category || "—"}</dd>
      <dt>Missing</dt><dd>${item.missing_evidence || "—"}</dd>
    </dl>
    <p>This is investigation priority, not a confirmed industrial fire.</p>
    <pre>${JSON.stringify(ranking.ranked_dimensions || [], null, 2)}</pre>
  `;
}

loadBtn.addEventListener("click", () => {
  loadList().catch((err) => {
    statusEl.textContent = err.message;
  });
});

rowsEl.addEventListener("click", (ev) => {
  const tr = ev.target.closest("tr");
  if (!tr) return;
  openEvent(tr.dataset.id).catch((err) => {
    detail.textContent = err.message;
  });
});

closeDrawer.addEventListener("click", () => {
  drawer.hidden = true;
});
