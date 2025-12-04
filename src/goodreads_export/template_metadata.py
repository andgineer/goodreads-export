"""Template metadata management."""

import hashlib
import json
from datetime import datetime
from pathlib import Path

from goodreads_export.templates import METADATA_FILE_NAME, TEMPLATE_FILES
from goodreads_export.version import VERSION


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of file.

    Args:
        file_path: Path to the file.

    Returns:
        Hash string in format 'sha256:...'.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        sha256.update(f.read())
    return f"sha256:{sha256.hexdigest()}"


def compute_content_hash(content: str) -> str:
    """Compute SHA-256 hash of content string.

    Args:
        content: Content string to hash.

    Returns:
        Hash string in format 'sha256:...'.
    """
    sha256 = hashlib.sha256()
    sha256.update(content.encode("utf-8"))
    return f"sha256:{sha256.hexdigest()}"


def load_metadata(templates_folder: Path) -> dict | None:
    """Load template metadata if exists.

    Args:
        templates_folder: Path to templates folder.

    Returns:
        Metadata dictionary or None if file doesn't exist.
    """
    metadata_path = templates_folder / METADATA_FILE_NAME
    if not metadata_path.exists():
        return None

    with open(metadata_path, encoding="utf-8") as f:
        return json.load(f)


def save_metadata(templates_folder: Path, metadata: dict) -> None:
    """Save metadata to file.

    Args:
        templates_folder: Path to templates folder.
        metadata: Metadata dictionary to save.
    """
    metadata_path = templates_folder / METADATA_FILE_NAME
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)


def create_metadata(templates_folder: Path, builtin_name: str) -> dict:
    """Create new metadata for templates.

    Args:
        templates_folder: Path to templates folder.
        builtin_name: Name of builtin template set used.

    Returns:
        New metadata dictionary.
    """
    now = datetime.now().isoformat()
    metadata = {
        "version": VERSION,
        "created_date": now,
        "last_updated_date": now,
        "builtin_name": builtin_name,
        "files": {},
    }

    for file_name in TEMPLATE_FILES:
        file_path = templates_folder / file_name
        if file_path.exists():
            file_hash = compute_file_hash(file_path)
            metadata["files"][file_name] = {
                "hash": file_hash,
                "size": file_path.stat().st_size,
            }

    return metadata


def update_metadata(templates_folder: Path, builtin_name: str) -> dict:
    """Update existing metadata or create new if doesn't exist.

    Args:
        templates_folder: Path to templates folder.
        builtin_name: Name of builtin template set used.

    Returns:
        Updated metadata dictionary.
    """
    existing_metadata = load_metadata(templates_folder)
    now = datetime.now().isoformat()

    if existing_metadata:
        metadata = {
            "version": VERSION,
            "created_date": existing_metadata.get("created_date", now),
            "last_updated_date": now,
            "builtin_name": builtin_name,
            "files": {},
        }
    else:
        metadata = {
            "version": VERSION,
            "created_date": now,
            "last_updated_date": now,
            "builtin_name": builtin_name,
            "files": {},
        }

    for file_name in TEMPLATE_FILES:
        file_path = templates_folder / file_name
        if file_path.exists():
            file_hash = compute_file_hash(file_path)
            metadata["files"][file_name] = {
                "hash": file_hash,
                "size": file_path.stat().st_size,
            }

    return metadata
