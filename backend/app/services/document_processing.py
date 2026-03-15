from __future__ import annotations

from pathlib import Path

SUPPORTED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/jpeg",
    "image/png",
    "text/plain",
}


class UnsupportedFileTypeError(ValueError):
    pass


def extract_text(file_path: Path, content_type: str) -> str:
    if content_type not in SUPPORTED_CONTENT_TYPES:
        raise UnsupportedFileTypeError(f"Unsupported content type: {content_type}")

    if content_type == "application/pdf":
        return _extract_pdf(file_path)
    if (
        content_type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ):
        return _extract_docx(file_path)
    if content_type in {"image/jpeg", "image/png"}:
        return _extract_image(file_path)
    return file_path.read_text(encoding="utf-8")


def _extract_pdf(file_path: Path) -> str:
    import pdfplumber

    pages: list[str] = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    return "\n".join(pages).strip()


def _extract_docx(file_path: Path) -> str:
    import docx

    document = docx.Document(file_path)
    paragraphs = [paragraph.text for paragraph in document.paragraphs]
    return "\n".join(paragraphs).strip()


def _extract_image(file_path: Path) -> str:
    import pytesseract
    from PIL import Image

    image = Image.open(file_path)
    return pytesseract.image_to_string(image).strip()
