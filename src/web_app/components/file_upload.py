"""File upload widget for portfolio screenshots and PDF statements."""

from __future__ import annotations

import base64
from typing import Optional

import streamlit as st


def upload_portfolio_image() -> Optional[str]:
    """Render an image upload widget and return base64-encoded image data.

    Returns
    -------
    str or None
        Base64-encoded image string, or None if no file uploaded.
    """
    uploaded = st.file_uploader(
        "Upload portfolio screenshot or statement",
        type=["png", "jpg", "jpeg", "pdf"],
        key="portfolio_file_upload",
    )

    if uploaded is None:
        return None

    if uploaded.type == "application/pdf":
        return _extract_from_pdf(uploaded)

    image_bytes = uploaded.read()
    st.image(image_bytes, caption="Uploaded file", use_container_width=True)
    return base64.b64encode(image_bytes).decode("utf-8")


def _extract_from_pdf(uploaded_file) -> Optional[str]:
    """Extract text from PDF and return as string for NL parsing.

    Note: Returns text content for NL parsing, not base64 image.
    For PDFs, we extract text rather than treating as an image.
    """
    try:
        import pdfplumber
        with pdfplumber.open(uploaded_file) as pdf:
            text_pages = []
            for page in pdf.pages[:10]:  # Limit to first 10 pages
                text = page.extract_text()
                if text:
                    text_pages.append(text)

        if text_pages:
            full_text = "\n\n".join(text_pages)
            st.text_area("Extracted text", full_text, height=200, disabled=True)
            return full_text
        else:
            st.warning("Could not extract text from the PDF.")
            return None
    except ImportError:
        st.error("pdfplumber is required for PDF processing. Install with: pip install pdfplumber")
        return None
    except Exception as e:
        st.error(f"PDF processing error: {e}")
        return None
