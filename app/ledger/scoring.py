from __future__ import annotations

from .article import analyze_article_content
from .editorial import analyze_editorial
from .models import IntegrityLedgerResult
from .ownership import analyze_ownership
from .pattern import analyze_pattern
from .regulatory import analyze_regulatory
from .revenue import analyze_revenue


def _categorize(total: float) -> str:
    if total < 0.25:
        return "LOW"
    if total < 0.50:
        return "MODERATE"
    if total < 0.75:
        return "ELEVATED"
    return "STRUCTURAL"


def run_integrity_ledger(
    article_input: object, include_damage_estimate: bool = False
) -> IntegrityLedgerResult:
    ownership = analyze_ownership(getattr(article_input, "outlet", ""))
    revenue = analyze_revenue(getattr(article_input, "outlet", ""))
    editorial = analyze_editorial(article_input)
    article = analyze_article_content(article_input)
    regulatory = analyze_regulatory(article_input)
    pattern = analyze_pattern(article_input)

    total = (
        ownership.score * 0.15
        + revenue.score * 0.20
        + editorial.score * 0.15
        + article.score * 0.25
        + regulatory.score * 0.10
        + pattern.score * 0.15
    )

    risk = _categorize(total)

    result = IntegrityLedgerResult(
        outlet=getattr(article_input, "outlet", ""),
        article_id=getattr(article_input, "id", ""),
        ownership=ownership,
        revenue=revenue,
        editorial=editorial,
        article=article,
        regulatory=regulatory,
        pattern=pattern,
        total_score=total,
        risk_level=risk,
        damage_estimate=None,
        methodology_version="0.1-alpha",
    )

    if include_damage_estimate:
        from .but_if import generate_damage_estimate

        result.damage_estimate = generate_damage_estimate(result)

    return result
