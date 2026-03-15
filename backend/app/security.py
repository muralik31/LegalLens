"""Security utilities for LegalLens application."""

from __future__ import annotations

import re
from pathlib import Path

import magic
import structlog

logger = structlog.get_logger(__name__)

# MIME type mappings for validation
ALLOWED_MIME_TYPES = {
    "application/pdf": [".pdf"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    "image/jpeg": [".jpg", ".jpeg"],
    "image/png": [".png"],
    "text/plain": [".txt"],
}


class SecurityValidationError(ValueError):
    """Raised when security validation fails."""

    pass


def validate_file_content(file_path: Path, declared_content_type: str) -> tuple[bool, str]:
    """
    Validate file content matches declared content type using magic numbers.

    Args:
        file_path: Path to the file to validate
        declared_content_type: Content-Type from upload

    Returns:
        Tuple of (is_valid, actual_mime_type)

    Raises:
        SecurityValidationError: If validation fails
    """
    try:
        # Get actual MIME type from file content
        mime = magic.Magic(mime=True)
        actual_mime_type = mime.from_file(str(file_path))

        # Normalize MIME types (some variations exist)
        actual_mime_normalized = _normalize_mime_type(actual_mime_type)
        declared_mime_normalized = _normalize_mime_type(declared_content_type)

        # Check if actual type is allowed
        if actual_mime_normalized not in ALLOWED_MIME_TYPES:
            logger.warning(
                "file_validation_failed",
                declared=declared_content_type,
                actual=actual_mime_type,
                reason="unsupported_type",
            )
            raise SecurityValidationError(
                f"File type not supported. Detected: {actual_mime_type}"
            )

        # Verify declared type matches actual type (or is compatible)
        if not _mime_types_compatible(declared_mime_normalized, actual_mime_normalized):
            logger.warning(
                "file_validation_failed",
                declared=declared_content_type,
                actual=actual_mime_type,
                reason="type_mismatch",
            )
            raise SecurityValidationError(
                f"File content does not match declared type. "
                f"Declared: {declared_content_type}, Actual: {actual_mime_type}"
            )

        logger.info(
            "file_validated",
            declared=declared_content_type,
            actual=actual_mime_type,
        )
        return True, actual_mime_type

    except SecurityValidationError:
        raise
    except Exception as e:
        logger.error("file_validation_error", error=str(e))
        raise SecurityValidationError(f"File validation failed: {e}") from e


def _normalize_mime_type(mime_type: str) -> str:
    """Normalize MIME type for comparison."""
    # Remove charset and other parameters
    mime_type = mime_type.split(";")[0].strip().lower()

    # Handle common variations
    if mime_type in ("application/msword", "application/x-pdf"):
        return "application/pdf"
    if "image/jpg" in mime_type:
        return "image/jpeg"

    return mime_type


def _mime_types_compatible(declared: str, actual: str) -> bool:
    """Check if declared and actual MIME types are compatible."""
    if declared == actual:
        return True

    # Allow some flexibility for text files
    if declared == "text/plain" and actual.startswith("text/"):
        return True

    # Allow image format variations
    if declared in ("image/jpeg", "image/jpg") and actual in ("image/jpeg", "image/jpg"):
        return True

    return False


def sanitize_for_llm(text: str, max_length: int = 15000) -> str:
    """
    Sanitize text before sending to LLM to prevent prompt injection.

    Args:
        text: Input text to sanitize
        max_length: Maximum length to truncate to

    Returns:
        Sanitized text
    """
    # Detect potential prompt injection patterns
    dangerous_patterns = [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"you\s+are\s+now",
        r"system\s*:",
        r"assistant\s*:",
        r"<\|im_start\|>",
        r"<\|im_end\|>",
        r"###\s*instruction",
        r"disregard\s+(all\s+)?(previous|above)",
    ]

    text_lower = text.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, text_lower):
            logger.warning(
                "prompt_injection_detected",
                pattern=pattern,
                text_preview=text[:100],
            )
            # Don't block, but log for monitoring
            # In production, you might want to strip or block

    # Truncate to max length
    if len(text) > max_length:
        text = text[:max_length] + "\n[...truncated for length...]"
        logger.info("text_truncated", original_length=len(text), max_length=max_length)

    return text


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and other attacks.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove path separators
    filename = filename.replace("/", "_").replace("\\", "_")

    # Remove null bytes
    filename = filename.replace("\x00", "")

    # Only allow alphanumeric, dash, underscore, dot
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)

    # Prevent hidden files
    if filename.startswith("."):
        filename = "_" + filename

    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        filename = name[:250] + ("." + ext if ext else "")

    return filename


def validate_email(email: str) -> bool:
    """
    Validate email format (basic check).

    Args:
        email: Email address to validate

    Returns:
        True if valid format
    """
    # Basic email regex (pydantic EmailStr does better validation)
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def check_password_strength(password: str) -> tuple[bool, list[str]]:
    """
    Check password strength and return recommendations.

    Args:
        password: Password to check

    Returns:
        Tuple of (is_strong, list of issues)
    """
    issues = []

    if len(password) < 12:
        issues.append("Password should be at least 12 characters")

    if not re.search(r"[A-Z]", password):
        issues.append("Password should contain at least one uppercase letter")

    if not re.search(r"[a-z]", password):
        issues.append("Password should contain at least one lowercase letter")

    if not re.search(r"\d", password):
        issues.append("Password should contain at least one digit")

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        issues.append("Password should contain at least one special character")

    # Check common passwords (simplified)
    common_passwords = [
        "password",
        "12345678",
        "qwerty",
        "abc123",
        "password123",
        "admin",
        "letmein",
    ]
    if password.lower() in common_passwords:
        issues.append("Password is too common")

    return len(issues) == 0, issues
