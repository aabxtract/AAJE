const API_BASE = localStorage.getItem("aaje_api_base") || "http://localhost:8000";
let adminToken = localStorage.getItem("aaje_admin_token") || "";
let streamChart = null;

const naira = new Intl.NumberFormat("en-NG", { style: "currency", currency: "NGN" });
const dateFmt = new Intl.DateTimeFormat("en-NG", { dateStyle: "medium" });

function headers() {
  return { Authorization: `Bearer ${adminToken}`, "Content-Type": "application/json" };
}

async function api(path) {
  const res = await fetch(`${API_BASE}${path}`, { headers: headers() });
  if (!res.ok) throw new Error(`${path} failed with ${res.status}`);
  return res.json();
}

function text(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function shortDate(value) {
  if (!value) return "-";
  return dateFmt.format(new Date(value));
}

async function loadOverview() {
  const data = await api("/admin/overview");
  text("total-users", data.total_users);
  text("total-transactions", data.total_transactions);
  text("total-vault-value", naira.format(data.total_vault_value || 0));
  text("average-score", Number(data.average_trader_score || 0).toFixed(1));
}

async function loadUsers() {
  const data = await api("/admin/users");
  text("user-count", `${data.total} users`);
  const table = document.getElementById("users-table");
  table.innerHTML = "";
  data.users.forEach((user) => {
    const tr = document.createElement("tr");
    tr.tabIndex = 0;
    tr.innerHTML = `
      <td>${user.full_name || "Unnamed trader"}</td>
      <td>${user.preferred_language || "en"}</td>
      <td>${user.streams || 0}</td>
      <td>${Number(user.trader_score || 0).toFixed(1)}</td>
      <td><span class="badge">${user.credit_grade || "N/A"}</span></td>
      <td>${shortDate(user.created_at)}</td>
    `;
    tr.addEventListener("click", () => openUser(user.id));
    table.appendChild(tr);
  });
}

async function loadTransactions() {
  const data = await api("/admin/transactions?limit=20");
  const table = document.getElementById("transactions-table");
  table.innerHTML = "";
  data.transactions.forEach((tx) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${tx.user_name || "-"}</td>
      <td>${tx.stream_name || "-"}</td>
      <td><span class="badge ${tx.type === "credit" ? "success" : "danger"}">${tx.type}</span></td>
      <td>${naira.format(tx.amount || 0)}</td>
      <td>${tx.category || "-"}</td>
      <td>${shortDate(tx.timestamp)}</td>
    `;
    table.appendChild(tr);
  });
}

function renderScore(score) {
  const box = document.getElementById("score-breakdown");
  if (!score) {
    box.innerHTML = `<article class="mini-card"><span>Score</span><strong>Not ready</strong></article>`;
    return;
  }
  box.innerHTML = `
    <article class="mini-card"><span>Score</span><strong>${Number(score.trader_score || 0).toFixed(1)}</strong></article>
    <article class="mini-card"><span>Grade</span><strong>${score.credit_grade || "N/A"}</strong></article>
    <article class="mini-card"><span>Consistency</span><strong>${Number(score.consistency_score || 0).toFixed(1)}</strong></article>
    <article class="mini-card"><span>Volume</span><strong>${Number(score.volume_score || 0).toFixed(1)}</strong></article>
    <article class="mini-card"><span>Savings</span><strong>${Number(score.savings_score || 0).toFixed(1)}</strong></article>
    <article class="mini-card"><span>Loan Ceiling</span><strong>${naira.format(score.recommended_loan_ceiling || 0)}</strong></article>
  `;
}

function renderVaults(streams) {
  const list = document.getElementById("vault-list");
  list.innerHTML = "";
  streams.forEach((stream) => {
    const item = document.createElement("article");
    item.className = "list-card";
    item.innerHTML = `
      <div><strong>${stream.stream_name}</strong><span>${stream.split_percentage}% split</span></div>
      <strong>${naira.format(stream.current_balance || 0)}</strong>
    `;
    list.appendChild(item);
  });
}

function renderModalTransactions(transactions) {
  const list = document.getElementById("modal-transactions");
  list.innerHTML = "";
  transactions.forEach((tx) => {
    const item = document.createElement("article");
    item.className = "list-card";
    item.innerHTML = `
      <div><strong>${tx.narration || tx.category || "Transaction"}</strong><span>${shortDate(tx.timestamp)}</span></div>
      <strong>${tx.type === "debit" ? "-" : ""}${naira.format(tx.amount || 0)}</strong>
    `;
    list.appendChild(item);
  });
}

function renderChart(streams) {
  const ctx = document.getElementById("stream-chart");
  if (streamChart) streamChart.destroy();
  streamChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: streams.map((stream) => stream.stream_name),
      datasets: [{
        label: "Total Deposited",
        data: streams.map((stream) => stream.total_deposited || 0),
        backgroundColor: "#1f9d8a",
        borderRadius: 4,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true } },
    },
  });
}

async function openUser(id) {
  const user = await api(`/admin/users/${id}`);
  text("modal-title", `${user.full_name || "Trader"} (${user.preferred_language || "en"})`);
  renderScore(user.score);
  renderVaults(user.streams || []);
  renderModalTransactions(user.transactions || []);
  renderChart(user.streams || []);
  document.getElementById("user-modal").classList.add("open");
}

async function boot() {
  document.getElementById("admin-token").value = adminToken;
  document.getElementById("save-token").addEventListener("click", async () => {
    adminToken = document.getElementById("admin-token").value.trim();
    localStorage.setItem("aaje_admin_token", adminToken);
    await bootData();
  });
  document.getElementById("close-modal").addEventListener("click", () => {
    document.getElementById("user-modal").classList.remove("open");
  });
  if (adminToken) await bootData();
}

async function bootData() {
  try {
    await Promise.all([loadOverview(), loadUsers(), loadTransactions()]);
  } catch (error) {
    console.error(error);
    alert("Could not load dashboard data. Check API URL and admin token.");
  }
}

boot();
