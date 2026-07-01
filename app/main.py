import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.config.config import config
from app.controllers.task_controller import router as task_router

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger("Main")

app = FastAPI(
    title="Task Management API",
    description="API for creating and managing tasks",
    version="1.0.0"
)

# Map PascalCase alias names to snake_case field names for error messages
_FIELD_ALIAS_TO_SNAKE = {
    "Title": "title",
    "Description": "description",
    "Priority": "priority",
    "Due_date": "due_date",
    "User_name": "user_name",
}


# Override validation error handler to return 400 with both formats
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()

    # Build a human-readable error string for the "error" key (snake_case field names)
    missing_fields = []
    other_field_errors = []

    for err in errors:
        loc = err.get("loc", [])
        # Extract the field name from loc (skip "body" prefix)
        field = loc[-1] if loc else ""
        snake_field = _FIELD_ALIAS_TO_SNAKE.get(str(field), str(field).lower())

        if err.get("type") == "value_error.missing":
            missing_fields.append(snake_field)
        else:
            other_field_errors.append(snake_field)

    if missing_fields:
        error_str = f"Missing required field(s): {', '.join(missing_fields)}"
    elif other_field_errors:
        error_str = f"Invalid value for field: {', '.join(other_field_errors)}"
    else:
        error_str = "Validation error"

    return JSONResponse(
        status_code=400,
        content={
            "detail": errors,
            "error": error_str,
        },
    )


app.include_router(task_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
