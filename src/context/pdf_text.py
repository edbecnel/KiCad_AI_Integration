"""Optional PDF text extraction for SUBCKT Tier A prompts."""

from __future__ import annotations

from pathlib import Path


def extract_pdf_text(pdf_path: Path, *, max_chars: int = 120_000) -> tuple[str, str | None]:
    """
    Extract text from a PDF file.

    Returns ``(text, error)``. Uses pypdf or PyPDF2 when installed; otherwise
    returns empty text with an error message.
    """
    path = pdf_path.expanduser().resolve()
    if not path.is_file():
        return "", f"PDF not found: {path}"

    reader = None
    error: str | None = None
    for module_name in ("pypdf", "PyPDF2"):
        try:
            module = __import__(module_name)
            reader_cls = getattr(module, "PdfReader", None)
            if reader_cls is not None:
                reader = reader_cls(str(path))
                break
        except ImportError:
            continue
        except Exception as exc:  # pragma: no cover - corrupt PDF
            return "", f"Failed to read PDF: {exc}"

    if reader is None:
        return (
            "",
            "PDF text extractor not available (install pypdf for Tier A fact extraction)",
        )

    chunks: list[str] = []
    try:
        for page in reader.pages:
            text = page.extract_text() or ""
            chunks.append(text)
            if sum(len(c) for c in chunks) >= max_chars:
                break
    except Exception as exc:  # pragma: no cover
        return "", f"Failed to extract PDF text: {exc}"

    combined = "\n".join(chunks).strip()
    if len(combined) > max_chars:
        combined = combined[:max_chars] + "\n…[truncated]"
    if not combined:
        error = "No extractable text in PDF (scanned image PDFs need OCR)"
    return combined, error
