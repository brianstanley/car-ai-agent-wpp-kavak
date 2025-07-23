"""
User management service.
"""

import logging
from enum import Enum
from typing import Optional

import psycopg2
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from db.config import Config
from db.session import SessionLocal
from kavak_chatbot.models.db import UserDB
from kavak_chatbot.models.schemas.user import User

logger = logging.getLogger(__name__)


class UserServiceError(str, Enum):
    USER_NOT_FOUND = "User not found with id: {id}"
    ERROR_UPDATE_NAME = "Error updating user name: {error}"
    ERROR_UPDATE_PREFS = "Error updating preferences: {error}"
    ERROR_GET_BY_PHONE = "Error in get_user_by_phone: {error}"
    ERROR_GET_ALL = "Error in get_all_users: {error}"
    ERROR_GET_BY_ID = "Error in get_user_by_id: {error}"
    INVALID_UUID = "Invalid UUID format: {error}"
    ERROR_UPDATE_USER = "Error updating user: {error}"
    ERROR_DELETE_USER = "Error deleting user: {error}"


class UserService:
    def __init__(self):
        self.connection_string = Config.DATABASE_URL

    def _to_schema(self, db_user: UserDB) -> User:
        return User(
            id=db_user.id,
            phone_number=db_user.phone_number,
            name=db_user.name,
            preferences=db_user.preferences,
            created_at=db_user.created_at
        )

    def get_connection(self):
        return psycopg2.connect(self.connection_string)

    def get_or_create_user(self, phone_number: str) -> User:
        with SessionLocal() as session:
            user = session.scalar(select(UserDB).where(UserDB.phone_number == phone_number))
            if user:
                return self._to_schema(user)

            new_user = UserDB(phone_number=phone_number)
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            return self._to_schema(new_user)

    def update_user_name(self, id: str, name: str) -> Optional[User]:
        try:
            with SessionLocal() as session:
                db_user = session.scalar(select(UserDB).where(UserDB.id == id))
                if not db_user:
                    logger.warning(UserServiceError.USER_NOT_FOUND.value.format(id=id))
                    return None

                db_user.name = name
                session.commit()
                session.refresh(db_user)

                return self._to_schema(db_user)
        except SQLAlchemyError as e:
            logger.error(UserServiceError.ERROR_UPDATE_NAME.value.format(error=e))
            raise

    def update_preferences(self, id: str, preferences: dict) -> Optional[User]:
        try:
            with SessionLocal() as session:
                db_user = session.scalar(select(UserDB).where(UserDB.id == id))
                if not db_user:
                    logger.warning(UserServiceError.USER_NOT_FOUND.value.format(id=id))
                    return None

                current = db_user.preferences or {}
                if not isinstance(current, dict):
                    current = {}
                current.update(preferences)
                db_user.preferences = current
                # workaround for sqlalchemy not detecting changes in dict
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(db_user, "preferences")

                session.commit()
                session.refresh(db_user)

                return self._to_schema(db_user)
        except SQLAlchemyError as e:
            logger.error(UserServiceError.ERROR_UPDATE_PREFS.value.format(error=e))
            raise

    def get_user_by_phone(self, phone_number: str) -> Optional[User]:
        try:
            with SessionLocal() as session:
                db_user = session.scalar(select(UserDB).where(UserDB.phone_number == phone_number))
                return self._to_schema(db_user) if db_user else None
        except SQLAlchemyError as e:
            logger.error(UserServiceError.ERROR_GET_BY_PHONE.value.format(error=e))
            raise

    def get_all_users(self) -> list[User]:
        """Get all users from the database."""
        try:
            with SessionLocal() as session:
                db_users = session.scalars(select(UserDB)).all()
                return [self._to_schema(user) for user in db_users]
        except SQLAlchemyError as e:
            logger.error(UserServiceError.ERROR_GET_ALL.value.format(error=e))
            raise

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by their ID."""
        try:
            from uuid import UUID
            with SessionLocal() as session:
                db_user = session.scalar(select(UserDB).where(UserDB.id == UUID(user_id)))
                return self._to_schema(db_user) if db_user else None
        except SQLAlchemyError as e:
            logger.error(UserServiceError.ERROR_GET_BY_ID.value.format(error=e))
            raise
        except ValueError as e:
            logger.error(UserServiceError.INVALID_UUID.value.format(error=e))
            raise

    def update_user(self, user_id: str, name: Optional[str] = None, preferences: Optional[dict] = None) -> Optional[User]:
        """Update a user's name and/or preferences."""
        try:
            from uuid import UUID
            with SessionLocal() as session:
                db_user = session.scalar(select(UserDB).where(UserDB.id == UUID(user_id)))
                if not db_user:
                    logger.warning(UserServiceError.USER_NOT_FOUND.value.format(id=user_id))
                    return None
                # Update name if provided
                if name is not None:
                    db_user.name = name
                # Update preferences if provided
                if preferences is not None:
                    current = db_user.preferences or {}
                    if not isinstance(current, dict):
                        current = {}
                    current.update(preferences)
                    db_user.preferences = current
                    # Workaround for sqlalchemy not detecting changes in dict
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(db_user, "preferences")
                session.commit()
                session.refresh(db_user)
                return self._to_schema(db_user)
        except SQLAlchemyError as e:
            logger.error(UserServiceError.ERROR_UPDATE_USER.value.format(error=e))
            raise
        except ValueError as e:
            logger.error(UserServiceError.INVALID_UUID.value.format(error=e))
            raise

    def delete_user(self, user_id: str) -> bool:
        """Delete a user by their ID."""
        try:
            from uuid import UUID
            with SessionLocal() as session:
                db_user = session.scalar(select(UserDB).where(UserDB.id == UUID(user_id)))
                if not db_user:
                    logger.warning(UserServiceError.USER_NOT_FOUND.value.format(id=user_id))
                    return False
                session.delete(db_user)
                session.commit()
                return True
        except SQLAlchemyError as e:
            logger.error(UserServiceError.ERROR_DELETE_USER.value.format(error=e))
            raise
        except ValueError as e:
            logger.error(UserServiceError.INVALID_UUID.value.format(error=e))
            raise

