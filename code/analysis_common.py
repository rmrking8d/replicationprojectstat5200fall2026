"""Shared, small helpers for the individual table and figure scripts."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd
import scipy.stats as stats
import statsmodels.api as sm


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DATA_PATH = PROJECT_ROOT / "data" / "clean" / "analysis_sample.csv"
TABLES_DIR = PROJECT_ROOT / "results" / "tables"
FIGURES_DIR = PROJECT_ROOT / "results" / "figures"
CONDITION_NAMES = {
    0: "No Ads",
    1: "Genre Ad",
    2: "Plain Ad",
    3: "Price Ad",
    4: "Genre Ad",
    5: "Plain Ad",
    6: "Price Ad",
}


def load_analysis_sample() -> pd.DataFrame:
    """Load the clean participant-level dataset and validate its core fields."""
    if not ANALYSIS_DATA_PATH.is_file():
        raise FileNotFoundError(
            "Analysis data are missing. Run "
            "`python3 code/00_build_analysis_data.py` first."
        )

    data = pd.read_csv(ANALYSIS_DATA_PATH)
    required = {
        "ad_condition",
        "clicked_203",
        "clicked_303",
        "purchased_203",
        "purchased_303",
        "romance_rank",
        "mystery_rank",
    }
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Analysis dataset is missing columns: {sorted(missing)}")

    if data["ad_condition"].isna().any():
        raise ValueError("Analysis sample contains participants without an ad condition")

    return data


def fit_robust_ols(
    data: pd.DataFrame,
    outcome: str,
    regressors: pd.DataFrame,
    add_intercept: bool = True,
) -> sm.regression.linear_model.RegressionResultsWrapper:
    """Fit OLS with the HC1 robust standard errors used by Stata's ``robust``."""
    model_data = pd.concat(
        [data[[outcome]], regressors],
        axis=1,
    ).dropna()
    if model_data.empty:
        raise ValueError(f"No complete observations for outcome {outcome!r}")

    x = model_data.drop(columns=outcome).astype(float)
    if add_intercept:
        x = sm.add_constant(x, has_constant="add")
    y = model_data[outcome].astype(float)

    if len(model_data) <= x.shape[1]:
        raise ValueError(f"Insufficient observations to estimate {outcome!r}")

    # Stata reports t-based p-values with residual degrees of freedom. Setting
    # use_t=True applies that convention to the HC1 covariance estimates.
    return sm.OLS(y, x).fit(cov_type="HC1", use_t=True)


def robust_linear_contrast(
    result: sm.regression.linear_model.RegressionResultsWrapper,
    weights: dict[str, float],
) -> dict[str, float]:
    """Compute an estimated linear combination and its robust t test."""
    names = list(result.params.index)
    contrast = np.array([weights.get(name, 0.0) for name in names])
    estimate = float(contrast @ result.params.to_numpy())
    covariance = result.cov_params().to_numpy()
    variance = float(contrast @ covariance @ contrast)
    standard_error = float(np.sqrt(max(variance, 0.0)))
    t_value = estimate / standard_error if standard_error else np.nan
    p_value = (
        float(2 * stats.t.sf(abs(t_value), result.df_resid))
        if np.isfinite(t_value)
        else np.nan
    )
    return {
        "estimate": estimate,
        "standard_error": standard_error,
        "p_value": p_value,
    }


def condition_sample(data: pd.DataFrame, conditions: Sequence[int]) -> pd.DataFrame:
    """Return participants assigned to the listed experimental conditions."""
    return data.loc[data["ad_condition"].isin(conditions)].copy()


def save_table(data: pd.DataFrame, name: str) -> None:
    """Save a result table as CSV for inspection and reuse."""
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    data.to_csv(TABLES_DIR / f"{name}.csv", index=False, float_format="%.6f")
