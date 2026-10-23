"""HTTP layer: routes,dependencies and error rendering."""

import sqlite3
from collections.abc import Iterator
from fastapi import APIRouter, Depends, FastAPI , Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse


from .database import connection_scope
from .errors import AppError
from .models import Link
from .repository import LinkRepository
from .schemas import CreateLinkRequest, ErrorResponse, LinkResponse, LinkStatsResponse
from .service import LinkService

router = APIRouter()


def get_conn(request:Request)->Iterator [sqlite3.Connection]:
    yield from connection_scope(request.app.state.settings.db_path)

def get_service(request: Request, conn: sqlite3.Connection = Depends(get_conn)) -> LinkService:
    return LinkService(
        LinkRepository(conn),clock=request.app.state.clock

    )
def _short_url(request:Request,code:str)->str:
    base = request.app.state.settings.base_url or str(request.base_url).rstrip("/")
    return f"{base}/{code}"

def _link_response(request:Request,link:Link)->LinkResponse:
    return LinkResponse(
        code = link.code,
        short_url=_short_url(request, link.code),
        original_url =link.original_url,
        created_at = link.created_at,
        expires_at = link.expires_at,
    )
@router.post(
    "/links",
    response_model = LinkResponse,
    status_code = 201,
    responses = {409: {"model":ErrorResponse},422:{"model":ErrorResponse}},
    summary = "Create a short link",
)
def create_link(body:CreateLinkRequest,request:Request,service:LinkService = Depends(get_service)):
    link = service.create_link(body.url,alias=body.alias,expires_at = body.expires_at)
    return _link_response(request,link)

@router.get(
    "/links/{code}/stats",
    response_model = LinkStatsResponse,
    responses = {404: {"model":ErrorResponse}},
    summary = "Click statistics for a link",
)
def link_stats(code:str , service:LinkService = Depends(get_service)):
    link = service.get_stats(code)
    return LinkStatsResponse(
        code =link.code,
        original_url = link.original_url,
        total_clicks =link.click_count,
        last_clicked_at = link.last_clicked_at,
        created_at = link.created_at,
        expires_at = link.expires_at,
        is_expired = service.is_expired(link),
    )


@router.get(
    "/{code}",
    status_code=302,
    response_class =RedirectResponse,
    responses = {404:{"model":ErrorResponse},410:{"model":ErrorResponse}},
    summary = "Redirect to the original URL",
)

def follow_link(code:str, service:LinkService = Depends(get_service)):
    link= service.resolve(code)

    return RedirectResponse(link.original_url,status_code=302,headers= {"Cache-Control":"no-store"})


def _error_body(error: str, message: str, details: list[dict] | None = None) -> dict:
    body = {"error":error,"message":message}
    if details:
        body["details"] = details
    return body

def register_error_handlers(app:FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request,exc:AppError):
        return JSONResponse(status_code = exc.status_code,content = _error_body(exc.error,exc.message))

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_:Request,exc:RequestValidationError):
        details = []
        for err in exc.errors():
            field = ".".join(str(p) for p in err ["loc"] if p!="body")
            message = err["msg"].removeprefix("Value error, ")
            details.append({"field":field or "body","message":message})

        summary = "; ".join(f"{d['field']}: {d['message']}" for d in details)
        return JSONResponse(
            status_code=422,
            content=_error_body("validation_error",f"Invalid request. {summary}",details),
        )