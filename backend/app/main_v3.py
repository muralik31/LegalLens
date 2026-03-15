
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

import structlog
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.config import settings
from app.database import engine, get_db
from app.models import Base, Document, User
from app.security import (
    SecurityValidationError,
    sanitize_filename,
    sanitize_for_llm,
    validate_file_content,
)
from app.schemas import (
    AnalysisResponse,
    AnalyzeRequest,
    AskQuestionRequest,
    AskQuestionResponse,
    ChatRequest,
    ChatResponse,
    Token,
    TokenRefresh,
    UploadResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.analysis import analyze_document
from app.services.document_processing import UnsupportedFileTypeError, extract_text
from app.services.qa import answer_question, build_chat_reply
from app.services.storage import storage

# Structured logging
logger = structlog.get_logger(__name__)

DISCLAIMER = "This AI analysis is for informational purposes only and not legal advice."

# Rate limiting
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("application_startup", version=settings.APP_VERSION)

    # Validate configuration
    if not settings.DEBUG and len(settings.SECRET_KEY) < 32:
        logger.error("SECURITY: SECRET_KEY not properly configured!")
        raise RuntimeError("SECRET_KEY must be at least 32 characters in production")

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Shutdown
    logger.info("application_shutdown")
    await engine.dispose()


app = FastAPI(
    title=f"{settings.APP_NAME} API",
    version=settings.APP_VERSION,
    description="AI-powered legal document analyzer with multi-language support",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware - tightened for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Explicit methods only
    allow_headers=["Authorization", "Content-Type"],  # Explicit headers only
    max_age=3600,  # Cache preflight requests for 1 hour
)


# ============= Health & Info Endpoints =============


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "llm_provider": settings.LLM_PROVIDER,
        "storage_provider": settings.STORAGE_PROVIDER,
    }


@app.get("/disclaimer")
async def get_disclaimer() -> dict[str, str]:
    """Get legal disclaimer."""
    return {"disclaimer": DISCLAIMER}


# ============= Authentication Endpoints =============


@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")  # Limit registration attempts
async def register_user(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Register a new user."""
    # Check if user exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        subscription_tier="free",
        documents_analyzed=0,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info("user_registered", user_id=user.id, email=user.email)

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        subscription_tier=user.subscription_tier,
        documents_analyzed=user.documents_analyzed,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@app.post("/auth/login", response_model=Token)
@limiter.limit("5/minute")  # Prevent brute force attacks
async def login(
    request: Request,
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Login and get access token."""
    # Find user
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Create tokens
    access_token = create_access_token({"sub": user.id})
    refresh_token = create_refresh_token({"sub": user.id})

    logger.info("user_logged_in", user_id=user.id, email=user.email)

    return Token(access_token=access_token, refresh_token=refresh_token)


@app.post("/auth/refresh", response_model=Token)
async def refresh_token(token_data: TokenRefresh, db: AsyncSession = Depends(get_db)) -> Token:
    """Refresh access token using refresh token."""
    payload = decode_token(token_data.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user",
        )

    # Create new tokens
    access_token = create_access_token({"sub": user.id})
    new_refresh_token = create_refresh_token({"sub": user.id})

    return Token(access_token=access_token, refresh_token=new_refresh_token)


@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Get current user information."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        subscription_tier=current_user.subscription_tier,
        documents_analyzed=current_user.documents_analyzed,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


# ============= Document Endpoints =============


@app.post("/upload", response_model=UploadResponse)
@limiter.limit("10/minute")  # Limit upload rate
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UploadResponse:
    """Upload and process a legal document."""
    content_type = file.content_type or "application/octet-stream"

    # Sanitize filename
    safe_filename = sanitize_filename(file.filename or "document")

    # Read file
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(payload) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_UPLOAD_BYTES // (1024*1024)}MB limit")

    # Extract text and validate file content
    temp_path: Path | None = None
    try:
        with NamedTemporaryFile(delete=False, suffix=Path(safe_filename).suffix) as temp:
            temp.write(payload)
            temp_path = Path(temp.name)

        # Validate file content matches declared type (magic number check)
        try:
            is_valid, actual_mime = validate_file_content(temp_path, content_type)
            logger.info("file_validated", filename=safe_filename, actual_mime=actual_mime)
        except SecurityValidationError as e:
            logger.warning("file_validation_failed", filename=safe_filename, error=str(e))
            raise HTTPException(status_code=400, detail=str(e)) from e

        extracted_text = extract_text(temp_path, content_type)

        # Sanitize extracted text for LLM use
        extracted_text = sanitize_for_llm(extracted_text)

    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=422, detail="Could not decode uploaded text file") from exc
    except SecurityValidationError:
        raise  # Re-raise security validation errors
    except Exception as exc:
        logger.error("text_extraction_failed", filename=safe_filename, error=str(exc))
        detail = str(exc) if settings.DEBUG else "Text extraction failed"
        raise HTTPException(status_code=422, detail=detail) from exc
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()

    # Upload to storage
    try:
        storage_path = await storage.upload_file(payload, safe_filename, content_type)
    except Exception as exc:
        logger.error("storage_upload_failed", error=str(exc))
        detail = str(exc) if settings.DEBUG else "Failed to store file"
        raise HTTPException(status_code=500, detail=detail) from exc

    # Calculate expiry date
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.FILE_RETENTION_DAYS)

    # Save to database
    document_id = str(uuid4())
    document = Document(
        document_id=document_id,
        user_id=current_user.id,
        filename=safe_filename,
        content_type=content_type,
        file_size=len(payload),
        storage_path=storage_path,
        extracted_text=extracted_text,
        expires_at=expires_at,
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    logger.info(
        "document_uploaded",
        user_id=current_user.id,
        document_id=document_id,
        filename=safe_filename,
        size=len(payload),
    )

    return UploadResponse(
        document_id=document_id,
        filename=document.filename,
        content_type=document.content_type,
        uploaded_at=document.uploaded_at,
        extracted_characters=len(extracted_text),
    )


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    request: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnalysisResponse:
    """Analyze an uploaded document."""
    # Get document
    result = await db.execute(
        select(Document).where(
            Document.document_id == request.document_id,
            Document.user_id == current_user.id,
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document.extracted_text.strip():
        raise HTTPException(status_code=422, detail="No extractable text found in document")

    # Perform analysis
    try:
        analysis_result = await analyze_document(
            document.document_id,
            document.extracted_text,
            request.language,
        )
    except Exception as exc:
        logger.error("analysis_failed", document_id=document.document_id, error=str(exc))
        raise HTTPException(status_code=500, detail="Analysis failed") from exc

    # Save analysis results
    document.analysis = analysis_result.model_dump()
    document.analyzed_at = datetime.now(timezone.utc)

    # Update user stats
    current_user.documents_analyzed += 1

    await db.commit()

    logger.info(
        "document_analyzed",
        user_id=current_user.id,
        document_id=document.document_id,
        language=request.language,
    )

    return analysis_result


@app.get("/documents")
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List user's documents."""
    result = await db.execute(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.uploaded_at.desc())
    )
    documents = result.scalars().all()

    return {
        "documents": [
            {
                "document_id": doc.document_id,
                "filename": doc.filename,
                "uploaded_at": doc.uploaded_at,
                "analyzed_at": doc.analyzed_at,
                "expires_at": doc.expires_at,
            }
            for doc in documents
        ]
    }


@app.get("/document/{document_id}")
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get document details and analysis."""
    result = await db.execute(
        select(Document).where(
            Document.document_id == document_id,
            Document.user_id == current_user.id,
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "document_id": document.document_id,
        "filename": document.filename,
        "content_type": document.content_type,
        "uploaded_at": document.uploaded_at,
        "analyzed_at": document.analyzed_at,
        "expires_at": document.expires_at,
        "analysis": document.analysis,
    }


@app.post("/ask-question", response_model=AskQuestionResponse)
async def ask_question_endpoint(
    request: AskQuestionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AskQuestionResponse:
    """Ask a question about a document."""
    result = await db.execute(
        select(Document).where(
            Document.document_id == request.document_id,
            Document.user_id == current_user.id,
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    answer = await answer_question(document.extracted_text, request.question, request.language)

    logger.info(
        "question_answered",
        user_id=current_user.id,
        document_id=document.document_id,
        language=request.language,
    )

    return AskQuestionResponse(
        document_id=request.document_id,
        answer=answer,
        language=request.language,
    )


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """Chat with a document."""
    result = await db.execute(
        select(Document).where(
            Document.document_id == request.document_id,
            Document.user_id == current_user.id,
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    reply = await build_chat_reply(document.extracted_text, request.messages, request.language)

    logger.info(
        "chat_interaction",
        user_id=current_user.id,
        document_id=document.document_id,
        language=request.language,
    )

    return ChatResponse(
        document_id=request.document_id,
        reply=reply,
        language=request.language,
    )
