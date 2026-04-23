const API = "http://127.0.0.1:5000/api";




// DOM Elements
const paymentList = document.getElementById("paymentList");
const searchInput = document.getElementById("searchInput");
const statusFilter = document.getElementById("statusFilter");
const modal = document.getElementById("emiModal");
const studentSelect = document.getElementById("studentSelect");

let allPayments = []; // grouped by student

document.addEventListener("DOMContentLoaded", () => {

  /* =========================
     🔒 AUTH CHECK
  ========================= */
  fetch(`${API}/protected`, { credentials: "include" })
    .then(res => {
      if (!res.ok) window.location.href = "/";
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



  loadEnrollments();
  loadEMI();

  searchInput.addEventListener("input", filterPayments);
  statusFilter.addEventListener("change", filterPayments);
});

/* ================= LOAD ENROLLMENTS ================= */
function loadEnrollments() {
  fetch(`${API}/enrollments`, { credentials: "include" })
    .then(res => res.json())
    .then(data => {
      studentSelect.innerHTML = `<option value="">Select Student</option>`;
      data.forEach(s => {
        studentSelect.innerHTML += `
          <option value="${s.id}">${s.name} (${s.program})</option>`;
      });
    });
}

/* ================= LOAD EMI (GROUPED) ================= */
function loadEMI() {
  fetch(`${API}/emi`, { credentials: "include" })
    .then(res => res.json())
    .then(data => {
      const groups = {};

      data.forEach(item => {
  if (!groups[item.enrollment_id]) {
    groups[item.enrollment_id] = {
      enrollment_id: item.enrollment_id,
      student: item.student,
      program: item.program,
      totalCount: 0,
      paidCount: 0,
      totalAmount: 0,
      emis: []
    };
  }

  const g = groups[item.enrollment_id];

  // ✅ ONLY COUNT REAL EMIs
  if (item.emi_no > 0) {
    g.totalCount++;
    g.totalAmount += Number(item.amount);

    g.emis.push({
      emi_no: item.emi_no,
      amount: Number(item.amount),
      due_date: item.due_date || null,
      status: item.status
    });

    if (item.status === "Paid") {
      g.paidCount++;
    }
  }
});


      allPayments = Object.values(groups);
      renderPayments(allPayments);
    });
}

/* ================= RENDER ================= */
function renderPayments(data) {
  paymentList.innerHTML = "";

  if (!data.length) {
    paymentList.innerHTML =
      `<div class="text-center text-gray-400 py-10">No records found.</div>`;
    return;
  }

  data.forEach(student => {

    const emis = student.emis || [];

    const paidEmis = emis.filter(e => e.status === "Paid");
    const pendingEmis = emis.filter(
      e => e.status !== "Paid" && e.due_date
    );

    // ================= LABEL LOGIC =================
    let statusText = "";
    let statusClass = "";
    let dueText = "-";

    // 1️⃣ ALL PAID
    if (emis.length > 0 && paidEmis.length === emis.length) {
      statusText = "Completed";
      statusClass = "status-paid";
      dueText = "Completed";
    }

    // 2️⃣ EMI PENDING → NEXT DUE DATE
    else if (pendingEmis.length > 0) {
      const nextDue = pendingEmis
        .sort((a, b) => new Date(a.due_date) - new Date(b.due_date))[0];

      statusText = "Active";
      statusClass = "status-pending";
      dueText = `Next Due: ${formatDate(nextDue.due_date)}`;
    }

    // 3️⃣ EMI NOT GENERATED
    else {
      statusText = "Not Generated";
      statusClass = "status-pending";
      dueText = "-";
    }

    // ================= PROGRESS =================
    const percent = student.totalCount
      ? Math.round((student.paidCount / student.totalCount) * 100)
      : 0;

    // ================= CARD =================
    const card = document.createElement("div");
    card.className = "payment-card";

    card.innerHTML = `
      <div>
        <div class="student-name clickable-name"
             onclick="goToStudent(${student.enrollment_id})">
          ${student.student}
        </div>
        <div class="program-name">${student.program}</div>
      </div>

      <div class="emi-label">${student.totalCount} EMIs</div>

      <div class="amount">₹ ${student.totalAmount.toLocaleString()}</div>

      <div class="due-date">${dueText}</div>

      <div class="progress-container">
        <div class="progress-text">
          <span>Paid</span>
          <span>${student.paidCount}/${student.totalCount}</span>
        </div>
        <div class="progress-bg">
          <div class="progress-fill" style="width:${percent}%"></div>
        </div>
      </div>

      <div>
        <span class="status-badge ${statusClass}">
          ${statusText}
        </span>
      </div>

      <div>
        <button class="view-btn"
                onclick="goToStudent(${student.enrollment_id})">
          View Details
        </button>
      </div>
    `;

    paymentList.appendChild(card);
  });
}


/* ================= FILTER ================= */
function filterPayments() {
  const term = (searchInput.value || "").toLowerCase();
  const status = statusFilter.value;

  const filtered = allPayments.filter(s => {

    const studentName = (s.student || "").toLowerCase();
    const programName = (s.program || "").toLowerCase();

    const matchText =
      studentName.includes(term) ||
      programName.includes(term);

    let matchStatus = false;

    if (status === "All") matchStatus = true;

    if (status === "Paid" && s.totalCount > 0 && s.paidCount === s.totalCount)
      matchStatus = true;

    if (status === "Pending" && s.paidCount < s.totalCount)
      matchStatus = true;

    if (status === "Overdue" && s.emis.some(e => e.status === "Overdue"))
      matchStatus = true;

    return matchText && matchStatus;
  });

  renderPayments(filtered);
}

/* ================= ADD EMI ================= */
function addEMI() {
  const enrollment_id = studentSelect.value;

  let months = document.getElementById("emiPlan").value;
  if (months === "other") {
    months = document.getElementById("customPlan").value;
  }

  const amount = document.getElementById("amount").value;   // ✅ IMPORTANT
  const start_date = document.getElementById("dueDate").value;

  if (!enrollment_id || !months || !amount || !start_date) {
    alert("Fill all fields");
    return;
  }

  fetch(`${API}/emi/generate`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      enrollment_id: enrollment_id,
      months: months,
      start_date: start_date,
      amount: amount        // ✅ KEY FIX
    })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      closeModal();
      loadEMI();           // refresh EMI page
    } else {
      alert(data.error || "Failed to generate EMI");
    }
  });
}


/* ================= UTILS ================= */
function goToStudent(id) {
  window.location.href = `student-details.html?id=${id}`;
}

function formatDate(d) {
  return new Date(d).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric"
  });
}

function openModal() { modal.classList.remove("hidden"); }
function closeModal() { modal.classList.add("hidden"); }

function toggleCustomPlan() {
  const plan = document.getElementById("emiPlan").value;
  document
    .getElementById("customPlanWrapper")
    .classList.toggle("hidden", plan !== "other");
}


function downloadEmiReport() {
  // 🔥 No student ID needed
  window.location.href =
    "http://127.0.0.1:5000/api/emi/report";
}

