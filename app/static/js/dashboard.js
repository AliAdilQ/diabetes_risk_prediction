"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const chartElement = document.getElementById("chart-data");
  if (!chartElement || typeof Chart === "undefined") return;
  const data = JSON.parse(chartElement.dataset.charts);
  const teal = "#0c9488";
  const amber = "#e4a95d";
  Chart.defaults.font.family = 'Manrope, "Segoe UI", sans-serif';
  Chart.defaults.color = "#71818b";
  Chart.defaults.font.size = 11;
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const common = {
    responsive: true, maintainAspectRatio: false,
    animation: reducedMotion ? false : { duration: 600 },
    plugins: { legend: { display: false }, tooltip: { backgroundColor: "#183940", padding: 12 } },
  };
  new Chart(document.getElementById("timeline-chart"), {
    type: "line",
    data: { labels: data.days, datasets: [{ data: data.counts, borderColor: teal,
      backgroundColor: "rgba(12,148,136,.08)", fill: true, tension: .35, borderWidth: 2,
      pointRadius: 3, pointHoverRadius: 5, pointBackgroundColor: "#fff", pointBorderWidth: 2 }] },
    options: { ...common, scales: {
      x: { grid: { display: false }, border: { display: false }, ticks: { maxTicksLimit: 7, maxRotation: 0 } },
      y: { beginAtZero: true, border: { display: false }, grid: { color: "#edf2f2" }, ticks: { precision: 0 } },
    } },
  });
  new Chart(document.getElementById("risk-chart"), {
    type: "doughnut",
    data: { labels: ["Lower Predicted Risk", "Higher Predicted Risk"], datasets: [{
      data: data.risk, backgroundColor: [teal, amber], borderWidth: 5, borderColor: "#fff",
      hoverOffset: 3, borderRadius: 4 }] },
    options: { ...common, cutout: "78%" },
  });
  new Chart(document.getElementById("age-chart"), {
    type: "bar",
    data: { labels: data.ageLabels, datasets: [{ data: data.ageCounts,
      backgroundColor: ["#aadfd9", "#73c7bd", "#33ad9f", teal], borderRadius: 6, maxBarThickness: 38 }] },
    options: { ...common, scales: {
      x: { grid: { display: false }, border: { display: false } },
      y: { beginAtZero: true, border: { display: false }, grid: { color: "#edf2f2" }, ticks: { precision: 0 } },
    } },
  });
});
