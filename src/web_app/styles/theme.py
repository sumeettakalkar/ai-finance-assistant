"""Minimal CSS that works with Streamlit's native theming.

We avoid overriding background/text colors so the CSS works regardless
of whether Streamlit is in light or dark mode.  Only additive styles
(borders, badges, spacing) are applied.
"""

from __future__ import annotations

# Accent color used for branding elements only
_ACCENT = "#636EFA"
_SUCCESS = "#00CC96"
_WARNING = "#FFA15A"
_DANGER = "#EF553B"


def generate_css() -> str:
    """Return CSS that layers on top of Streamlit's native theme."""
    return f"""
    /* Risk badges */
    .risk-badge {{
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }}
    .risk-high {{ background: {_DANGER}22; color: {_DANGER}; }}
    .risk-medium {{ background: {_WARNING}22; color: {_WARNING}; }}
    .risk-low {{ background: {_SUCCESS}22; color: {_SUCCESS}; }}

    /* Confidence indicators */
    .confidence-badge {{
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 500;
    }}
    .confidence-high {{ background: {_SUCCESS}22; color: {_SUCCESS}; }}
    .confidence-medium {{ background: {_WARNING}22; color: {_WARNING}; }}
    .confidence-low {{ background: {_DANGER}22; color: {_DANGER}; }}

    /* Sidebar branding */
    .sidebar-brand {{
        font-size: 1.4rem;
        font-weight: 700;
        color: {_ACCENT};
        padding: 0.5rem 0 1rem 0;
        margin-bottom: 1rem;
    }}

    /* Tab instructions — uses semi-transparent tint so it works on any bg */
    .tab-instructions {{
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        border-left: 3px solid {_ACCENT};
        background: rgba(99, 110, 250, 0.06);
    }}
    """
