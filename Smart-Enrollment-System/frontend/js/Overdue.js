const API = "http://127.0.0.1:5000/api";

// DOM Elements
const overdueTableBody = document.getElementById("overdueTableBody");
const totalDueDisplay = document.getElementById("totalDueDisplay");
const totalFinesDisplay = document.getElementById("totalFinesDisplay");
const totalAmountDisplay = document.getElementById("totalAmountDisplay");

document.addEventListener("DOMContentLoaded", () => {
  loadOverdueData();
});

 const logoutBtn = document.getElementById("logoutBtn");

if (logoutBtn) {
  logoutBtn.addEventListener("click", () => {
    fetch("http://127.0.0.1:5000/api/logout", {
      method: "POST",
      credentials: "include"
    }).then(() => {
      window.location.href = "/";
    });
  });
}



function loadOverdueData() {
  fetch(`${API}/emi/overdue`, {
    credentials: "include"   // ✅ REQUIRED
  })
    .then(res => res.json())
    .then(data => {
      renderOverdueTable(data); // backend already sends overdue only
    })
    .catch(err => console.error("Error loading overdue data:", err));
}

function renderOverdueTable(data) {
  overdueTableBody.innerHTML = "";

  let totalDue = 0;
  let totalFines = 0;
  let totalWithFines = 0;

  if (!data || data.length === 0) {
    overdueTableBody.innerHTML =
      "<tr><td colspan='10' class='text-center'>No overdue records found.</td></tr>";
    totalDueDisplay.innerText = "₹0";
    totalFinesDisplay.innerText = "₹0";
    totalAmountDisplay.innerText = "₹0";
    return;
  }

  const today = new Date();

  data.forEach(item => {
    const dueDate = new Date(item.due_date);
    const diffTime = today - dueDate;
    const daysLate = Math.max(0, Math.ceil(diffTime / (1000 * 60 * 60 * 24)));

    const fineAmount = daysLate * 50; // ₹50 per day
    const amount = Number(item.amount) || 0;

    totalDue += amount;
    totalFines += fineAmount;
    totalWithFines += amount + fineAmount;

    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td><strong>${item.student}</strong></td>
      <td>${item.program}</td>
      <td>-</td>
      <td>${formatDate(item.due_date)}</td>
      <td>₹${amount.toLocaleString()}</td>
      <td class="red-text">${daysLate}</td>
      <td class="red-text">₹${fineAmount.toLocaleString()}</td>
      <td>₹${(amount + fineAmount).toLocaleString()}</td>
      <td>
        <span class="status-badge status-overdue">Overdue</span>
      </td>
      <td>
        <button class="mark-btn"
          onclick="markPaid(${item.enrollment_id}, ${item.emi_no})">
          Mark Paid
        </button>
      </td>
    `;

    overdueTableBody.appendChild(tr);
  });

  totalDueDisplay.innerText = `₹${totalDue.toLocaleString()}`;
  totalFinesDisplay.innerText = `₹${totalFines.toLocaleString()}`;
  totalAmountDisplay.innerText = `₹${totalWithFines.toLocaleString()}`;
}

// ✅ MARK EMI AS PAID
function markPaid(enrollmentId, emiNo) {
  if (!confirm("Mark this EMI as Paid?")) return;

  fetch(`${API}/emi/pay`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",   // ✅ REQUIRED
    body: JSON.stringify({
      enrollment_id: enrollmentId,
      emi_no: emiNo
    })
  })
    .then(res => res.json())
    .then(() => loadOverdueData());
}

// Date formatter
function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric"
  });
}

function applyAllFines() {
  alert("Fine calculation is already applied dynamically.");
}

function downloadReport() {
  window.location.href = "http://127.0.0.1:5000/api/overdue/download-report";
}