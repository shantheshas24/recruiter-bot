"""Custom exception types and error-response helpers."""

from fastapi import HTTPException, status


class NotFoundError(HTTPException):
    """Resource not found (404)."""

    def __init__(self, resource: str, resource_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with id {resource_id} not found.",
        )


class DuplicateError(HTTPException):
    """Duplicate resource (409)."""

    def __init__(self, detail: str) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


class DatabaseError(HTTPException):
    """Unexpected database error (500). Never exposes internals."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected database error occurred. Please try again later.",
        )
