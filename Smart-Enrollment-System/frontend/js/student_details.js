const API = "http://127.0.0.1:5000/api";

// DOM Elements
const studentTitle = document.getElementById("studentTitle");
const studentNameEl = document.getElementById("studentName");
const studentProgramEl = document.getElementById("studentProgram");
const studentJoinDateEl = document.getElementById("studentJoinDate");

const studentPhoneEl = document.getElementById("studentPhone");
const studentPaymentPlanEl = document.getElementById("studentPaymentPlan");


const statTotal = document.getElementById("statTotal");
const statPaid = document.getElementById("statPaid");
const statRemaining = document.getElementById("statRemaining");
const statPercent = document.getElementById("statPercent");

const emiTableBody = document.getElementById("emiTableBody");

document.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(window.location.search);
  const studentId = params.get("id");

  if (!studentId) {
    document.body.innerHTML = "<h2>Student ID missing</h2>";
    return;
  }

  loadStudentDetails(studentId);
});

/* ===========================
   LOAD STUDENT + EMI DETAILS
=========================== */
function loadStudentDetails(studentId) {
  fetch(`${API}/student/${studentId}`, { credentials: "include" })
    .then(res => res.json())
    .then(data => {
      console.log("Student API response:", data);

      // ================= STUDENT INFO =================
      studentTitle.innerText = `Student Profile - ${data.name}`;
      studentNameEl.innerText = data.email || "-";
      studentProgramEl.innerText = data.program || "-";
      studentJoinDateEl.innerText = data.join_date || "-";
      studentPhoneEl.innerText = data.phone || "Not Available";   // ✅ ADD THIS


      const paymentType = data.payment_type;
      const courseAmount = data.amount || 0;
      const emis = data.emis || [];

     // ===== Set Payment Plan Display =====
      if (paymentType === "EMI") {
        studentPaymentPlanEl.innerText = `EMI - ${data.emi_months || 0} Months`;
      } else {
        studentPaymentPlanEl.innerText = "Full Payment";
      }
      let total = 0;
      let paid = 0;

      emiTableBody.innerHTML = "";

      // ================= EMI TABLE LOGIC =================
      if (paymentType !== "EMI") {
        // FULL PAYMENT
        total = courseAmount;
        paid = courseAmount;

        emiTableBody.innerHTML =
          `<tr><td colspan="5">Full payment – no installments</td></tr>`;
      }
      else if (emis.length === 0) {
        // EMI BUT NOT GENERATED
        total = courseAmount;
        paid = 0;

        emiTableBody.innerHTML =
          `<tr><td colspan="5">Installment schedule not generated yet</td></tr>`;
      }
      else {
        // EMI GENERATED
        emis.forEach(emi => {
          total += emi.amount;
          if (emi.status === "Paid") paid += emi.amount;

          emiTableBody.innerHTML += `
                <tr>
                  <td><strong>#${emi.emi_no}</strong></td>
                  <td>₹${emi.amount}</td>
                  <td>${emi.due_date || "-"}</td>
                  <td>
                    <span class="status-badge ${
                      emi.status === "Paid"
                        ? "status-paid"
                        : emi.status === "Overdue"
                        ? "status-overdue"
                        : "status-pending"
                    }">
                      ${emi.status}
                    </span>
                  </td>
                  <td>${emi.paid_date ? formatDate(emi.paid_date) : "-"}</td>
                  <td>
                    ${
                      emi.status === "Paid"
                        ? `<button class="undo-btn"
                              onclick="undoEmiPaid(${studentId}, ${emi.emi_no})">
                              Undo
                          </button>`
                        : `<button class="pay-btn"
                              onclick="markEmiPaid(${studentId}, ${emi.emi_no})">
                              Mark Paid
                          </button>`
                    }
                  </td>
                </tr>
                `;
        });
      }

      // ================= STATS =================
      const remaining = total - paid;
      const percent = total ? Math.round((paid / total) * 100) : 0;

      statTotal.innerText = `₹${total}`;
      statPaid.innerText = `₹${paid}`;
      statRemaining.innerText = `₹${remaining}`;
      statPercent.innerText = `${percent}%`;
    })
    .catch(err => {
      console.error("Student details error:", err);
      alert("Failed to load student details");
    });
}

/* ===========================
   MARK EMI AS PAID
=========================== */
function markEmiPaid(enrollmentId, emiNo) {
  if (!confirm(`Mark EMI #${emiNo} as Paid?`)) return;

  fetch(`${API}/emi/pay`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({
      enrollment_id: enrollmentId,
      emi_no: emiNo
    })
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        loadStudentDetails(enrollmentId);
      } else {
        alert("Failed to update EMI");
      }
    });
}
function undoEmiPaid(enrollmentId, emiNo) {
  if (!confirm(`Undo payment for EMI #${emiNo}?`)) return;

  fetch(`${API}/emi/undo`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({
      enrollment_id: enrollmentId,
      emi_no: emiNo
    })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      loadStudentDetails(enrollmentId);
    } else {
      alert("Failed to undo EMI payment");
    }
  });
}

function formatDate(dateStr) {
  if (!dateStr) return "-";
  return new Date(dateStr).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric"
  });
}



function downloadStudentReport() {
  const params = new URLSearchParams(window.location.search);
  const studentId = params.get("id");

  if (!studentId) {
    alert("Student ID missing");
    return;
  }

  window.location.href = `${API}/student/report/pdf/${studentId}`;
}
