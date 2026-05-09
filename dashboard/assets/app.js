/**
 * AAJE Admin — app.js
 * Calls FastAPI /admin/* endpoints and populates the dashboard.
 * Replace API_BASE with your Render deployment URL in production.
 */

const API_BASE = "http://localhost:8000";
const ADMIN_TOKEN = localStorage.getItem("aaje_admin_token") || "";

const headers = {
  "Authorization": `Bearer ${ADMIN_TOKEN}`,
  "Content-Type": "application/json",
};

async function fetchStats() {
  try {
    const res = await fetch(`${API_BASE}/admin/stats`, { headers });
    const data = await res.json();
    document.getElementById("total-traders").textContent = data.total_traders ?? "—";
    document.getElementById("active-today").textContent = data.active_today ?? "—";
    document.getElementById("txns-today").textContent = data.transactions_today ?? "—";
    document.getElementById("vault-balance").textContent =
      data.total_vault_balance != null
        ? `₦${Number(data.total_vault_balance).toLocaleString()}`
        : "—";
  } catch (err) {
    console.error("Failed to fetch stats:", err);
  }
}

function initVolumeChart() {
  const ctx = document.getElementById("volume-chart");
  if (!ctx) return;
  new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
      datasets: [
        {
          label: "Transaction Volume (₦)",
          data: [0, 0, 0, 0, 0, 0, 0],
          backgroundColor: "rgba(108,99,255,0.5)",
          borderColor: "#6c63ff",
          borderWidth: 2,
          borderRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: { legend: { labels: { color: "#e2e8f0" } } },
      scales: {
        x: { ticks: { color: "#718096" }, grid: { color: "#2d3748" } },
        y: { ticks: { color: "#718096" }, grid: { color: "#2d3748" } },
      },
    },
  });
}

// Init
fetchStats();
initVolumeChart();
