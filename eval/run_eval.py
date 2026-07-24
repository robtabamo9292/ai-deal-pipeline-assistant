from pathlib import Path

import pandas as pd

from src.schema import DealRecord
from src.scoring import apply_vc_scorecard

ROOT = Path(__file__).resolve().parents[1]


def _split(value) -> list[str]:
    if (
        pd.isna(value)
        or not str(value).strip()
        or str(value).strip().lower() == "unknown"
    ):
        return []
    return [
        item.strip()
        for item in str(value).split("|")
        if item.strip()
    ]


def _text(value) -> str:
    if pd.isna(value) or not str(value).strip():
        return "Unknown"
    return str(value).strip()


def main() -> None:
    cases = pd.read_csv(ROOT / "eval" / "eval_set.csv")
    rows = []
    for case in cases.itertuples(index=False):
        deal = DealRecord(
            company_name=_text(case.company_name),
            sector=_text(case.sector),
            subsector=_text(case.subsector),
            business_model=_text(case.business_model),
            stage=_text(case.stage),
            description=_text(case.description),
            traction_signals=_split(case.traction_signals),
            customer_signals=_split(case.customer_signals),
            risks=_split(case.risks),
        )
        deal = apply_vc_scorecard(deal, case.notes)
        passed = (
            case.expected_min_score
            <= deal.opportunity_score
            <= case.expected_max_score
            and deal.priority == case.expected_status
        )
        rows.append(
            {
                "case_id": case.case_id,
                "evidence_score": deal.opportunity_score,
                "diligence_status": deal.priority,
                "expected_min_score": case.expected_min_score,
                "expected_max_score": case.expected_max_score,
                "expected_status": case.expected_status,
                "passed": passed,
            }
        )
    results = pd.DataFrame(rows)
    results.to_csv(
        ROOT / "eval" / "eval_results.csv",
        index=False,
    )
    print(results.to_string(index=False))
    if not results["passed"].all():
        raise SystemExit("One or more evaluation cases failed.")


if __name__ == "__main__":
    main()
