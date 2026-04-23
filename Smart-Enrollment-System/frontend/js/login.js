const API = "http://127.0.0.1:5000/api";

function login() {
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value.trim();

  if (!username || !password) {
    alert("Please enter username and password");
    return;
  }

  fetch(`${API}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({
      username: username,
      password: password
    })
  })
  .then(res => {
    if (!res.ok) throw new Error();
    return res.json();
  })
  .then(() => {
    window.location.href = "/dashboard";
  })
  .catch(() => {
    alert("Invalid username or password");
  });
}


function showForgot() {
  document.getElementById("forgotBox").style.display = "block";
}

function resetPassword() {
  const username = document.getElementById("fpUsername").value.trim();
  const newPassword = document.getElementById("fpNewPassword").value.trim();

  if (!username || !newPassword) {
    alert("Please fill all fields");
    return;
  }

  fetch(`${API}/forgot-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: username,
      new_password: newPassword
    })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      alert("Password reset successful. Please login.");
      window.location.reload();
    } else {
      alert(data.error);
    }
  });
}
