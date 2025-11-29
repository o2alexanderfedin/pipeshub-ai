"""
Pydantic models for Hupyy verification.

Defines request/response schemas with strict typing and validation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class VerificationVerdict(str, Enum):
    """Verification verdict types."""

    SAT = "SAT"  # Satisfiable - formula is valid
    UNSAT = "UNSAT"  # Unsatisfiable - formula is invalid
    UNKNOWN = "UNKNOWN"  # Cannot determine (timeout, resource limits, etc.)
    ERROR = "ERROR"  # Error occurred during verification


class FailureMode(str, Enum):
    """Failure modes for UNKNOWN verdicts."""

    TIMEOUT = "timeout"  # Solver timeout
    RESOURCE_LIMIT = "resource_limit"  # Memory/CPU limits exceeded
    PARSE_ERROR = "parse_error"  # Input parsing failed
    SOLVER_ERROR = "solver_error"  # Internal solver error
    NETWORK_ERROR = "network_error"  # Network/API error
    UNKNOWN = "unknown"  # Unclassified failure


class HupyyRequest(BaseModel):
    """Request to Hupyy verification API."""

    informal_text: str = Field(..., description="Natural language text to formalize")
    skip_formalization: bool = Field(
        default=False, description="Skip formalization step"
    )
    enrich: bool = Field(default=False, description="Enable web search enrichment")

    @validator("enrich", always=True)
    def force_enrich_false(cls, v: bool) -> bool:
        """Force enrich=false as per requirements."""
        return False

    @validator("informal_text")
    def validate_non_empty(cls, v: str) -> str:
        """Ensure text is non-empty."""
        if not v or not v.strip():
            raise ValueError("Informal text cannot be empty")
        return v.strip()

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "informal_text": "Find all users with admin privileges",
                "skip_formalization": False,
                "enrich": False,
            }
        }


class HupyyResponse(BaseModel):
    """Response from Hupyy verification API."""

    verdict: VerificationVerdict = Field(..., description="Verification verdict")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score (0.0-1.0)"
    )
    formalization_similarity: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Similarity between NL and SMT"
    )
    explanation: Optional[str] = Field(
        default=None, description="Human-readable explanation"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    duration_ms: Optional[int] = Field(
        default=None, ge=0, description="Verification duration"
    )

    @classmethod
    def from_hupyy_process_response(cls, response_data: Dict[str, Any]) -> "HupyyResponse":
        """
        Parse Hupyy /pipeline/process response into HupyyResponse.

        Maps:
        - check_sat_result → verdict (SAT/UNSAT/UNKNOWN)
        - formalization_similarity → confidence
        - model, proof, smt_lib_code, formal_text → metadata

        Args:
            response_data: Raw response from Hupyy /pipeline/process endpoint

        Returns:
            Parsed HupyyResponse instance
        """
        # Map check_sat_result to verdict
        check_sat = response_data.get("check_sat_result", "").upper()
        if check_sat == "SAT":
            verdict = VerificationVerdict.SAT
        elif check_sat == "UNSAT":
            verdict = VerificationVerdict.UNSAT
        else:
            verdict = VerificationVerdict.UNKNOWN

        # Use formalization_similarity as confidence (default to 0.5 if missing)
        confidence = response_data.get("formalization_similarity", 0.5)

        # Store additional fields in metadata
        metadata = {
            "model": response_data.get("model"),
            "proof": response_data.get("proof"),
            "smt_lib_code": response_data.get("smt_lib_code"),
            "formal_text": response_data.get("formal_text"),
            "informal_text": response_data.get("informal_text"),
            "extraction_degradation": response_data.get("extraction_degradation"),
            "solver_success": response_data.get("solver_success"),
            "passed_all_checks": response_data.get("passed_all_checks"),
        }

        # Remove None values
        metadata = {k: v for k, v in metadata.items() if v is not None}

        # Extract explanation from proof summary if available
        explanation = None
        if response_data.get("proof") and isinstance(response_data["proof"], dict):
            explanation = response_data["proof"].get("summary")

        # Get duration from metrics if available
        duration_ms = None
        if response_data.get("metrics") and isinstance(response_data["metrics"], dict):
            duration_ms = response_data["metrics"].get("total_time_ms")

        return cls(
            verdict=verdict,
            confidence=confidence,
            formalization_similarity=response_data.get("formalization_similarity"),
            explanation=explanation,
            metadata=metadata,
            duration_ms=duration_ms,
        )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "verdict": "SAT",
                "confidence": 0.95,
                "formalization_similarity": 0.88,
                "explanation": "The formula is satisfiable with high confidence",
                "metadata": {"solver": "z3", "model_size": 42},
                "duration_ms": 1250,
            }
        }


class VerificationRequest(BaseModel):
    """Internal verification request (with chunking support)."""

    request_id: str = Field(..., description="Unique request ID")
    content: str = Field(..., description="Content to verify")
    chunk_index: int = Field(default=0, ge=0, description="Chunk index (0-based)")
    total_chunks: int = Field(default=1, ge=1, description="Total number of chunks")
    nl_query: str = Field(..., description="Natural language query")
    source_document_id: Optional[str] = Field(
        default=None, description="Source document ID"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Request timestamp"
    )

    @validator("content")
    def validate_content_size(cls, v: str) -> str:
        """Validate content is not too large (max 10KB per chunk)."""
        max_size = 10 * 1024  # 10KB
        if len(v.encode("utf-8")) > max_size:
            raise ValueError(f"Content exceeds maximum size of {max_size} bytes")
        return v

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "request_id": "req_123abc",
                "content": "Sample SMT formula content",
                "chunk_index": 0,
                "total_chunks": 1,
                "nl_query": "Find admin users",
                "source_document_id": "doc_456def",
                "timestamp": "2025-11-27T10:00:00Z",
            }
        }


class VerificationResult(BaseModel):
    """Verification result with full context."""

    request_id: str = Field(..., description="Original request ID")
    chunk_index: int = Field(..., ge=0, description="Chunk index")
    verdict: VerificationVerdict = Field(..., description="Verification verdict")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    formalization_similarity: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    explanation: Optional[str] = Field(default=None)
    failure_mode: Optional[FailureMode] = Field(
        default=None, description="Failure mode if UNKNOWN/ERROR"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
    duration_seconds: float = Field(..., ge=0.0, description="Verification duration")
    cached: bool = Field(default=False, description="Whether result was from cache")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "request_id": "req_123abc",
                "chunk_index": 0,
                "verdict": "SAT",
                "confidence": 0.95,
                "formalization_similarity": 0.88,
                "explanation": "Formula is satisfiable",
                "failure_mode": None,
                "metadata": {"solver": "z3"},
                "duration_seconds": 62.5,
                "cached": False,
                "timestamp": "2025-11-27T10:01:02Z",
            }
        }


class ChunkingConfig(BaseModel):
    """Configuration for input chunking."""

    max_chunk_size_bytes: int = Field(
        default=10240, ge=1024, description="Max chunk size (10KB)"
    )
    overlap_chars: int = Field(default=100, ge=0, description="Overlap between chunks")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {"max_chunk_size_bytes": 10240, "overlap_chars": 100}
        }


class VerificationStats(BaseModel):
    """Statistics for verification operations."""

    total_requests: int = Field(default=0, ge=0)
    successful_verifications: int = Field(default=0, ge=0)
    failed_verifications: int = Field(default=0, ge=0)
    cache_hits: int = Field(default=0, ge=0)
    cache_misses: int = Field(default=0, ge=0)
    average_duration_seconds: float = Field(default=0.0, ge=0.0)
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    cache_hit_rate: float = Field(default=0.0, ge=0.0, le=1.0)

    def update_success_rate(self) -> None:
        """Recalculate success rate."""
        if self.total_requests > 0:
            self.success_rate = self.successful_verifications / self.total_requests

    def update_cache_hit_rate(self) -> None:
        """Recalculate cache hit rate."""
        total_cache_ops = self.cache_hits + self.cache_misses
        if total_cache_ops > 0:
            self.cache_hit_rate = self.cache_hits / total_cache_ops

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "total_requests": 100,
                "successful_verifications": 85,
                "failed_verifications": 15,
                "cache_hits": 60,
                "cache_misses": 40,
                "average_duration_seconds": 58.3,
                "success_rate": 0.85,
                "cache_hit_rate": 0.60,
            }
        }
