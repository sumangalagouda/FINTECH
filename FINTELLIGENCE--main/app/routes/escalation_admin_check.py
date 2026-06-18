from app.models.user import User


def is_admin(user_id: str) -> bool:
    if not user_id:
        return False
    user = User.query.get(user_id)
    return bool(user and user.role == 'admin')

