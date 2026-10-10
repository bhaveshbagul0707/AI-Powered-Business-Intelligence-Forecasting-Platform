"""MongoDB Atlas access, account authentication, and per-user sales storage."""
from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import re
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ASCENDING, MongoClient
from pymongo.errors import DuplicateKeyError, PyMongoError

from config import CONFIG

logger = logging.getLogger(__name__)

PASSWORD_ITERATIONS = 310_000
PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
USER_COLLECTION = "users"
DATASET_COLLECTION = "sales_datasets"
ROW_COLLECTION = "sales_rows"


class AtlasNotConfiguredError(RuntimeError):
    """Raised when MongoDB Atlas credentials are not configured."""


class InvalidCredentialsError(ValueError):
    """Raised when an email/password pair is invalid."""


class EmailAlreadyRegisteredError(ValueError):
    """Raised when a registration email is already in use."""


class AccountNotFoundError(ValueError):
    """Raised when an authenticated account no longer exists."""


class DatasetValidationError(ValueError):
    """Raised when a CSV cannot be saved as a sales dataset."""


class DatasetCleanupError(RuntimeError):
    """Raised when a new dataset is active but old rows could not be cleaned up."""


@st.cache_resource(show_spinner=False)
def get_database():
    """Connect to Atlas once per Streamlit process and prepare required indexes."""
    uri = CONFIG.mongodb_uri
    if not uri:
        raise AtlasNotConfiguredError("MONGODB_URI is not configured.")
    if "<" in uri or ">" in uri:
        raise AtlasNotConfiguredError(
            "MONGODB_URI still contains template placeholders. Replace them with the Atlas values."
        )
    if not uri.startswith(("mongodb://", "mongodb+srv://")):
        raise AtlasNotConfiguredError("MONGODB_URI must be a MongoDB connection URI.")

    client = MongoClient(
        uri,
        appname="DukaanDost",
        connectTimeoutMS=10_000,
        serverSelectionTimeoutMS=10_000,
    )
    client.admin.command("ping")
    database = client[CONFIG.mongodb_database]
    database[USER_COLLECTION].create_index("email", unique=True)
    database[DATASET_COLLECTION].create_index(
        [("owner_id", ASCENDING), ("_id", ASCENDING)]
    )
    database[ROW_COLLECTION].create_index(
        [
            ("owner_id", ASCENDING),
            ("dataset_id", ASCENDING),
            ("row_index", ASCENDING),
        ]
    )
    return database


def _password_record(password: str, salt: bytes | None = None) -> dict[str, str | int]:
    actual_salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        actual_salt,
        PASSWORD_ITERATIONS,
    )
    return {
        "password_salt": base64.b64encode(actual_salt).decode("ascii"),
        "password_hash": base64.b64encode(digest).decode("ascii"),
        "password_iterations": PASSWORD_ITERATIONS,
    }


def _verify_password(password: str, user: dict[str, Any]) -> bool:
    try:
        salt = base64.b64decode(user["password_salt"], validate=True)
        expected = base64.b64decode(user["password_hash"], validate=True)
        iterations = int(user["password_iterations"])
    except (KeyError, TypeError, ValueError):
        return False
    candidate = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations
    )
    return hmac.compare_digest(candidate, expected)


_DUMMY_PASSWORD_RECORD = _password_record("not-a-real-account-password")


def normalize_email(email: str) -> str:
    normalized = email.strip().casefold()
    if len(normalized) > 254 or not EMAIL_PATTERN.fullmatch(normalized):
        raise ValueError("Enter a valid email address.")
    return normalized


def register_user(email: str, password: str) -> dict[str, str]:
    normalized_email = normalize_email(email)
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters.")
    if len(password) > PASSWORD_MAX_LENGTH:
        raise ValueError(f"Password must be no more than {PASSWORD_MAX_LENGTH} characters.")

    document = {
        "email": normalized_email,
        **_password_record(password),
        "created_at": datetime.now(timezone.utc),
        "active_dataset_id": None,
    }
    try:
        result = get_database()[USER_COLLECTION].insert_one(document)
    except DuplicateKeyError as exc:
        raise EmailAlreadyRegisteredError(
            "An account with that email already exists."
        ) from exc
    return {"id": str(result.inserted_id), "email": normalized_email}


def authenticate_user(email: str, password: str) -> dict[str, str]:
    normalized_email = normalize_email(email)
    if len(password) > PASSWORD_MAX_LENGTH:
        raise InvalidCredentialsError("Email or password is incorrect.")
    user = get_database()[USER_COLLECTION].find_one({"email": normalized_email})
    if user is None:
        _verify_password(password, _DUMMY_PASSWORD_RECORD)
        raise InvalidCredentialsError("Email or password is incorrect.")
    if not _verify_password(password, user):
        raise InvalidCredentialsError("Email or password is incorrect.")
    return {"id": str(user["_id"]), "email": user["email"]}


def get_user(user_id: str) -> dict[str, str] | None:
    try:
        object_id = ObjectId(user_id)
    except (InvalidId, TypeError):
        return None
    user = get_database()[USER_COLLECTION].find_one(
        {"_id": object_id}, {"email": 1}
    )
    if user is None:
        return None
    return {"id": str(user["_id"]), "email": user["email"]}


def get_active_dataset_metadata(user_id: str) -> dict[str, Any] | None:
    user = get_database()[USER_COLLECTION].find_one(
        {"_id": ObjectId(user_id)}, {"active_dataset_id": 1}
    )
    if user is None:
        raise AccountNotFoundError("The signed-in account no longer exists.")
    dataset_id = user.get("active_dataset_id")
    if not dataset_id:
        return None
    metadata = get_database()[DATASET_COLLECTION].find_one(
        {"_id": dataset_id, "owner_id": user_id},
        {"_id": 1, "file_name": 1, "row_count": 1, "columns": 1, "uploaded_at": 1},
    )
    if metadata is None:
        raise DatasetValidationError("Saved dataset metadata is missing.")
    return metadata


def _to_mongo_value(value: Any) -> Any:
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    if not isinstance(value, (list, tuple, dict)):
        missing = pd.isna(value)
        if bool(missing):
            return None
        item = getattr(value, "item", None)
        if callable(item):
            return _to_mongo_value(item())
    return value


def _mongo_row_batches(
    owner_id: str, dataset_id: str, frame: pd.DataFrame, batch_size: int = 500
):
    batch: list[dict[str, Any]] = []
    for row_index, row in enumerate(frame.to_dict(orient="records")):
        batch.append(
            {
                "owner_id": owner_id,
                "dataset_id": dataset_id,
                "row_index": row_index,
                "values": [_to_mongo_value(value) for value in row.values()],
            }
        )
        if len(batch) == batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def save_sales_dataset(
    user_id: str, frame: pd.DataFrame, file_name: str
) -> dict[str, Any]:
    if frame.empty:
        raise DatasetValidationError("The uploaded CSV has no rows.")
    missing = [column for column in ("Sales", "Profit") if column not in frame]
    if missing:
        raise DatasetValidationError(
            f"Add the required column(s): {', '.join(missing)}."
        )
    for column in ("Sales", "Profit"):
        if pd.to_numeric(frame[column], errors="coerce").isna().any():
            raise DatasetValidationError(
                f"Every {column} value must be a valid number before saving."
            )

    database = get_database()
    user = database[USER_COLLECTION].find_one(
        {"_id": ObjectId(user_id)}, {"active_dataset_id": 1}
    )
    if user is None:
        raise AccountNotFoundError("The signed-in account no longer exists.")

    dataset_id = uuid.uuid4().hex
    safe_file_name = Path(file_name).name[:200] or "uploaded.csv"
    row_count = 0
    metadata = {
        "_id": dataset_id,
        "owner_id": user_id,
        "file_name": safe_file_name,
        "row_count": len(frame),
        "columns": list(frame.columns),
        "uploaded_at": datetime.now(timezone.utc),
    }
    try:
        for documents in _mongo_row_batches(user_id, dataset_id, frame):
            database[ROW_COLLECTION].insert_many(documents, ordered=True)
            row_count += len(documents)
        database[DATASET_COLLECTION].insert_one(metadata)
        result = database[USER_COLLECTION].update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"active_dataset_id": dataset_id}},
        )
        if result.matched_count != 1:
            raise AccountNotFoundError("The signed-in account no longer exists.")
    except (PyMongoError, AccountNotFoundError):
        try:
            database[ROW_COLLECTION].delete_many(
                {"owner_id": user_id, "dataset_id": dataset_id}
            )
            database[DATASET_COLLECTION].delete_one(
                {"_id": dataset_id, "owner_id": user_id}
            )
        except PyMongoError as cleanup_error:
            logger.error(
                "Could not clean up an incomplete dataset after an Atlas write failure (%s).",
                type(cleanup_error).__name__,
            )
        raise

    old_dataset_id = user.get("active_dataset_id")
    if old_dataset_id:
        try:
            database[ROW_COLLECTION].delete_many(
                {"owner_id": user_id, "dataset_id": old_dataset_id}
            )
            database[DATASET_COLLECTION].delete_one(
                {"_id": old_dataset_id, "owner_id": user_id}
            )
        except PyMongoError as exc:
            raise DatasetCleanupError(
                "The new CSV is saved, but the previous copy could not be removed. "
                "Contact the app administrator."
            ) from exc
    return metadata


def load_sales_dataset(user_id: str) -> tuple[pd.DataFrame, dict[str, Any]] | None:
    metadata = get_active_dataset_metadata(user_id)
    if metadata is None:
        return None

    cursor = get_database()[ROW_COLLECTION].find(
        {
            "owner_id": user_id,
            "dataset_id": metadata["_id"],
        },
        {"_id": 0, "row_index": 1, "values": 1},
    ).sort("row_index", ASCENDING)
    rows = [document["values"] for document in cursor]
    if len(rows) != metadata["row_count"]:
        raise DatasetValidationError(
            "Saved dataset is incomplete. Upload and save the CSV again."
        )
    return pd.DataFrame(rows, columns=metadata["columns"]), metadata


def delete_active_dataset(user_id: str) -> None:
    database = get_database()
    user = database[USER_COLLECTION].find_one(
        {"_id": ObjectId(user_id)}, {"active_dataset_id": 1}
    )
    if user is None:
        raise AccountNotFoundError("The signed-in account no longer exists.")
    dataset_id = user.get("active_dataset_id")
    if not dataset_id:
        return
    result = database[USER_COLLECTION].update_one(
        {"_id": ObjectId(user_id), "active_dataset_id": dataset_id},
        {"$set": {"active_dataset_id": None}},
    )
    if result.matched_count != 1:
        raise DatasetValidationError(
            "Your saved data changed in another session. Refresh and try again."
        )
    database[ROW_COLLECTION].delete_many(
        {"owner_id": user_id, "dataset_id": dataset_id}
    )
    database[DATASET_COLLECTION].delete_one(
        {"_id": dataset_id, "owner_id": user_id}
    )
