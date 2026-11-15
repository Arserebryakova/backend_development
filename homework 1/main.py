import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from routers.predict import router as prediction_router
from schemas import ValidationErrorResponse

logger = logging.getLogger(__name__)

app = FastAPI(title="Сервис модерации объявлений", version="1.0.0")
app.include_router(prediction_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # Do not echo request data or validator internals in the response.
    errors = [
        {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
        for error in exc.errors()
    ]
    response = ValidationErrorResponse(detail=errors)
    return JSONResponse(status_code=400, content=response.model_dump())


@app.exception_handler(Exception)
async def internal_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled error for %s %s", request.method, request.url.path, exc_info=exc
    )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


def custom_openapi() -> dict:
    if app.openapi_schema is None:
        schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
        # Request validation uses 400 instead of FastAPI's default 422.
        schema["paths"]["/predict"]["post"]["responses"].pop("422", None)
        app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi
