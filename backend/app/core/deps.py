from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User

# Auth is disabled for local testing: every request runs as a single
# default user, created on first use. Re-enable token validation here to
# restore real authentication.
DEFAULT_USER_EMAIL = "demo@buildtrack.local"


def get_current_user(db: Session = Depends(get_db)) -> User:
    user = db.query(User).filter(User.email == DEFAULT_USER_EMAIL).first()
    if user is None:
        user = User(
            email=DEFAULT_USER_EMAIL,
            hashed_password="",
            full_name="Demo User",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
