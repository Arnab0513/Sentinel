/**
 * SENTINEL — dashboard.js
 * Main dashboard logic: API polling, table rendering, alerts, modals
 */

'use strict';

/* ─── State ──────────────────────────────────────────────────────────────── */
const state = {
  currentUser:  null,
  alertCount:   0,
  flaggedUsers: [],
};

/* ─── Clock ──────────────────────────────────────────────────────────────── */
function updateClock() {
  const now = new Date();
  const el  = document.getElementById('clock');
  if (el) el.textContent = now.toUTCString().replace('GMT', 'UTC').toUpperCase();
}
setInterval(updateClock, 1000);
updateClock();

/* ─── API Helpers ────────────────────────────────────────────────────────── */
const API_BASE = '';   // Empty = same origin (Flask serves both)

async function apiFetch(path) {
  try {
    const res = await fetch(API_BASE + path);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (e) {
    console.warn(`[API] ${path} failed:`, e.message);
    return null;
  }
}

/* ─── Summary Stats ──────────────────────────────────────────────────────── */
async function loadSummaryStats() {
  const data = await apiFetch('/api/stats/summary');
  if (!data) return;

  setEl('statHighRisk',  data.high_risk_users);
  setEl('statAnomalies', data.high_risk_users + data.medium_risk_users);
  setEl('statEvents',    data.events_per_second.toLocaleString());
  setEl('statAlerts',    state.alertCount);

  updateGaugeChart(Math.round(data.system_risk_index));

  const acc = data.model_accuracy;
  setEl('modelAccuracy', acc + '%');
  updateDistChart(
    data.high_risk_users,
    data.medium_risk_users,
    data.low_risk_users,
    data.normal_users
  );
}

/* ─── Timeline ───────────────────────────────────────────────────────────── */
async function loadTimeline(points = 60) {
  const data = await apiFetch(`/api/stats/timeline?points=${points}`);
  if (!data) return;

  const labels    = data.timeline.map(d => d.timestamp);
  const anomaly   = data.timeline.map(d => d.anomaly_score);
  const baseline  = data.timeline.map(d => d.baseline);

  initTimelineChart(labels, anomaly, baseline);
}

/* ─── Range Button ───────────────────────────────────────────────────────── */
function setRange(range, btn) {
  document.querySelectorAll('.btn-small').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const points = { '1h': 60, '6h': 120, '24h': 180 }[range] || 60;
  loadTimeline(points);
}

/* ─── Live Timeline Update ───────────────────────────────────────────────── */
async function liveTimelineUpdate() {
  const data = await apiFetch('/api/stats/timeline?points=2');
  if (!data || !data.timeline.length) return;
  const pt = data.timeline[data.timeline.length - 1];
  updateTimeline(pt.anomaly_score, pt.baseline, pt.timestamp);
}

/* ─── Flagged Users Table ────────────────────────────────────────────────── */
async function loadFlaggedUsers() {
  const data = await apiFetch('/api/users/flagged');
  if (!data) return;

  state.flaggedUsers = data.flagged_users;
  renderUserTable(data.flagged_users);
  setEl('lastUpdate', 'Updated ' + new Date().toLocaleTimeString());
}

function renderUserTable(users) {
  const tbody = document.getElementById('userTable');
  if (!users || users.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:20px;color:var(--text-secondary);font-family:var(--font-mono)">No flagged users at this time.</td></tr>';
    return;
  }

  tbody.innerHTML = users.map((u, i) => {
    const { cls, color } = riskStyle(u.risk_level);
    return `
    <tr style="animation-delay:${i * 0.05}s;cursor:pointer" onclick="openUserModal(${i})">
      <td style="font-family:var(--font-mono);color:var(--accent-cyan)">${u.user_id}</td>
      <td>${u.department}</td>
      <td style="color:var(--text-secondary)">${u.anomaly_type || '—'}</td>
      <td>
        <div class="score-bar">
          <div class="score-track">
            <div class="score-fill" style="width:${u.risk_score}%;background:${color}"></div>
          </div>
          <span style="font-family:var(--font-mono);font-size:11px;color:${color}">${u.risk_score}</span>
        </div>
      </td>
      <td><span class="risk-badge ${cls}">${u.risk_level}</span></td>
      <td style="font-family:var(--font-mono);color:var(--text-secondary)">${u.last_seen}</td>
      <td><button class="btn-small" onclick="event.stopPropagation();openUserModal(${i})">ANALYZE</button></td>
    </tr>`;
  }).join('');
}

/* ─── Alerts ─────────────────────────────────────────────────────────────── */
let _lastAlertId = -1;

async function loadAlerts() {
  const data = await apiFetch('/api/alerts?limit=15');
  if (!data) return;

  const feed   = document.getElementById('alertFeed');
  const alerts = data.alerts;

  // Only add new ones at top
  const newAlerts = alerts.filter(a => a.id > _lastAlertId);
  if (!newAlerts.length && feed.children.length > 0) return;

  newAlerts.forEach(a => {
    const div = document.createElement('div');
    div.className = `alert-item alert-${a.type}`;
    div.innerHTML = `
      <div class="alert-title">${a.title}</div>
      <div class="alert-meta">
        <span>${a.timestamp} UTC</span>
        <span>${a.user_id}</span>
        <span style="color:${riskStyle(a.type).color}">${a.type}</span>
      </div>`;
    feed.insertBefore(div, feed.firstChild);
    if (feed.children.length > 15) feed.removeChild(feed.lastChild);

    if (a.type === 'HIGH') showNotif(a.title, 'critical');
  });

  if (alerts.length) _lastAlertId = Math.max(...alerts.map(a => a.id));

  state.alertCount += newAlerts.length;
  setEl('alertCount', newAlerts.length > 0 ? `${newAlerts.length} NEW` : `${alerts.length} TOTAL`);
  setEl('statAlerts', state.alertCount);
}

/* ─── Heatmap ────────────────────────────────────────────────────────────── */
async function loadHeatmap() {
  const data = await apiFetch('/api/stats/timeline?points=24');
  if (!data) return;

  const grid  = document.getElementById('heatGrid');
  const hours = document.getElementById('heatHours');

  grid.style.gridTemplateColumns  = 'repeat(24, 1fr)';
  hours.style.gridTemplateColumns = 'repeat(24, 1fr)';

  const vals = data.timeline.map(d => d.anomaly_score / 100);

  hours.innerHTML = Array.from({length: 24}, (_, i) =>
    `<span style="text-align:center;font-family:var(--font-mono);font-size:9px;color:var(--text-dim)">${i.toString().padStart(2,'0')}</span>`
  ).join('');

  grid.innerHTML = '';
  vals.forEach((val, i) => {
    const cell = document.createElement('div');
    cell.style.cssText = `height:28px;border-radius:2px;cursor:pointer;transition:transform .2s;`;

    if      (val < 0.2) cell.style.background = `rgba(0,212,255,${val * 2})`;
    else if (val < 0.5) cell.style.background = `rgba(255,184,0,${val})`;
    else                cell.style.background = `rgba(255,58,58,${val})`;

    const status = val > 0.7 ? 'HIGH RISK' : val > 0.4 ? 'SUSPICIOUS' : 'NORMAL';
    cell.addEventListener('mouseenter', e => showTooltip(e, `HOUR: ${i.toString().padStart(2,'0')}:00<br>ACTIVITY: ${Math.round(val*100)}%<br>STATUS: ${status}`));
    cell.addEventListener('mouseleave', hideTooltip);
    cell.addEventListener('mousemove',  e => moveTooltip(e));
    grid.appendChild(cell);
  });
}

/* ─── ML Model Info ──────────────────────────────────────────────────────── */
async function loadModelInfo() {
  const data = await apiFetch('/api/model/info');
  if (!data) return;

  const metrics = [
    { label: 'Precision', val: data.precision,  color: 'var(--accent-cyan)' },
    { label: 'Recall',    val: data.recall,      color: 'var(--accent-green)' },
    { label: 'F1 Score',  val: data.f1_score,    color: 'var(--accent-purple)' },
    { label: 'AUC-ROC',   val: data.auc_roc,     color: 'var(--accent-amber)' },
  ];

  document.getElementById('modelMetrics').innerHTML =
    metrics.map(m => `
      <div style="margin-bottom:10px">
        <div style="display:flex;justify-content:space-between;font-family:var(--font-mono);font-size:10px;margin-bottom:4px">
          <span style="color:var(--text-secondary)">${m.label}</span>
          <span style="color:${m.color}">${m.val}%</span>
        </div>
        <div style="height:3px;background:var(--border)">
          <div style="width:${m.val}%;height:100%;background:${m.color};transition:width 1s ease"></div>
        </div>
      </div>
    `).join('') + `
    <div style="border-top:1px solid var(--border);padding-top:10px;margin-top:4px">
      <div style="font-family:var(--font-mono);font-size:9px;color:var(--text-secondary)">ALGORITHM</div>
      <div style="font-family:var(--font-display);font-size:11px;color:var(--accent-cyan);margin-top:2px">${data.algorithm}</div>
      <div style="font-family:var(--font-mono);font-size:9px;color:var(--text-dim);margin-top:4px">
        contamination=${data.contamination} | n_estimators=${data.n_estimators}
      </div>
    </div>`;
}

/* ─── Modal ──────────────────────────────────────────────────────────────── */
function openUserModal(idx) {
  const u = state.flaggedUsers[idx];
  if (!u) return;
  state.currentUser = u;

  document.getElementById('modalTitle').textContent = `⚡ USER PROFILE — ${u.user_id}`;

  const { cls, color } = riskStyle(u.risk_level);
  const rows = [
    ['User ID',           u.user_id],
    ['Department',        u.department],
    ['Risk Score',        `<span style="color:${color};font-size:18px;font-family:var(--font-display)">${u.risk_score}</span>`],
    ['Risk Level',        `<span class="risk-badge ${cls}">${u.risk_level}</span>`],
    ['Anomaly Detected',  u.anomaly_type || '—'],
    ['Source IP',         u.ip_address || '—'],
    ['Location',          u.location || '—'],
    ['Login Count (24h)', u.login_count || '—'],
    ['Data Accessed',     u.data_accessed_gb ? u.data_accessed_gb + ' GB' : '—'],
    ['Last Seen',         u.last_seen],
    ['Isolation Score',   u.isolation_score],
  ];

  document.getElementById('modalContent').innerHTML = rows.map(([k, v]) =>
    `<div class="modal-row"><span class="modal-key">${k}</span><span class="modal-val">${v}</span></div>`
  ).join('');

  document.getElementById('btnBlock').onclick = blockUser;
  document.getElementById('btnWatch').onclick = watchUser;
  document.getElementById('userModal').classList.add('show');
}

function closeModal() {
  document.getElementById('userModal').classList.remove('show');
}

async function blockUser() {
  if (!state.currentUser) return;
  await apiFetch(`/api/users/${state.currentUser.user_id}/action`);
  showNotif(`🔒 User ${state.currentUser.user_id} BLOCKED`, 'critical');
  closeModal();
}

async function watchUser() {
  if (!state.currentUser) return;
  await apiFetch(`/api/users/${state.currentUser.user_id}/action`);
  showNotif(`👁 User ${state.currentUser.user_id} added to Watch List`, 'warning');
  closeModal();
}

document.getElementById('userModal').addEventListener('click', function(e) {
  if (e.target === this) closeModal();
});

/* ─── Tooltip ────────────────────────────────────────────────────────────── */
function showTooltip(e, html) {
  const t = document.getElementById('tooltip');
  t.innerHTML = html;
  t.style.display = 'block';
  moveTooltip(e);
}
function moveTooltip(e) {
  const t = document.getElementById('tooltip');
  t.style.left = (e.clientX + 12) + 'px';
  t.style.top  = (e.clientY - 48) + 'px';
}
function hideTooltip() {
  document.getElementById('tooltip').style.display = 'none';
}

/* ─── Notifications ──────────────────────────────────────────────────────── */
function showNotif(msg, type) {
  const container = document.getElementById('notifContainer');
  const colors    = { critical: 'var(--accent-red)', warning: 'var(--accent-amber)', info: 'var(--accent-cyan)' };
  const color     = colors[type] || colors.info;

  const div = document.createElement('div');
  div.className = 'notif';
  div.style.borderColor = color;
  div.style.boxShadow   = `0 0 20px ${color}40`;
  div.innerHTML = `
    <div class="notif-title" style="color:${color}">${msg}</div>
    <div class="notif-body">AI model flagged — immediate review recommended</div>`;

  container.appendChild(div);

  setTimeout(() => {
    div.style.opacity   = '0';
    div.style.transform = 'translateX(100%)';
    div.style.transition = 'all .4s ease';
    setTimeout(() => div.remove(), 400);
  }, 4000);
}

/* ─── Helpers ────────────────────────────────────────────────────────────── */
function setEl(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function riskStyle(level) {
  const map = {
    HIGH:   { cls: 'risk-high',   color: '#ff3a3a' },
    MEDIUM: { cls: 'risk-medium', color: '#ffb800' },
    LOW:    { cls: 'risk-low',    color: '#00d4ff' },
    NORMAL: { cls: 'risk-normal', color: '#00ff9d' },
  };
  return map[level] || map.NORMAL;
}

/* ─── Initialization ─────────────────────────────────────────────────────── */
async function init() {
  // Load everything in parallel
  await Promise.all([
    loadTimeline(),
    loadSummaryStats(),
    loadFlaggedUsers(),
    loadAlerts(),
    loadHeatmap(),
    loadModelInfo(),
  ]);

  // Gauge needs first data point
  initGaugeChart(74);

  console.log('[SENTINEL] Dashboard initialized');
}

// Polling intervals
setInterval(loadSummaryStats,   10000);   // Stats every 10s
setInterval(loadFlaggedUsers,   8000);    // User table every 8s
setInterval(loadAlerts,         6000);    // Alerts every 6s
setInterval(liveTimelineUpdate, 3000);    // Chart update every 3s

// Kick off
init();