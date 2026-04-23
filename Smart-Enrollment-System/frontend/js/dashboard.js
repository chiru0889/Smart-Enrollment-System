const API = "http://127.0.0.1:5000/api";

/* =========================
   🔒 AUTH CHECK
========================= */
fetch(`${API}/protected`, { credentials: "include" })
  .then(res => {
    if (!res.ok) {
      window.location.href = "/";
    }
  });

/* =========================
   🚀 LOAD DASHBOARD
========================= */
document.addEventListener("DOMContentLoaded", () => {
  fetchKPIStats();
  loadFunnelChart();
  loadRecentChanges();
  highlightActiveMenu();
});

/* =========================
   📊 KPI STATS
========================= */
function fetchKPIStats() {
  fetch(`${API}/dashboard/stats`, { credentials: "include" })
    .then(res => res.json())
    .then(data => {
      document.getElementById("totalEnquiries").innerText = data.totalEnquiries;
      document.getElementById("totalEnrollments").innerText = data.totalEnrollments;
      document.getElementById("totalDropouts").innerText = data.totalDropouts;
    });
}



/* =========================
   📈 FUNNEL CHART
========================= */
let funnelChart;

function loadFunnelChart() {
  fetch(`${API}/dashboard/stats`, { credentials: "include" })
    .then(res => res.json())
    .then(stats => {
      console.log("📈 GRAPH DATA:", stats);

      if (funnelChart) funnelChart.destroy();

      funnelChart = new Chart(
        document.getElementById("enrollmentChart"),
        {
          type: "bar",
          data: {
            labels: ["Enquiries", "Enrollments", "Dropouts"],
            datasets: [{
              data: [
                Number(stats.totalEnquiries),
                Number(stats.totalEnrollments),
                Number(stats.totalDropouts)
              ],
              backgroundColor: [
                "#0f766e",
                "#10b981",
                "#ef4444"
              ]
            }]
          },
          options: {
            responsive: true,
            scales: { y: { beginAtZero: true } }
          }
        }
      );
    });
}


/* =========================
   🕒 RECENT ENROLLMENTS
========================= */
function loadRecentChanges() {
  fetch(`${API}/dashboard/recent`, { credentials: "include" })
    .then(res => res.json())
    .then(data => {
      const container = document.getElementById("recentList");
      container.innerHTML = "";

      data.forEach(item => {
        container.innerHTML += `
          <div class="recent-item">
            <div class="recent-info">
              <div class="recent-avatar">${item.name[0]}</div>
              <div>
                <strong>${item.name}</strong>
                <span>${item.program}</span>
              </div>
            </div>
            <span class="recent-date">${item.date}</span>
          </div>
        `;
      });
    });
}

/* =========================
   🚪 LOGOUT
========================= */
function logout() {
  fetch(`${API}/logout`, { credentials: "include" })
    .then(() => {
      window.location.href = "/";
    });
}

/* =========================
   📌 ACTIVE MENU HIGHLIGHT
========================= */
function highlightActiveMenu() {
  const current = window.location.pathname;
  document.querySelectorAll(".menu a").forEach(link => {
    if (link.getAttribute("href") === current) {
      link.classList.add("active");
    }
  });
}
