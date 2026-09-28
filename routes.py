from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.ai_core.gemini_generator import generate_legal_document

router = APIRouter(
    prefix="/api",
    tags=["Legal Documents"]
)


class LegalDocumentRequest(BaseModel):

    document_type: str = Field(
        min_length=2,
        max_length=100
    )

    parties: str = Field(
        min_length=2,
        max_length=5000
    )

    terms: str = Field(
        min_length=2,
        max_length=10000
    )

    effective_date: str = Field(
        min_length=2,
        max_length=100
    )

    jurisdiction: str = Field(
        default="Not specified",
        max_length=300
    )

    additional_details: str = Field(
        default="",
        max_length=5000
    )


class DocumentTextRequest(BaseModel):

    content: str = Field(
        min_length=1,
        max_length=50000
    )


@router.post("/generate")
def generate(request: LegalDocumentRequest):

    try:

        document = generate_legal_document(
            document_type=request.document_type,
            parties=request.parties,
            terms=request.terms,
            effective_date=request.effective_date,
            jurisdiction=request.jurisdiction,
            additional_details=request.additional_details
        )

        return {
            "success": True,
            "document": document
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )