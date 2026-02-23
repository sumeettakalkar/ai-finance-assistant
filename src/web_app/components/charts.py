"""Plotly chart builder functions for agent responses.

Each function takes metadata from an AgentResponse and returns a
``plotly.graph_objects.Figure`` ready for ``st.plotly_chart()``.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import plotly.graph_objects as go


# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------

_COLORS = [
    "#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A",
    "#19D3F3", "#FF6692", "#B6E880", "#FF97FF", "#FECB52",
]

_LAYOUT_DEFAULTS = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=20, r=20, t=40, b=20),
    font=dict(family="system-ui, -apple-system, sans-serif", size=13),
)


# ---------------------------------------------------------------------------
# Portfolio charts
# ---------------------------------------------------------------------------

def portfolio_allocation_donut(metadata: Dict) -> Optional[go.Figure]:
    """Donut pie chart showing allocation by ticker.

    Parameters
    ----------
    metadata : dict
        Must contain ``allocations`` (dict of ticker -> weight 0-1).

    Returns
    -------
    go.Figure or None
        Returns None if no allocation data is available.
    """
    allocations = metadata.get("allocations")
    if not allocations:
        return None

    tickers = list(allocations.keys())
    weights = [w * 100 for w in allocations.values()]

    fig = go.Figure(data=[
        go.Pie(
            labels=tickers,
            values=weights,
            hole=0.45,
            marker=dict(colors=_COLORS[:len(tickers)]),
            textinfo="label+percent",
            textposition="outside",
            hovertemplate="%{label}: %{value:.1f}%<extra></extra>",
        )
    ])
    fig.update_layout(
        title="Portfolio Allocation",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15),
        **_LAYOUT_DEFAULTS,
    )
    return fig


def portfolio_asset_mix_bar(metadata: Dict) -> Optional[go.Figure]:
    """Horizontal bar chart showing asset mix (Stocks/Bonds/Other).

    Parameters
    ----------
    metadata : dict
        Must contain ``stock_pct``, ``bond_pct``, ``other_pct``.
    """
    stock_pct = metadata.get("stock_pct")
    bond_pct = metadata.get("bond_pct")
    other_pct = metadata.get("other_pct")

    if stock_pct is None:
        return None

    categories = ["Stocks", "Bonds", "Other"]
    values = [stock_pct, bond_pct, other_pct]
    colors = ["#636EFA", "#00CC96", "#FFA15A"]

    fig = go.Figure(data=[
        go.Bar(
            y=categories,
            x=values,
            orientation="h",
            marker=dict(color=colors),
            text=[f"{v:.1f}%" for v in values],
            textposition="auto",
            hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
        )
    ])
    fig.update_layout(
        title="Asset Mix",
        xaxis=dict(title="Percentage", range=[0, 105]),
        yaxis=dict(autorange="reversed"),
        **_LAYOUT_DEFAULTS,
    )
    return fig


# ---------------------------------------------------------------------------
# Market charts
# ---------------------------------------------------------------------------

def market_price_history(
    ticker: str,
    closes: List[float],
    dates: Optional[List[str]] = None,
) -> Optional[go.Figure]:
    """Line chart showing price history for a stock.

    Parameters
    ----------
    ticker : str
        Stock ticker symbol.
    closes : list[float]
        List of closing prices.
    dates : list[str], optional
        Corresponding date labels. Defaults to numbered days.
    """
    if not closes:
        return None

    if dates is None:
        dates = [f"Day {i+1}" for i in range(len(closes))]

    fig = go.Figure(data=[
        go.Scatter(
            x=dates,
            y=closes,
            mode="lines+markers",
            line=dict(color="#636EFA", width=2),
            marker=dict(size=6),
            hovertemplate="$%{y:.2f}<extra>%{x}</extra>",
        )
    ])
    fig.update_layout(
        title=f"{ticker} Price History",
        xaxis=dict(title="Date"),
        yaxis=dict(title="Price ($)"),
        **_LAYOUT_DEFAULTS,
    )
    return fig


# ---------------------------------------------------------------------------
# Goals charts
# ---------------------------------------------------------------------------

def goal_savings_projection(metadata: Dict) -> Optional[go.Figure]:
    """Area chart showing projected savings growth over time.

    Computes a month-by-month projection using the metadata from
    the GoalAgent's computation result.

    Parameters
    ----------
    metadata : dict
        Must contain ``monthly_contribution``, ``months``, ``monthly_rate``,
        ``current_savings``, ``target_amount``.
    """
    monthly_contribution = metadata.get("monthly_contribution")
    months = metadata.get("months")
    monthly_rate = metadata.get("monthly_rate")
    current_savings = metadata.get("current_savings", 0)
    target_amount = metadata.get("target_amount")

    if monthly_contribution is None or months is None or monthly_rate is None:
        return None

    months = int(months)

    # Build month-by-month projection
    balance = float(current_savings)
    balances = [balance]
    month_labels = [0]

    for m in range(1, months + 1):
        balance = balance * (1 + monthly_rate) + monthly_contribution
        balances.append(balance)
        month_labels.append(m)

    # Convert months to years for readability
    year_labels = [m / 12 for m in month_labels]

    fig = go.Figure()

    # Projected savings area
    fig.add_trace(go.Scatter(
        x=year_labels,
        y=balances,
        fill="tozeroy",
        fillcolor="rgba(99, 110, 250, 0.2)",
        line=dict(color="#636EFA", width=2),
        name="Projected Balance",
        hovertemplate="Year %{x:.1f}: $%{y:,.0f}<extra></extra>",
    ))

    # Target line
    if target_amount:
        fig.add_trace(go.Scatter(
            x=[year_labels[0], year_labels[-1]],
            y=[target_amount, target_amount],
            mode="lines",
            line=dict(color="#EF553B", width=2, dash="dash"),
            name=f"Target: ${target_amount:,.0f}",
            hovertemplate="Target: $%{y:,.0f}<extra></extra>",
        ))

    fig.update_layout(
        title="Savings Growth Projection",
        xaxis=dict(title="Years"),
        yaxis=dict(title="Balance ($)", tickformat="$,.0f"),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
        **_LAYOUT_DEFAULTS,
    )
    return fig
