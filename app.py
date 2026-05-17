from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base, User, Role, Permission, RolePermission, AuditLog
from rbac import check_access, seed_defaults
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change-this-in-production"

engine = create_engine("sqlite:///db.sqlite3", connect_args={"check_same_thread": False})
Base.metadata.create_all(engine)
Session = scoped_session(sessionmaker(bind=engine))

# Seed demo roles/permissions/users if empty
with app.app_context():
    seed_defaults(Session())

@app.teardown_appcontext
def shutdown_session(exception=None):
    Session.remove()

@app.route("/")
def intro():
    return render_template("intro.html")

@app.route("/dashboard")
def dashboard():
    s = Session()
    roles = s.query(Role).all()
    users = s.query(User).all()
    perms = s.query(Permission).all()
    allowed = s.query(AuditLog).filter(AuditLog.decision == "ALLOWED").count()
    denied = s.query(AuditLog).filter(AuditLog.decision == "DENIED").count()
    return render_template("dashboard.html", roles=roles, users=users, perms=perms,
                           allowed=allowed, denied=denied)

@app.route("/users", methods=["GET", "POST"])
def users():
    s = Session()
    roles = s.query(Role).all()
    if request.method == "POST":
        username = request.form.get("username")
        role_id = request.form.get("role_id")
        if not username or not role_id:
            flash("Username and role are required.", "danger")
        else:
            role = s.query(Role).get(int(role_id))
            s.add(User(username=username, role=role))
            s.commit()
            flash(f"User '{username}' created.", "success")
        return redirect(url_for("users"))
    users = s.query(User).all()
    return render_template("users.html", users=users, roles=roles)

@app.route("/users/<int:user_id>/delete", methods=["POST"])
def delete_user(user_id):
    s = Session()
    u = s.query(User).get(user_id)
    if u:
        s.delete(u)
        s.commit()
        flash("User deleted.", "info")
    return redirect(url_for("users"))

@app.route("/roles", methods=["GET", "POST"])
def roles():
    s = Session()
    perms = s.query(Permission).all()
    if request.method == "POST":
        name = request.form.get("name")
        if not name:
            flash("Role name is required.", "danger")
        else:
            r = Role(name=name)
            s.add(r)
            s.commit()
            flash(f"Role '{name}' created.", "success")
        return redirect(url_for("roles"))
    roles = s.query(Role).all()
    return render_template("roles.html", roles=roles, perms=perms)

@app.route("/roles/<int:role_id>/assign", methods=["POST"])
def assign_permission(role_id):
    s = Session()
    role = s.query(Role).get(role_id)
    permission_ids = request.form.getlist("permissions")
    # Clear existing permissions
    s.query(RolePermission).filter(RolePermission.role_id == role_id).delete()
    s.commit()
    # Assign new set
    for pid in permission_ids:
        perm = s.query(Permission).get(int(pid))
        s.add(RolePermission(role=role, permission=perm))
    s.commit()
    flash("Permissions updated.", "success")
    return redirect(url_for("roles"))

@app.route("/permissions", methods=["POST"])
def create_permission():
    s = Session()
    resource = request.form.get("resource")
    action = request.form.get("action")
    if not resource or not action:
        flash("Resource and action are required.", "danger")
    else:
        s.add(Permission(resource=resource, action=action))
        s.commit()
        flash("Permission created.", "success")
    return redirect(url_for("roles"))

@app.route("/audit")
def audit():
    s = Session()
    logs = s.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(200).all()
    return render_template("audit.html", logs=logs)

@app.route("/simulate", methods=["POST"])
def simulate():
    s = Session()
    user_id = int(request.form.get("user_id"))
    resource = request.form.get("resource")
    action = request.form.get("action")
    user = s.query(User).get(user_id)
    allowed = check_access(s, user, resource, action)
    status = "ALLOWED" if allowed else "DENIED"
    
    # Log the access attempt to the audit log
    log_entry = AuditLog(
        user=user.username,  # Store the username as a string
        resource=resource,
        action=action,
        decision=status,
        timestamp=datetime.utcnow()
    )
    s.add(log_entry)
    s.commit()
    
    flash(f"Action {action} on {resource} for {user.username}: {status}", "info")
    return redirect(url_for("dashboard"))

@app.route("/stats.json")
def stats_json():
    s = Session()
    allowed = s.query(AuditLog).filter(AuditLog.decision == "ALLOWED").count()
    denied = s.query(AuditLog).filter(AuditLog.decision == "DENIED").count()
    return jsonify({"allowed": allowed, "denied": denied})

@app.route("/reset-counters", methods=["POST"])
def reset_counters():
    s = Session()
    try:
        # Delete all audit logs
        s.query(AuditLog).delete()
        s.commit()
        return jsonify({"status": "success", "message": "Counters reset successfully"})
    except Exception as e:
        s.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
