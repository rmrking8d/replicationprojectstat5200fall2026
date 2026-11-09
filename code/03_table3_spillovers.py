"""Reproduce Table 3: spillovers from price and genre advertising."""

from __future__ import annotations

import pandas as pd

from analysis_common import (
    condition_sample,
    fit_robust_ols,
    load_analysis_sample,
    save_table,
)


PRICE_OUTCOMES = [
    ("Price sorted low-to-high", "sorted_by_price_asc"),
    ("Price sorted high-to-low", "sorted_by_price_desc"),
    ("Searched another cheap book", "clicked_cheap_other"),
    ("Bought another cheap book", "purchased_cheap_other"),
    ("Self-reported price importance", "importance_price_num"),
]
GENRE_OUTCOMES = [
    ("Filtered to advertised genre", "filtered_to_focal_genre"),
    ("Filtered to any genre", "filtered_to_genre"),
    ("Searched another book of advertised genre", "clicked_focal_genre_other"),
    ("Bought another book of advertised genre", "purchased_focal_genre_other"),
    ("Self-reported genre importance", "importance_genre_num"),
]


def _estimate_panel(
    data: pd.DataFrame,
    panel: str,
    treatment_conditions: list[int],
    outcome_definitions: list[tuple[str, str]],
) -> list[dict[str, object]]:
    """Estimate the pooled treatment effect for one Table 3 panel."""
    sample = condition_sample(
        data,
        sorted(set([2, 5, *treatment_conditions])),
    )
    sample["treatment"] = sample["ad_condition"].isin(treatment_conditions).astype(int)
    rows = []

    for label, outcome in outcome_definitions:
        result = fit_robust_ols(
            sample,
            outcome,
            sample[["treatment"]],
        )
        rows.append(
            {
                "panel": panel,
                "outcome": label,
                "plain_ad_mean": sample.loc[
                    sample["treatment"].eq(0),
                    outcome,
                ].mean(),
                "attribute_ad_mean": sample.loc[
                    sample["treatment"].eq(1),
                    outcome,
                ].mean(),
                "estimate": result.params["treatment"],
                "standard_error": result.bse["treatment"],
                "p_value": result.pvalues["treatment"],
                "n": int(result.nobs),
            }
        )

    return rows


def estimate_table3(data: pd.DataFrame) -> pd.DataFrame:
    """Estimate the price-ad and genre-ad spillover results."""
    rows = _estimate_panel(
        data,
        "Price advertising",
        [3, 6],
        PRICE_OUTCOMES,
    )

    # The paper measures whether people filtered to the genre advertised in
    # their assigned ad; Lost Girls is a romance book and Stateline is a mystery.
    data = data.copy()
    data["filtered_to_focal_genre"] = data["filtered_to_romance"].where(
        data["ad_condition"].isin([1, 2]),
        data["filtered_to_thriller"],
    )
    data["clicked_focal_genre_other"] = data["clicked_romance_other"].where(
        data["ad_condition"].isin([1, 2]),
        data["clicked_mystery_other"],
    )
    data["purchased_focal_genre_other"] = data[
        "purchased_romance_other"
    ].where(
        data["ad_condition"].isin([1, 2]),
        data["purchased_mystery_other"],
    )
    rows.extend(
        _estimate_panel(
            data,
            "Genre advertising",
            [1, 4],
            GENRE_OUTCOMES,
        )
    )

    return pd.DataFrame(rows)


def main() -> None:
    data = load_analysis_sample()
    table = estimate_table3(data)
    save_table(table, "table3_advertising_spillovers")
    print(f"Saved Table 3 output for {len(data):,} participants.")


if __name__ == "__main__":
    main()
