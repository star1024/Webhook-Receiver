const eventList = document.getElementById("eventList");
const eventCount = document.getElementById("eventCount");
const emptyState = document.getElementById("emptyState");
const refreshButton = document.getElementById("refreshButton");
const clearButton = document.getElementById("clearButton");
const sampleCommand = document.getElementById("sampleCommand");

sampleCommand.textContent =
  "Invoke-RestMethod -Method POST `\n" +
  '  -Uri "http://127.0.0.1:8000/webhook" `\n' +
  '  -ContentType "application/json" `\n' +
  '  -Body \'{"event":"order.created","orderId":12345,"source":"demo"}\'';

function renderEvents(events) {
  eventCount.textContent = `${events.length} event${events.length === 1 ? "" : "s"} captured`;
  eventList.innerHTML = "";
  emptyState.classList.toggle("hidden", events.length > 0);

  for (const event of events) {
    const card = document.createElement("article");
    card.className = "event-card";

    const meta = document.createElement("div");
    meta.className = "event-meta";
    meta.innerHTML = `
      <strong>${event.path}</strong>
      <span>${new Date(event.received_at).toLocaleString()}</span>
      <span>${event.content_type || "unknown content-type"}</span>
    `;

    const pre = document.createElement("pre");
    pre.textContent = JSON.stringify(event.payload, null, 2);

    card.append(meta, pre);
    eventList.append(card);
  }
}

async function loadEvents() {
  const response = await fetch("/api/events", { cache: "no-store" });
  const data = await response.json();
  renderEvents(data.events || []);
}

async function clearEvents() {
  await fetch("/api/events/clear", { method: "POST" });
  await loadEvents();
}

refreshButton.addEventListener("click", loadEvents);
clearButton.addEventListener("click", clearEvents);

loadEvents();
setInterval(loadEvents, 5000);
