"""Standardized API response helpers."""

from typing import Any


def success_response(data: Any = None, message: str = "Success") -> dict:
    """Wrap data in a standard success envelope."""
    return {
        "success": True,
        "data": data,
        "message": message,
    }


def error_response(code: str, message: str) -> dict:
    """Wrap error info in a standard error envelope."""
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
    }
