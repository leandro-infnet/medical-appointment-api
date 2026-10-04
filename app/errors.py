"""Erros de entrada sem repetir dados clínicos, tokens ou segredos enviados."""
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def validation_error_response(_request: Request, error: Exception) -> JSONResponse:
    if not isinstance(error, RequestValidationError):
        raise error
    detalhes = [{"loc": item["loc"], "type": item["type"], "msg": item["msg"]}
                for item in error.errors()]
    return JSONResponse({"detail": detalhes}, status_code=422, headers={"Cache-Control": "no-store"})
