/**
 * SENTINEL — charts.js
 * Chart.js chart setup: Timeline, Distribution Doughnut, Risk Gauge
 */

'use strict';

/* ─── Shared Chart Defaults ─────────────────────────────────────────────── */
Chart.defaults.color = '#5a8ab0';
Chart.defaults.font.family = 'Share Tech Mono';

const TOOLTIP_STYLE = {
  backgroundColor: '#0a1520',
  borderColor:     '#1a5c8a',
  borderWidth:     1,
  titleColor:      '#00d4ff',
  bodyColor:       '#e0f0ff',
  titleFont:       { family: 'Share Tech Mono', size: 11 },
  bodyFont:        { family: 'Share Tech Mono', size: 10 },
};

/* ─── Timeline Chart ─────────────────────────────────────────────────────── */

let timelineChart = null;

function initTimelineChart(labels, anomalyData, baselineData) {
  const ctx = document.getElementById('timelineChart').getContext('2d');

  if (timelineChart) timelineChart.destroy();

  timelineChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label:           'Anomaly Score',
          data:            anomalyData,
          borderColor:     '#ff3a3a',
          backgroundColor: 'rgba(255,58,58,0.08)',
          borderWidth:     2,
          fill:            true,
          tension:         0.4,
          pointRadius:     0,
          pointHoverRadius: 5,
          pointHoverBackgroundColor: '#ff3a3a',
        },
        {
          label:           'Baseline',
          data:            baselineData,
          borderColor:     '#00d4ff',
          backgroundColor: 'rgba(0,212,255,0.04)',
          borderWidth:     1.5,
          borderDash:      [4, 4],
          fill:            true,
          tension:         0.4,
          pointRadius:     0,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      interaction: { intersect: false, mode: 'index' },
      plugins: {
        legend: { labels: { color: '#5a8ab0', font: { family: 'Share Tech Mono', size: 10 }, boxWidth: 20 } },
        tooltip: TOOLTIP_STYLE,
      },
      scales: {
        x: {
          ticks: { color: '#2a4a60', font: { family: 'Share Tech Mono', size: 8 }, maxTicksLimit: 12 },
          grid:  { color: 'rgba(14,48,80,0.4)' },
          border:{ color: 'rgba(14,48,80,0.4)' },
        },
        y: {
          min: 0, max: 100,
          ticks: { color: '#2a4a60', font: { family: 'Share Tech Mono', size: 9 }, stepSize: 25 },
          grid:  { color: 'rgba(14,48,80,0.4)' },
          border:{ color: 'rgba(14,48,80,0.4)' },
        }
      }
    }
  });

  return timelineChart;
}

function updateTimeline(newAnomalyPoint, newBaselinePoint, newLabel) {
  if (!timelineChart) return;
  timelineChart.data.datasets[0].data.push(newAnomalyPoint);
  timelineChart.data.datasets[0].data.shift();
  timelineChart.data.datasets[1].data.push(newBaselinePoint);
  timelineChart.data.datasets[1].data.shift();
  if (newLabel) {
    timelineChart.data.labels.push(newLabel);
    timelineChart.data.labels.shift();
  }
  timelineChart.update('none');
}

/* ─── Distribution Doughnut ──────────────────────────────────────────────── */

let distChart = null;

function initDistChart(high, medium, low, normal) {
  const ctx = document.getElementById('distChart').getContext('2d');
  if (distChart) distChart.destroy();

  distChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels:   ['HIGH RISK', 'MEDIUM RISK', 'LOW RISK', 'NORMAL'],
      datasets: [{
        data:            [high, medium, low, normal],
        backgroundColor: [
          'rgba(255,58,58,0.8)',
          'rgba(255,184,0,0.8)',
          'rgba(0,212,255,0.5)',
          'rgba(0,255,157,0.3)',
        ],
        borderColor: ['#ff3a3a', '#ffb800', '#00d4ff', '#00ff9d'],
        borderWidth: 1,
        hoverOffset: 8,
      }]
    },
    options: {
      responsive: true,
      cutout: '65%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: '#5a8ab0', font: { family: 'Share Tech Mono', size: 9 }, padding: 10, boxWidth: 12 }
        },
        tooltip: TOOLTIP_STYLE,
      }
    }
  });
}

function updateDistChart(high, medium, low, normal) {
  if (!distChart) return;
  distChart.data.datasets[0].data = [high, medium, low, normal];
  distChart.update('active');
}

/* ─── Gauge Chart ────────────────────────────────────────────────────────── */

let gaugeChart = null;

function initGaugeChart(score) {
  const ctx = document.getElementById('gaugeChart').getContext('2d');
  if (gaugeChart) gaugeChart.destroy();

  gaugeChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      datasets: [{
        data:            [score, 100 - score],
        backgroundColor: [gaugeColor(score), 'rgba(14,48,80,0.3)'],
        borderWidth:     0,
        circumference:   180,
        rotation:        270,
      }]
    },
    options: {
      responsive: false,
      cutout: '70%',
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
    }
  });
}

function updateGaugeChart(score) {
  if (!gaugeChart) return;
  gaugeChart.data.datasets[0].data = [score, 100 - score];
  gaugeChart.data.datasets[0].backgroundColor[0] = gaugeColor(score);
  gaugeChart.update('none');

  const el = document.getElementById('riskNum');
  el.textContent = score;
  el.style.color = score > 66 ? 'var(--accent-red)' : score > 33 ? 'var(--accent-amber)' : 'var(--accent-green)';
  el.style.textShadow = score > 66 ? '0 0 30px rgba(255,58,58,0.5)' : '';

  const lbl = document.getElementById('riskLabel');
  if (score > 66)      { lbl.textContent = '● HIGH ALERT';  lbl.style.color = 'var(--accent-red)'; }
  else if (score > 33) { lbl.textContent = '● MODERATE';    lbl.style.color = 'var(--accent-amber)'; }
  else                 { lbl.textContent = '● NORMAL';       lbl.style.color = 'var(--accent-green)'; }
}

function gaugeColor(score) {
  if (score > 66) return 'rgba(255,58,58,0.85)';
  if (score > 33) return 'rgba(255,184,0,0.85)';
  return 'rgba(0,255,157,0.7)';
}