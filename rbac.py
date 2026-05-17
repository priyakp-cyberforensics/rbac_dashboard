from models import Role, Permission, RolePermission, User, AuditLog

def check_access(session, user, resource, action):
    # Deny by default if user or role missing
    if not user or not user.role:
        _log(session, user.username if user else "unknown", resource, action, "DENIED")
        return False

    permissions = [rp.permission for rp in user.role.permissions]
    allowed = any(p.resource == resource and p.action == action for p in permissions)
    _log(session, user.username, resource, action, "ALLOWED" if allowed else "DENIED")
    return allowed

def _log(session, username, resource, action, decision):
    session.add(AuditLog(user=username, resource=resource, action=action, decision=decision))
    session.commit()

def seed_defaults(session):
    # Seed roles
    if session.query(Role).count() == 0:
        admin = Role(name="Admin")
        analyst = Role(name="Analyst")
        intern = Role(name="Intern")
        session.add_all([admin, analyst, intern])
        session.commit()

        # Seed permissions
        perms = [
            Permission(resource="reports", action="read"),
            Permission(resource="reports", action="delete"),
            Permission(resource="docs", action="read"),
            Permission(resource="docs", action="update"),
            Permission(resource="dashboard", action="view"),
        ]
        session.add_all(perms)
        session.commit()

        # Map Admin to all perms
        for p in session.query(Permission).all():
            session.add(RolePermission(role=admin, permission=p))
        # Analyst: read reports, view dashboard
        session.add(RolePermission(role=analyst, permission=session.query(Permission).filter_by(resource="reports", action="read").one()))
        session.add(RolePermission(role=analyst, permission=session.query(Permission).filter_by(resource="dashboard", action="view").one()))
        # Intern: read docs, view dashboard
        session.add(RolePermission(role=intern, permission=session.query(Permission).filter_by(resource="docs", action="read").one()))
        session.add(RolePermission(role=intern, permission=session.query(Permission).filter_by(resource="dashboard", action="view").one()))
        session.commit()

        # Seed users
        session.add_all([
            User(username="alice", role=admin),
            User(username="bob", role=analyst),
            User(username="charlie", role=intern),
        ])
        session.commit()
