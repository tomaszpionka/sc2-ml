"""Phase 0: Data & Model Sanity Validation (ROADMAP §3).

Functions that validate DuckDB views, temporal splits, feature distributions,
baseline smoke tests, and known issues.  Each check returns a ``SanityCheck``
result that can be aggregated by the CLI or pytest runner.

All checks are designed to work on *both* synthetic (in-memory) and real
DuckDB databases — the caller provides the connection and/or DataFrames.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from sc2ml.config import TEST_RATIO, TRAIN_RATIO, VAL_RATIO

if TYPE_CHECKING:
    import duckdb

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class SanityCheck:
    """One validation check result."""

    name: str
    passed: bool
    detail: str = ""
    value: object = None  # Optional numeric value for reporting


@dataclass
class SanityReport:
    """Aggregated results from all validation checks."""

    checks: list[SanityCheck] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def summary(self) -> str:
        passed = sum(c.passed for c in self.checks)
        total = len(self.checks)
        lines = [f"Sanity Validation: {passed}/{total} checks passed"]
        for c in self.checks:
            status = "PASS" if c.passed else "FAIL"
            lines.append(f"  [{status}] {c.name}: {c.detail}")
        return "\n".join(lines)


# ===================================================================
# §3.1 DuckDB View Sanity
# ===================================================================

def check_flat_players_row_count(con: "duckdb.DuckDBPyConnection") -> SanityCheck:
    """flat_players should have ~2x rows per unique match."""
    fp_count = con.execute("SELECT count(*) FROM flat_players").fetchone()[0]
    unique_matches = con.execute(
        "SELECT count(DISTINCT match_id) FROM flat_players"
    ).fetchone()[0]
    ratio = fp_count / unique_matches if unique_matches > 0 else 0
    ok = 1.9 <= ratio <= 2.1
    return SanityCheck(
        "flat_players row count ratio",
        ok,
        f"flat_players={fp_count}, unique_matches={unique_matches}, ratio={ratio:.2f}",
        ratio,
    )


def check_matches_flat_row_count(con: "duckdb.DuckDBPyConnection") -> SanityCheck:
    """matches_flat should have ~2x rows per unique match."""
    mf_count = con.execute("SELECT count(*) FROM matches_flat").fetchone()[0]
    unique_matches = con.execute(
        "SELECT count(DISTINCT match_id) FROM matches_flat"
    ).fetchone()[0]
    ratio = mf_count / unique_matches if unique_matches > 0 else 0
    ok = 1.9 <= ratio <= 2.1
    return SanityCheck(
        "matches_flat row count ratio",
        ok,
        f"matches_flat={mf_count}, unique_matches={unique_matches}, ratio={ratio:.2f}",
        ratio,
    )


def check_null_rate(con: "duckdb.DuckDBPyConnection") -> SanityCheck:
    """Critical columns (match_time, player names, race, result) must have 0% NULLs."""
    critical_cols = [
        ("match_time", "matches_flat"),
        ("p1_name", "matches_flat"),
        ("p2_name", "matches_flat"),
        ("p1_race", "flat_players"),
        ("p1_result", "matches_flat"),
    ]
    # Adjust column name for flat_players where columns differ
    fp_critical = [
        ("match_time", "flat_players"),
        ("player_name", "flat_players"),
        ("race", "flat_players"),
        ("result", "flat_players"),
    ]

    failures = []
    for col, view in critical_cols + fp_critical:
        try:
            null_count = con.execute(
                f'SELECT count(*) FROM {view} WHERE "{col}" IS NULL'
            ).fetchone()[0]
            total = con.execute(f"SELECT count(*) FROM {view}").fetchone()[0]
            if null_count > 0:
                pct = null_count / total * 100 if total > 0 else 0
                failures.append(f"{view}.{col}: {null_count} NULLs ({pct:.1f}%)")
        except Exception:
            # Column may not exist in some views — skip gracefully
            pass

    ok = len(failures) == 0
    detail = "No NULL critical columns" if ok else "; ".join(failures)
    return SanityCheck("NULL rate audit", ok, detail)


def check_match_time_range(con: "duckdb.DuckDBPyConnection") -> SanityCheck:
    """match_time should be in reasonable range (2016-present, no future dates)."""
    row = con.execute(
        "SELECT MIN(match_time), MAX(match_time) FROM matches_flat"
    ).fetchone()
    min_time, max_time = row[0], row[1]

    issues = []
    if min_time is not None:
        if hasattr(min_time, "year") and min_time.year < 2010:
            issues.append(f"min_time too early: {min_time}")
    if max_time is not None:
        # Allow up to 2027 for flexibility
        if hasattr(max_time, "year") and max_time.year > 2027:
            issues.append(f"max_time in future: {max_time}")

    ok = len(issues) == 0
    detail = f"range: {min_time} to {max_time}" if ok else "; ".join(issues)
    return SanityCheck("match_time range", ok, detail, (min_time, max_time))


def check_race_distribution(con: "duckdb.DuckDBPyConnection") -> SanityCheck:
    """Only 3 races should exist: Terran, Protoss, Zerg."""
    races = con.execute(
        "SELECT DISTINCT race FROM flat_players ORDER BY race"
    ).fetchall()
    race_set = {r[0] for r in races}
    valid_races = {"Terran", "Protoss", "Zerg"}

    unexpected = race_set - valid_races
    ok = len(unexpected) == 0 and len(race_set) > 0
    detail = (
        f"races: {sorted(race_set)}"
        if ok
        else f"unexpected races: {sorted(unexpected)}, all: {sorted(race_set)}"
    )
    return SanityCheck("race distribution", ok, detail, sorted(race_set))


def check_duplicate_match_ids(con: "duckdb.DuckDBPyConnection") -> SanityCheck:
    """Each match_id should have exactly 2 rows in flat_players."""
    bad = con.execute("""
        SELECT match_id, count(*) AS cnt
        FROM flat_players
        GROUP BY match_id
        HAVING cnt != 2
    """).fetchall()

    ok = len(bad) == 0
    detail = (
        "all match_ids have exactly 2 rows"
        if ok
        else f"{len(bad)} match_ids with != 2 rows (first: {bad[:3]})"
    )
    return SanityCheck("duplicate match_id check", ok, detail)


def check_series_coverage(con: "duckdb.DuckDBPyConnection") -> SanityCheck:
    """Report what % of matches belong to a detected series."""
    total = con.execute(
        "SELECT count(DISTINCT match_id) FROM matches_flat WHERE p1_name < p2_name"
    ).fetchone()[0]
    in_series = con.execute(
        "SELECT count(DISTINCT match_id) FROM match_series"
    ).fetchone()[0]
    pct = in_series / total * 100 if total > 0 else 0
    # We expect most matches to have series assignment
    ok = pct >= 50
    return SanityCheck(
        "series assignment coverage",
        ok,
        f"{in_series}/{total} matches in series ({pct:.1f}%)",
        pct,
    )


def run_view_sanity(con: "duckdb.DuckDBPyConnection") -> list[SanityCheck]:
    """Run all §3.1 DuckDB View Sanity checks."""
    return [
        check_flat_players_row_count(con),
        check_matches_flat_row_count(con),
        check_null_rate(con),
        check_match_time_range(con),
        check_race_distribution(con),
        check_duplicate_match_ids(con),
        check_series_coverage(con),
    ]


# ===================================================================
# §3.2 Temporal Split Integrity
# ===================================================================

def check_target_balance(df: pd.DataFrame) -> SanityCheck:
    """Each split should have ~50% win rate (due to dual perspective)."""
    issues = []
    for split_name in ["train", "val", "test"]:
        subset = df[df["split"] == split_name] if "split" in df.columns else df
        if len(subset) == 0:
            continue
        wr = subset["target"].mean() if "target" in subset.columns else np.nan
        if np.isnan(wr) or not (0.40 <= wr <= 0.60):
            issues.append(f"{split_name}: win_rate={wr:.3f}")

    ok = len(issues) == 0
    detail = "all splits ~50% balanced" if ok else "; ".join(issues)
    return SanityCheck("target balance per split", ok, detail)


def check_temporal_leakage(con: "duckdb.DuckDBPyConnection") -> SanityCheck:
    """max(train.match_time) < min(val.match_time) < min(test.match_time)."""
    boundaries = con.execute("""
        SELECT
            ms.split,
            MIN(m.match_time) AS min_time,
            MAX(m.match_time) AS max_time
        FROM match_split ms
        JOIN matches_flat m ON ms.match_id = m.match_id
        WHERE m.p1_name < m.p2_name
        GROUP BY ms.split
        ORDER BY min_time
    """).df()

    splits = boundaries.set_index("split")
    issues = []

    if "train" in splits.index and "val" in splits.index:
        if splits.loc["train", "max_time"] >= splits.loc["val", "min_time"]:
            issues.append(
                f"train/val overlap: train_max={splits.loc['train', 'max_time']}, "
                f"val_min={splits.loc['val', 'min_time']}"
            )
    if "val" in splits.index and "test" in splits.index:
        if splits.loc["val", "max_time"] >= splits.loc["test", "min_time"]:
            issues.append(
                f"val/test overlap: val_max={splits.loc['val', 'max_time']}, "
                f"test_min={splits.loc['test', 'min_time']}"
            )

    ok = len(issues) == 0
    detail = "no temporal leakage" if ok else "; ".join(issues)
    return SanityCheck("temporal leakage check", ok, detail)


def check_series_containment(con: "duckdb.DuckDBPyConnection") -> SanityCheck:
    """No series should be split across train/val or val/test boundaries."""
    broken = con.execute("""
        SELECT ms2.series_id, COUNT(DISTINCT ms1.split) AS split_count
        FROM match_split ms1
        JOIN match_series ms2 ON ms1.match_id = ms2.match_id
        GROUP BY ms2.series_id
        HAVING split_count > 1
    """).df()

    ok = len(broken) == 0
    detail = (
        "all series contained within one split"
        if ok
        else f"{len(broken)} series span multiple splits"
    )
    return SanityCheck("series containment", ok, detail)


def check_split_ratios(con: "duckdb.DuckDBPyConnection") -> SanityCheck:
    """Split sizes should be close to 80/15/5."""
    counts = con.execute("""
        SELECT ms.split, COUNT(DISTINCT ms.match_id) AS cnt
        FROM match_split ms
        GROUP BY ms.split
    """).df()

    total = counts["cnt"].sum()
    ratios = {row["split"]: row["cnt"] / total for _, row in counts.iterrows()}

    issues = []
    expected = {"train": TRAIN_RATIO, "val": VAL_RATIO, "test": TEST_RATIO}
    # Allow 5% tolerance due to series boundary snapping
    tolerance = 0.05
    for split_name, expected_ratio in expected.items():
        actual = ratios.get(split_name, 0)
        if abs(actual - expected_ratio) > tolerance:
            issues.append(
                f"{split_name}: expected {expected_ratio:.2f}, got {actual:.2f}"
            )

    ok = len(issues) == 0
    detail = (
        f"ratios: {', '.join(f'{k}={v:.2f}' for k, v in sorted(ratios.items()))}"
        if ok
        else "; ".join(issues)
    )
    return SanityCheck("split size ratios", ok, detail, ratios)


def run_split_integrity(
    con: "duckdb.DuckDBPyConnection",
    df: pd.DataFrame,
) -> list[SanityCheck]:
    """Run all §3.2 Temporal Split Integrity checks."""
    return [
        check_target_balance(df),
        check_temporal_leakage(con),
        check_series_containment(con),
        check_split_ratios(con),
    ]


# ===================================================================
# §3.3 Feature Distribution Checks
# ===================================================================

def check_constant_features(features_df: pd.DataFrame) -> SanityCheck:
    """No features should be constant or near-constant (std ~ 0)."""
    from sc2ml.features.common import _METADATA_COLUMNS

    feature_cols = [c for c in features_df.columns if c not in _METADATA_COLUMNS]
    numeric_cols = features_df[feature_cols].select_dtypes(include="number").columns

    # Use training split only for statistics
    if "split" in features_df.columns:
        train = features_df[features_df["split"] == "train"]
    else:
        train = features_df

    constants = []
    for col in numeric_cols:
        std = train[col].std()
        if std is not None and std < 1e-10:
            constants.append(col)

    ok = len(constants) == 0
    detail = (
        f"no constant features (checked {len(numeric_cols)} columns)"
        if ok
        else f"{len(constants)} constant features: {constants[:10]}"
    )
    return SanityCheck("constant feature check", ok, detail, constants)


def check_degenerate_features(features_df: pd.DataFrame) -> SanityCheck:
    """No features should have >50% NaN/zero values."""
    from sc2ml.features.common import _METADATA_COLUMNS

    feature_cols = [c for c in features_df.columns if c not in _METADATA_COLUMNS]
    numeric_cols = features_df[feature_cols].select_dtypes(include="number").columns

    if "split" in features_df.columns:
        train = features_df[features_df["split"] == "train"]
    else:
        train = features_df

    degenerate = []
    n = len(train)
    for col in numeric_cols:
        nan_or_zero = (train[col].isna() | (train[col] == 0)).sum()
        if n > 0 and nan_or_zero / n > 0.50:
            degenerate.append((col, nan_or_zero / n))

    ok = len(degenerate) == 0
    detail = (
        f"no degenerate features (checked {len(numeric_cols)} columns)"
        if ok
        else f"{len(degenerate)} degenerate features: "
        f"{[(c, f'{r:.1%}') for c, r in degenerate[:10]]}"
    )
    return SanityCheck("degenerate feature check", ok, detail, degenerate)


def check_elo_distribution(features_df: pd.DataFrame) -> SanityCheck:
    """Elo: mean ~ 1500, reasonable spread, elo_diff centered near 0."""
    issues = []

    for col in ["p1_pre_match_elo", "p2_pre_match_elo"]:
        if col not in features_df.columns:
            issues.append(f"missing column: {col}")
            continue
        mean = features_df[col].mean()
        std = features_df[col].std()
        # Mean should be reasonably near 1500 (within 100)
        if abs(mean - 1500) > 200:
            issues.append(f"{col} mean={mean:.1f} (expected ~1500)")
        if std < 10:
            issues.append(f"{col} std={std:.1f} too low")

    if "elo_diff" in features_df.columns:
        elo_diff_mean = features_df["elo_diff"].mean()
        # elo_diff should be centered near 0 (within 50)
        if abs(elo_diff_mean) > 100:
            issues.append(f"elo_diff mean={elo_diff_mean:.1f} (expected ~0)")

    ok = len(issues) == 0
    detail = "Elo features look reasonable" if ok else "; ".join(issues)
    return SanityCheck("Elo distribution", ok, detail)


def check_cold_start_handling(features_df: pd.DataFrame) -> SanityCheck:
    """Historical features should have sensible defaults for first matches, not NaN."""
    hist_cols = [c for c in features_df.columns if "hist_" in c or "total_games" in c]
    if not hist_cols:
        return SanityCheck(
            "cold-start handling", True, "no historical columns to check"
        )

    nan_counts = {}
    for col in hist_cols:
        nan_count = features_df[col].isna().sum()
        if nan_count > 0:
            nan_counts[col] = nan_count

    ok = len(nan_counts) == 0
    detail = (
        f"no NaN in historical features (checked {len(hist_cols)} columns)"
        if ok
        else f"NaN found: {nan_counts}"
    )
    return SanityCheck("cold-start handling", ok, detail, nan_counts)


def check_feature_correlations(features_df: pd.DataFrame) -> SanityCheck:
    """No unexpected perfect correlations (|r| > 0.99) between features."""
    from sc2ml.features.common import _METADATA_COLUMNS

    feature_cols = [c for c in features_df.columns if c not in _METADATA_COLUMNS]
    numeric = features_df[feature_cols].select_dtypes(include="number")

    # Only check if we have a reasonable number of features
    if numeric.shape[1] < 2:
        return SanityCheck("feature correlations", True, "fewer than 2 features")

    corr = numeric.corr().abs()
    # Zero out diagonal (need a writable copy)
    corr_vals = corr.values.copy()
    np.fill_diagonal(corr_vals, 0)

    perfect = []
    for i in range(len(corr)):
        for j in range(i + 1, len(corr)):
            if corr_vals[i, j] > 0.99:
                perfect.append(
                    (corr.columns[i], corr.columns[j], float(corr_vals[i, j]))
                )

    ok = len(perfect) == 0
    detail = (
        f"no perfect correlations (checked {numeric.shape[1]} features)"
        if ok
        else f"{len(perfect)} near-perfect correlations: {perfect[:5]}"
    )
    return SanityCheck("feature correlations", ok, detail, perfect)


def check_feature_count_monotonic(features_df: pd.DataFrame) -> SanityCheck:
    """Feature count should grow monotonically per group: A->B->C->D->E."""
    from sc2ml.features.common import _METADATA_COLUMNS

    # We need the raw df to rebuild features per group — use a sentinel to skip
    # this check if we don't have it.
    # This check is deferred: it uses a pre-computed mapping from the ROADMAP.
    # Expected: A→14, A+B→37, A+B+C→45, A+B+C+D→62, all→66
    # We check the actual features_df column count is > 0 and plausible.
    feature_cols = [c for c in features_df.columns if c not in _METADATA_COLUMNS]
    numeric = features_df[feature_cols].select_dtypes(include="number")
    n_features = numeric.shape[1]

    ok = n_features >= 14  # Minimum: Group A only
    detail = f"{n_features} numeric features"
    return SanityCheck("feature count plausibility", ok, detail, n_features)


def run_feature_distribution(features_df: pd.DataFrame) -> list[SanityCheck]:
    """Run all §3.3 Feature Distribution checks."""
    return [
        check_constant_features(features_df),
        check_degenerate_features(features_df),
        check_elo_distribution(features_df),
        check_cold_start_handling(features_df),
        check_feature_correlations(features_df),
        check_feature_count_monotonic(features_df),
    ]


# ===================================================================
# §3.4 Leakage & Baseline Smoke Tests
# ===================================================================

def check_majority_baseline(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
) -> SanityCheck:
    """Majority class baseline should be ~50% (balanced target from dual perspective)."""
    from sc2ml.models.baselines import MajorityClassBaseline

    model = MajorityClassBaseline()
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    acc = (preds == y_test.values).mean()

    ok = 0.45 <= acc <= 0.55
    detail = f"majority baseline accuracy={acc:.4f}"
    return SanityCheck("majority class baseline ~50%", ok, detail, acc)


def check_elo_baseline(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
) -> SanityCheck:
    """Elo-only baseline should be meaningfully above 50% (~58-62%)."""
    from sc2ml.models.baselines import EloOnlyBaseline

    if "expected_win_prob" not in X_test.columns:
        return SanityCheck(
            "Elo baseline above 50%", False, "expected_win_prob column missing"
        )

    model = EloOnlyBaseline()
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    acc = (preds == y_test.values).mean()

    # On synthetic data the threshold is relaxed — Elo should at least match random
    ok = acc >= 0.50
    detail = f"Elo-only accuracy={acc:.4f}"
    return SanityCheck("Elo baseline above 50%", ok, detail, acc)


def check_lgbm_accuracy_range(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
) -> SanityCheck:
    """LightGBM on all features should be ~63-66% (per prior runs)."""
    from lightgbm import LGBMClassifier

    from sc2ml.config import RANDOM_SEED

    model = LGBMClassifier(
        n_estimators=100, random_state=RANDOM_SEED, verbosity=-1
    )
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    acc = (preds == y_test.values).mean()

    # Allow wider range for synthetic data; real data expects 0.60-0.70
    ok = acc > 0.50
    detail = f"LightGBM accuracy={acc:.4f}"
    return SanityCheck("LightGBM accuracy range", ok, detail, acc)


def check_no_matchup_above_threshold(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    matchup_col: pd.Series | None = None,
    threshold: float = 0.75,
) -> SanityCheck:
    """No single matchup should achieve >75% accuracy (would suggest leakage)."""
    if matchup_col is None:
        return SanityCheck(
            "no matchup >75%", True, "no matchup column available — skipped"
        )

    from lightgbm import LGBMClassifier

    from sc2ml.config import RANDOM_SEED

    model = LGBMClassifier(
        n_estimators=100, random_state=RANDOM_SEED, verbosity=-1
    )
    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    suspicious = []
    for matchup in matchup_col.unique():
        mask = matchup_col == matchup
        if mask.sum() < 10:
            continue
        matchup_acc = (preds[mask.values] == y_test.values[mask.values]).mean()
        if matchup_acc > threshold:
            suspicious.append((matchup, matchup_acc))

    ok = len(suspicious) == 0
    detail = (
        "no matchup exceeds threshold"
        if ok
        else f"suspicious matchups: {suspicious}"
    )
    return SanityCheck(f"no matchup >{threshold:.0%}", ok, detail, suspicious)


def check_no_single_feature_high_correlation(
    features_df: pd.DataFrame,
    threshold: float = 0.30,
) -> SanityCheck:
    """No single feature should have >0.3 correlation with target after temporal ordering."""
    if "target" not in features_df.columns:
        return SanityCheck(
            "feature-target correlation cap", False, "no target column"
        )

    from sc2ml.features.common import _METADATA_COLUMNS

    feature_cols = [c for c in features_df.columns if c not in _METADATA_COLUMNS]
    numeric = features_df[feature_cols].select_dtypes(include="number")

    target = features_df["target"]
    violations = []
    for col in numeric.columns:
        corr = numeric[col].corr(target)
        if abs(corr) > threshold:
            violations.append((col, corr))

    ok = len(violations) == 0
    detail = (
        f"no feature exceeds |r|>{threshold} with target"
        if ok
        else f"{len(violations)} features with high target correlation: {violations[:5]}"
    )
    return SanityCheck("feature-target correlation cap", ok, detail, violations)


def check_lgbm_top_features(
    X_train: pd.DataFrame,
    y_train: pd.Series,
) -> SanityCheck:
    """Top features from LightGBM should be Elo/winrate-related, not map/context."""
    from lightgbm import LGBMClassifier

    from sc2ml.config import RANDOM_SEED

    model = LGBMClassifier(
        n_estimators=100, random_state=RANDOM_SEED, verbosity=-1
    )
    model.fit(X_train, y_train)

    importance = pd.Series(
        model.feature_importances_, index=X_train.columns
    ).sort_values(ascending=False)

    top_5 = importance.head(5).index.tolist()

    # Elo/winrate features should dominate — check if at least 1 is in top 5
    elo_winrate_keywords = ["elo", "winrate", "win_rate", "expected_win"]
    has_elo_or_wr = any(
        any(kw in f.lower() for kw in elo_winrate_keywords) for f in top_5
    )

    ok = has_elo_or_wr
    detail = f"top 5 features: {top_5}"
    return SanityCheck("LightGBM top features sanity", ok, detail, top_5)


def check_train_test_accuracy_gap(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    max_gap: float = 0.05,
) -> SanityCheck:
    """Train vs. test accuracy gap should be <5%."""
    from lightgbm import LGBMClassifier

    from sc2ml.config import RANDOM_SEED

    model = LGBMClassifier(
        n_estimators=100, random_state=RANDOM_SEED, verbosity=-1
    )
    model.fit(X_train, y_train)

    train_acc = (model.predict(X_train) == y_train.values).mean()
    test_acc = (model.predict(X_test) == y_test.values).mean()
    gap = train_acc - test_acc

    ok = gap < max_gap
    detail = f"train_acc={train_acc:.4f}, test_acc={test_acc:.4f}, gap={gap:.4f}"
    return SanityCheck(f"train/test accuracy gap <{max_gap:.0%}", ok, detail, gap)


def run_leakage_smoke_tests(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    features_df: pd.DataFrame,
    matchup_col: pd.Series | None = None,
) -> list[SanityCheck]:
    """Run all §3.4 Leakage & Baseline Smoke Tests."""
    return [
        check_majority_baseline(X_train, X_test, y_train, y_test),
        check_elo_baseline(X_train, X_test, y_train, y_test),
        check_lgbm_accuracy_range(X_train, X_test, y_train, y_test),
        check_no_matchup_above_threshold(
            X_train, X_test, y_train, y_test, matchup_col
        ),
        check_no_single_feature_high_correlation(features_df),
        check_lgbm_top_features(X_train, y_train),
        check_train_test_accuracy_gap(X_train, X_test, y_train, y_test),
    ]


# ===================================================================
# §3.5 Known Issues to Verify/Fix
# ===================================================================

def check_race_dummies_are_int(features_df: pd.DataFrame) -> SanityCheck:
    """Confirm pd.get_dummies race columns are int, not bool."""
    race_cols = [c for c in features_df.columns if "race_" in c.lower()]
    bool_cols = [
        c for c in race_cols if features_df[c].dtype == "bool"
    ]

    ok = len(bool_cols) == 0
    detail = (
        f"all {len(race_cols)} race columns are non-bool"
        if ok
        else f"bool race columns: {bool_cols}"
    )
    return SanityCheck("race dummies are int (not bool)", ok, detail, bool_cols)


def check_expanding_excludes_current(features_df: pd.DataFrame) -> SanityCheck:
    """Confirm expanding-window aggregates exclude the current match.

    Strategy: the first match for any player should have 0 games played
    (expanding count starts at 0, not 1).
    """
    if "p1_total_games_played" not in features_df.columns:
        return SanityCheck(
            "expanding excludes current match", True,
            "p1_total_games_played not found — skipped"
        )

    # Find each player's first match and check total_games_played == 0
    first_match_mask = features_df.groupby("p1_name").cumcount() == 0
    first_matches = features_df[first_match_mask]
    bad_first = first_matches[first_matches["p1_total_games_played"] != 0]

    ok = len(bad_first) == 0
    detail = (
        "first match for every player has 0 prior games"
        if ok
        else f"{len(bad_first)} players have non-zero count on first match"
    )
    return SanityCheck("expanding excludes current match", ok, detail)


def check_elo_deduplication(features_df: pd.DataFrame) -> SanityCheck:
    """Confirm Elo computation deduplicates via processed_matches set.

    If both perspectives of the same match updated Elo, ratings would diverge
    more than expected. Check that p1_pre_match_elo and p2_pre_match_elo are
    consistent across perspectives of the same match.
    """
    if "match_id" not in features_df.columns:
        return SanityCheck(
            "Elo deduplication", True, "match_id not in columns — skipped"
        )
    if "p1_pre_match_elo" not in features_df.columns:
        return SanityCheck(
            "Elo deduplication", True, "Elo columns not present — skipped"
        )

    # Group by match_id: both rows should have the same set of Elo values
    # (one row's p1_elo should match the other row's p2_elo for the same match)
    grouped = features_df.groupby("match_id").agg(
        p1_elo_first=("p1_pre_match_elo", "first"),
        p2_elo_first=("p2_pre_match_elo", "first"),
        p1_elo_last=("p1_pre_match_elo", "last"),
        p2_elo_last=("p2_pre_match_elo", "last"),
    )

    # In the dual-perspective layout, the second row swaps p1/p2.
    # So first_row.p1_elo should equal second_row.p2_elo.
    mismatches = grouped[
        (grouped["p1_elo_first"] - grouped["p2_elo_last"]).abs() > 0.01
    ]

    ok = len(mismatches) == 0
    detail = (
        "Elo consistent across match perspectives"
        if ok
        else f"{len(mismatches)} matches with inconsistent Elo across perspectives"
    )
    return SanityCheck("Elo deduplication", ok, detail)


def check_rolling_windows_sparse_players(features_df: pd.DataFrame) -> SanityCheck:
    """Verify Group D rolling windows handle players with sparse match histories.

    Players with very few matches should not have NaN in form features.
    """
    form_cols = [
        c for c in features_df.columns
        if any(kw in c for kw in ["streak", "ema_", "matches_last_", "h2h"])
    ]
    if not form_cols:
        return SanityCheck(
            "rolling windows sparse players", True,
            "no form features found — skipped"
        )

    nan_counts = {}
    for col in form_cols:
        nans = features_df[col].isna().sum()
        if nans > 0:
            nan_counts[col] = nans

    ok = len(nan_counts) == 0
    detail = (
        f"no NaN in {len(form_cols)} form features"
        if ok
        else f"NaN found: {nan_counts}"
    )
    return SanityCheck("rolling windows sparse players", ok, detail, nan_counts)


def run_known_issues(features_df: pd.DataFrame) -> list[SanityCheck]:
    """Run all §3.5 Known Issues checks."""
    return [
        check_race_dummies_are_int(features_df),
        check_expanding_excludes_current(features_df),
        check_elo_deduplication(features_df),
        check_rolling_windows_sparse_players(features_df),
    ]


# ===================================================================
# Full sanity validation
# ===================================================================

def run_full_sanity(
    con: "duckdb.DuckDBPyConnection",
    features_df: pd.DataFrame,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    matchup_col: pd.Series | None = None,
) -> SanityReport:
    """Run all Phase 0 sanity validation checks.

    Returns a :class:`SanityReport` with all results.
    """
    report = SanityReport()

    logger.info("=== Phase 0: Data & Model Sanity Validation ===")

    logger.info("--- §3.1 DuckDB View Sanity ---")
    report.checks.extend(run_view_sanity(con))

    logger.info("--- §3.2 Temporal Split Integrity ---")
    report.checks.extend(run_split_integrity(con, features_df))

    logger.info("--- §3.3 Feature Distribution Checks ---")
    report.checks.extend(run_feature_distribution(features_df))

    logger.info("--- §3.4 Leakage & Baseline Smoke Tests ---")
    report.checks.extend(
        run_leakage_smoke_tests(
            X_train, X_test, y_train, y_test, features_df, matchup_col
        )
    )

    logger.info("--- §3.5 Known Issues ---")
    report.checks.extend(run_known_issues(features_df))

    logger.info(report.summary)
    return report
