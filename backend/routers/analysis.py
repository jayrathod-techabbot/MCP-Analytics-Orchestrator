from fastapi import APIRouter, HTTPException

from backend.models.schemas import AnalyzeRequest, AnalyzeResponse, ErrorResponse
from backend.services.openai_service import run_analysis
from backend.utils.file_handler import resolve_upload_path
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    responses={404: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
)
async def analyze(request: AnalyzeRequest):
    file_path = resolve_upload_path(request.file_id)
    if file_path is None:
        raise HTTPException(status_code=404, detail="File not found. Please upload again.")

    try:
        result = run_analysis(
            file_path=str(file_path.resolve()),
            question=request.question,
            conversation_history=request.conversation_history,
        )

        return AnalyzeResponse(
            answer=result["answer"],
            charts=result.get("charts", []),
            summary=result.get("summary"),
            insights=result.get("insights", []),
            tool_calls_made=result.get("tool_calls_made", []),
            tokens_used=result.get("tokens_used"),
        )
    except Exception as e:
        logger.error("Analysis failed: %s", str(e))
        raise HTTPException(status_code=502, detail=f"Analysis failed: {str(e)}")
