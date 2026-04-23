from flask import Blueprint, request, jsonify, session

auth_bp = Blueprint("auth", __name__)

# TEMP ADMIN (replace later with DB / Replit OAuth)
ADMIN_USER = {
    "email": "admin@analogica.com",
    "password": "admin123"
}

# ================= LOGIN =================
@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    data = request.json

    email = data.get("email")
    password = data.get("password")

    if email == ADMIN_USER["email"] and password == ADMIN_USER["password"]:
        session["admin_logged_in"] = True
        session["admin_email"] = email
        return jsonify({"success": True})

    return jsonify({"success": False, "message": "Invalid credentials"}), 401


# ================= LOGOUT =================
@auth_bp.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})


# ================= CHECK SESSION =================
@auth_bp.route("/api/auth/me")
def check_auth():
    if session.get("admin_logged_in"):
        return jsonify({
            "authenticated": True,
            "email": session.get("admin_email")
        })

    return jsonify({"authenticated": False}), 401
