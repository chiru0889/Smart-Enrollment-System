document.addEventListener("DOMContentLoaded", () => {

  const API = "http://127.0.0.1:5000/api";

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
 
  const cards = document.getElementById("studentCards");
  const searchInput = document.getElementById("searchInput");

  const modal = document.getElementById("studentModal");
  const openModal = document.getElementById("openModal");
  const closeModal = document.getElementById("closeModal");
  const addStudentBtn = document.getElementById("addStudent");

  const paymentFilter = document.getElementById("paymentFilter");
  paymentFilter.addEventListener("change", filterEnrollments);
  
 
 
  

  /* INPUT REFERENCES */
  const name = document.getElementById("name");
  const email = document.getElementById("email");
  const phone = document.getElementById("phone");
  const program = document.getElementById("program");
  const date = document.getElementById("date");
  

  const paymentType = document.getElementById("paymentType");
  const amountField = document.getElementById("amount");
 
   

  const paymentModal = document.getElementById("paymentModal");
  const paymentAmountInput = document.getElementById("paymentAmount");
  const setFullBtn = document.getElementById("setFullBtn");
  const setEmiBtn = document.getElementById("setEmiBtn");
  const closePaymentModal = document.getElementById("closePaymentModal");

  



  
  

  /* =========================
     🔒 AUTH CHECK
  ========================= */
  fetch(`${API}/protected`, { credentials: "include" })
    .then(res => {
      if (!res.ok) window.location.href = "/";
    });

  /* =========================
     MODAL
  ========================= */
  // hide amount initially
paymentType.onchange = () => {
  if (paymentType.value === "FULL") {
    amountField.style.display = "block";   // show amount field
  } else {
    amountField.style.display = "none";    // hide for EMI / empty
    amountField.value = "";                // clear value
  }
};


/* ================= MODAL ================= */
openModal.onclick = () => modal.style.display = "flex";
closeModal.onclick = () => modal.style.display = "none";




  /* =========================
     LOAD ENROLLMENTS
  ========================= */
  function loadEnrollments() {
    fetch(`${API}/enrollments`, { credentials: "include" })
      .then(res => res.json())
      .then(data => {
        cards.innerHTML = "";

        data.forEach(s => {

          /* ✅ SOURCE OF TRUTH */
         /* ✅ SOURCE OF TRUTH */
            const hasAmount =
              s.amount !== null &&
              s.amount !== "" &&
              !isNaN(Number(s.amount)) &&
              Number(s.amount) > 0;

            const isEMI = s.payment_type === "EMI";
            const isFull = s.payment_type === "FULL";

            let badgeText = "Payment Pending";
            let badgeClass = "badge-pending";
            let topBorderColor = "border-gray-400";

            let progressPercent = 0;
            let progressText = "Pending";
            let progressColor = "bg-gray-400";

            /* ✅ FINAL DECISION */
            if (isFull && hasAmount) {
              badgeText = "Full Payment";
              badgeClass = "badge-full";
              topBorderColor = "border-green-500";

              progressPercent = 100;
              progressText = "Paid";
              progressColor = "bg-green-600";
            }

            if (isEMI && hasAmount) {
              badgeText = "EMI Plan";
              badgeClass = "badge-emi";
              topBorderColor = "border-teal-500";

              const paid = s.emi_paid || 0;
              const total = s.emi_total || 0;

              progressPercent = total ? (paid / total) * 100 : 0;
              progressText = total ? `${paid}/${total} EMIs` : "EMI Pending";
              progressColor = "bg-teal-600";
            }




          const joinDate = s.join_date
            ? new Date(s.join_date).toLocaleDateString()
            : "-";

          const card = document.createElement("div");
          card.className = `student-card ${topBorderColor}`;

          card.innerHTML = `
                <div class="card-header">
                  <div class="left-section">
                    <div class="avatar-circle">${s.name ? s.name.charAt(0) : "?"}</div>
                    <div>
                      <h3>${s.name}</h3>
                      <p class="program-text">${s.program}</p>
                    </div>
                  </div>

                  <div class="right-actions">
                    <button onclick="editStudent('${s.id}', event)">✏️</button>
                    <button onclick="deleteStudent('${s.id}', event)">🗑️</button>
                  </div>
                </div>

                <div class="card-middle">
                  <div>
                    <span class="date-label">Joined</span><br>
                    <span class="date-value">${joinDate}</span>
                  </div>
                  <div class="status-badge ${badgeClass}">${badgeText}</div>
                </div>

                <div class="progress-container">
                  <div class="bar-bg">
                    <div class="bar-fill ${progressColor}" style="width:${progressPercent}%"></div>
                  </div>
                  <div class="progress-text">${progressText}</div>
                </div>

                <div class="divider"></div>

                <div class="card-footer">
                  <span>Total Fee</span>
                  <span class="fee-amount">₹${s.amount || "-"}</span>
                </div>

              ${!hasAmount ? `
                <button class="set-payment-btn"
                  onclick="openPaymentSetup(${s.id}, event)">
                  Set Payment
                </button>
              ` : ""}




                ${isEMI ? `
                  <button class="view-emi-btn"
                    onclick="window.location.href='emi.html?id=${s.id}'">
                    View EMIs
                  </button>
                ` : ""}
              `;


          card.onclick = e => {
            if (!e.target.closest("button")) {
              window.location.href = `student-details.html?id=${s.id}`;
            }
          };

          cards.appendChild(card);
        });
      });
  }

  loadEnrollments();

  /* =========================
     ADD STUDENT
  ========================= */
  addStudentBtn.onclick = () => {
  const payload = {
    name: name.value.trim(),
    email: email.value.trim(),
    phone: phone.value.trim(),   // ✅ ADD THIS LINE
    program: program.value.trim(),
    date: date.value,
    payment_type: paymentType.value || null,
    amount: paymentType.value === "FULL" ? amountField.value : null
};


  // ✅ validation only for FULL payment
  if (paymentType.value === "FULL" && !amountField.value) {
    alert("Please enter total amount for full payment");
    return;
  }

  fetch(`${API}/enrollment/add`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  }).then(() => {
    modal.style.display = "none";
    loadEnrollments();
  });
};


  /* =========================
     DELETE
  ========================= */
  window.deleteStudent = (id, e) => {
    e.stopPropagation();
    if (confirm("Delete this enrollment?")) {
      fetch(`${API}/enrollment/delete`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id })
      }).then(() => loadEnrollments());
    }
  };

  /* =========================
     EDIT
  ========================= */
  window.editStudent = (id, e) => {
    e.stopPropagation();
    const newName = prompt("Enter new name:");
    if (newName) {
      fetch(`${API}/enrollment/update`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, name: newName })
      }).then(() => loadEnrollments());
    }
  };

  /* =========================
     SEARCH
  ========================= */
  searchInput.oninput = () => {
    const value = searchInput.value.toLowerCase();
    document.querySelectorAll(".student-card").forEach(card => {
      card.style.display = card.innerText.toLowerCase().includes(value)
        ? "block"
        : "none";
    });
  };

/* =========================
   SET PAYMENT MODAL LOGIC
========================= */

/* =========================
   SET PAYMENT MODAL LOGIC
========================= */

let selectedEnrollmentId = null;

window.openPaymentSetup = (id, e) => {
  e.stopPropagation();
  console.log("SET PAYMENT FOR ID:", id); // ✅ DEBUG (keep for now)
  selectedEnrollmentId = id;
  paymentModal.classList.remove("hidden");
};

closePaymentModal.onclick = () => {
  paymentModal.classList.add("hidden");
  paymentAmountInput.value = "";
  selectedEnrollmentId = null;
};


/* ===== FULL PAYMENT ===== */
document.getElementById("setFullBtn").onclick = () => {
  const amount = document.getElementById("paymentAmount").value;

  if (!amount || Number(amount) <= 0) {
    alert("Enter valid amount");
    return;
  }

  fetch(`${API}/enrollment/set-payment`, {   // ✅ CORRECT
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      id: selectedEnrollmentId,
      payment_type: "FULL",
      amount: amount
    })
  }).then(() => {
    paymentModal.classList.add("hidden");
    loadEnrollments();
  });
};

/* ===== EMI PAYMENT ===== */
document.getElementById("setEmiBtn").onclick = () => {
  const amount = document.getElementById("paymentAmount").value;

  if (!amount || Number(amount) <= 0) {
    alert("Enter valid amount");
    return;
  }

  fetch(`${API}/enrollment/set-payment`, {   // ✅ CORRECT
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      id: selectedEnrollmentId,
      payment_type: "EMI",
      amount: amount
    })
  }).then(() => {
    paymentModal.classList.add("hidden");
    loadEnrollments();
  });
};
});

function filterEnrollments() {

  const searchValue = document
    .getElementById("searchInput")
    .value.toLowerCase();

  const paymentValue = document
    .getElementById("paymentFilter")
    .value;

  const cards = document.querySelectorAll(".student-card");

  cards.forEach(card => {

    const text = card.innerText.toLowerCase();

    const matchSearch = text.includes(searchValue);

    let matchPayment = true;

    if (paymentValue !== "All") {
      matchPayment = text.includes(paymentValue.toLowerCase());
    }

    card.style.display =
      (matchSearch && matchPayment) ? "block" : "none";
  });
}
