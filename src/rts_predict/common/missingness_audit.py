"""Shared missingness-audit helpers for cleaning notebooks.

Extracted from inline definitions in the three 01_04_01 cleaning notebooks
(sc2egset, aoestats, aoe2companion) to eliminate duplication (NOTE-3 fix).

Invariants applied:
- I6 (reproducibility): all SQL produced by these helpers must appear verbatim
  in the notebook artifact JSON (callers' responsibility).
- I9 (phase-boundary discipline): these helpers document missingness only;
  they do not transform data. Transformation is Phase 02's responsibility.
"""
from __future__ import annotations

import logging
from typing import Any

import duckdb
import pandas as pd

logger = logging.getLogger(__name__)

_VALID_MECHANISMS: frozenset[str] = frozenset({"MAR", "MCAR", "MNAR", "N/A"})
_VALID_RECOMMENDATIONS: frozenset[str] = frozenset(
    {
        "DROP_COLUMN",
        "FLAG_FOR_IMPUTATION",
        "RETAIN_AS_IS",
        "EXCLUDE_TARGET_NULL_ROWS",
        "CONVERT_SENTINEL_TO_NULL",
    }
)


def _build_sentinel_predicate(
    col: str, sentinel_value: Any
) -> tuple[str | None, str | None]:
    """Construct SQL predicate for sentinel matching.

    Args:
        col: Column name (unused in predicate construction; kept for call-site
            symmetry with callers that pass the column name).
        sentinel_value: The sentinel value declared in the missingness spec, or
            ``None`` when no sentinel applies.

    Returns:
        A tuple ``(predicate_sql, sentinel_repr)`` where ``predicate_sql`` is a
        SQL fragment (e.g. ``"= 0"`` or ``"IN (0, 1)"`` ) and ``sentinel_repr``
        is a human-readable string representation.  Both elements are ``None``
        when ``sentinel_value`` is ``None``.
    """
    if sentinel_value is None:
        return None, None
    if isinstance(sentinel_value, list):
        quoted = []
        for v in sentinel_value:
            if isinstance(v, str):
                quoted.append("'" + v.replace("'", "''") + "'")
            else:
                quoted.append(repr(v))
        return f'IN ({", ".join(quoted)})', repr(sentinel_value)
    if isinstance(sentinel_value, str):
        escaped = sentinel_value.replace("'", "''")
        return f"= '{escaped}'", repr(sentinel_value)
    return f"= {sentinel_value!r}", repr(sentinel_value)


def _sentinel_census(
    view_name: str,
    total_rows: int,
    spec: dict[str, Any],
    con: duckdb.DuckDBPyConnection,
) -> list[dict[str, Any]]:
    """Run sentinel COUNT(*) FILTER per spec-declared column.

    Args:
        view_name: Name of the DuckDB VIEW to query.
        total_rows: Total row count of the view (used to compute pct_sentinel).
        spec: Missingness spec dict mapping column name to a dict with at least
            ``"sentinel_value"`` key.
        con: Active DuckDB connection with the view registered.

    Returns:
        List of dicts with keys ``column``, ``sentinel_value``, ``n_sentinel``,
        ``pct_sentinel``.  One entry per spec column.  If a spec column is
        absent from the VIEW, ``n_sentinel=0`` is returned (guarded by
        ``except Exception``).
    """
    rows = []
    for col, meta in spec.items():
        sentinel_value = meta["sentinel_value"]
        predicate, sentinel_repr = _build_sentinel_predicate(col, sentinel_value)
        if predicate is None:
            n_sentinel = 0
        else:
            sql = (
                f'SELECT COUNT(*) FILTER (WHERE "{col}" {predicate}) FROM {view_name}'
            )
            try:
                row = con.execute(sql).fetchone()
                n_sentinel = row[0] if row is not None else 0
            except Exception:
                # Column not present in this VIEW — skip silently.
                n_sentinel = 0
        pct_sentinel = (
            round(100.0 * n_sentinel / total_rows, 4) if total_rows > 0 else 0.0
        )
        rows.append(
            {
                "column": col,
                "sentinel_value": sentinel_repr,
                "n_sentinel": int(n_sentinel),
                "pct_sentinel": float(pct_sentinel),
            }
        )
    return rows


def _detect_constants(
    view_name: str,
    columns: list[str],
    con: duckdb.DuckDBPyConnection,
    identity_cols: frozenset[str] = frozenset(),
) -> dict[str, int | None]:
    """Per-column distinct-value count. Returns ``{col: n_distinct | None}``.

    Args:
        view_name: Name of the DuckDB VIEW to query.
        columns: List of column names to inspect.
        con: Active DuckDB connection with the view registered.
        identity_cols: Columns to skip (W6: identity columns are expensive and
            never constant by definition).

    Returns:
        Dict mapping column name to ``n_distinct`` (int) or ``None`` when the
        column was skipped (identity column).
    """
    out: dict[str, int | None] = {}
    for col in columns:
        if col in identity_cols:
            out[col] = None
            continue
        sql = f'SELECT COUNT(DISTINCT "{col}") FROM {view_name}'
        row = con.execute(sql).fetchone()
        out[col] = int(row[0]) if row is not None else 0
    return out


def _recommend(
    col: str,
    mechanism: str,
    pct: float,
    is_primary: bool,
    n_null: int,
    n_sentinel: int,
) -> tuple[str, str]:
    """Decision tree per ``temp/null_handling_recommendations.md`` §3.1.

    Args:
        col: Column name (used only for formatting justification text).
        mechanism: Declared missingness mechanism (``"MAR"``, ``"MCAR"``,
            ``"MNAR"``, or ``"N/A"``).
        pct: Combined missingness percentage (NULL + sentinel).
        is_primary: Whether the column is a primary feature (affects mid-rate
            recommendation in the 40–80% band).
        n_null: Observed NULL count.
        n_sentinel: Observed sentinel count.

    Returns:
        A tuple ``(recommendation_code, justification_text)`` where
        ``recommendation_code`` is one of the values in
        ``_VALID_RECOMMENDATIONS``.
    """
    # W3 fix: CONVERT_SENTINEL_TO_NULL fires for sentinel-only low-rate cases.
    if n_sentinel > 0 and n_null == 0 and pct < 5.0:
        return "CONVERT_SENTINEL_TO_NULL", (
            f"Low sentinel rate ({pct:.4f}%); convert sentinel to NULL via "
            f"NULLIF in 01_04_02+ DDL pass per Rule S3 (negligible rate). "
            f"Listwise deletion or simple imputation acceptable in Phase 02. "
            f"NOTE: if carries_semantic_content=True (consult ledger column), "
            f"this recommendation is non-binding — see corresponding DS entry "
            f"for the retain-as-category alternative."
        )
    if pct == 0.0:
        return "RETAIN_AS_IS", "Zero missingness observed; no action needed."
    if pct > 80.0:
        return "DROP_COLUMN", (
            f"NULL+sentinel rate {pct:.2f}% exceeds 80% (Rule S4 / van Buuren 2018). "
            f"Imputation indefensible at this rate."
        )
    if pct > 40.0:
        if mechanism == "MNAR":
            return "DROP_COLUMN", (
                f"Rate {pct:.2f}% in 40-80% MNAR band; no defensible imputation. "
                f"Drop unless domain knowledge provides correction."
            )
        if is_primary:
            return "FLAG_FOR_IMPUTATION", (
                f"Rate {pct:.2f}% in 40-80%; primary feature exception per Rule S4. "
                f"Phase 02: conditional imputation + add_indicator."
            )
        return "DROP_COLUMN", (
            f"Rate {pct:.2f}% in 40-80%; non-primary feature; cost/benefit favors "
            f"simplicity per Rule S4."
        )
    if pct > 5.0:
        return "FLAG_FOR_IMPUTATION", (
            f"Rate {pct:.2f}% in 5-40%; flag for Phase 02 imputation "
            f"(conditional for MAR, simple for MCAR per Rules from §3.1)."
        )
    # pct < 5% with at least one NULL (sentinel-only case handled above).
    return "RETAIN_AS_IS", (
        f"Rate {pct:.2f}% < 5% (Schafer & Graham 2002 boundary citation). "
        f"Listwise deletion or simple imputation acceptable in Phase 02."
    )


def _consolidate_ledger(
    view_name: str,
    df_null: pd.DataFrame,
    sentinel_rows: list[dict[str, Any]],
    spec: dict[str, Any],
    dtype_map: dict[str, str],
    total_rows: int,
    constants_map: dict[str, int | None],
    target_cols: set[str],
    identity_cols: frozenset[str] = frozenset(),
) -> pd.DataFrame:
    """Merge NULL census + sentinel census + constants + spec into one ledger row per column.

    Full-coverage (Option B): every column in the VIEW gets a row.

    Override priority (B4 + B5 + W7):

    0. Identity branch (B5): route to ``mechanism=N/A``, ``RETAIN_AS_IS``.
    1. Constants override (W7): ``n_distinct==1`` AND no NULLs/sentinels →
       ``DROP_COLUMN``.
    2. F1 zero-missingness: ``n_total_missing==0`` → ``RETAIN_AS_IS``.
    3. Spec / fallback recommendation via ``_recommend()``.
    4. Target post-step (B4): ``col in target_cols`` AND ``n_total_missing>0``
       → ``EXCLUDE_TARGET_NULL_ROWS``.

    Args:
        view_name: Name of the VIEW being audited (stored in each ledger row).
        df_null: Per-column NULL census DataFrame; must have ``null_count``
            column and either ``column_name`` or ``column`` as the column-name
            field.
        sentinel_rows: Output of ``_sentinel_census``.
        spec: Full missingness spec dict (superset of this VIEW's columns is OK).
        dtype_map: Mapping of column name → DuckDB type string (from DESCRIBE).
        total_rows: Total row count of the VIEW.
        constants_map: Output of ``_detect_constants``.
        target_cols: Set of target column names for this VIEW.
        identity_cols: Set of identity column names for this VIEW.

    Returns:
        DataFrame with exactly 17 columns matching Deliverable 5.B schema.
    """
    sentinel_map = {r["column"]: r for r in sentinel_rows}
    ledger = []
    col_field = "column_name" if "column_name" in df_null.columns else "column"
    for _, nrow in df_null.iterrows():
        col = nrow[col_field]
        n_null = int(nrow["null_count"])
        pct_null = float(nrow.get("null_pct", round(100.0 * n_null / total_rows, 4)))
        srow = sentinel_map.get(
            col, {"sentinel_value": None, "n_sentinel": 0, "pct_sentinel": 0.0}
        )
        n_sentinel = int(srow["n_sentinel"])
        pct_sentinel = float(srow["pct_sentinel"])
        n_total_missing = n_null + n_sentinel
        pct_missing_total = round(pct_null + pct_sentinel, 4)
        spec_entry = spec.get(col)
        n_distinct = constants_map.get(col, None)

        if col in identity_cols:
            mechanism = "N/A"
            mech_just = (
                "Identity column; n_distinct check skipped per W6 (constants-detection "
                "runtime budget). Zero NULLs by definition (asserted upstream)."
            )
            carries_sem = False
            is_primary = False
            rec = "RETAIN_AS_IS"
            rec_just = "Identity column; no missingness possible by upstream assertion."
        elif n_distinct == 1 and n_null == 0 and n_sentinel == 0:
            mechanism = "N/A"
            mech_just = (
                f"True constant column; n_distinct=1 across {total_rows:,} rows "
                f"(zero NULLs, zero sentinels). No information content for prediction. "
                f"Recommend drop in 01_04_02+."
            )
            carries_sem = False
            is_primary = False
            rec = "DROP_COLUMN"
            rec_just = "True constant column; n_distinct=1; no information content."
        elif n_total_missing == 0:
            mechanism = "N/A"
            mech_just = "Zero missingness observed; no action needed."
            carries_sem = bool(spec_entry["carries_semantic_content"]) if spec_entry else False
            is_primary = bool(spec_entry["is_primary_feature"]) if spec_entry else False
            rec = "RETAIN_AS_IS"
            rec_just = "Zero missingness observed; no action needed."
        elif spec_entry is not None:
            mechanism = spec_entry["mechanism"]
            mech_just = spec_entry["justification"]
            carries_sem = bool(spec_entry["carries_semantic_content"])
            is_primary = bool(spec_entry["is_primary_feature"])
            rec, rec_just = _recommend(
                col, mechanism, pct_missing_total, is_primary, n_null, n_sentinel
            )
        else:
            mechanism = "MAR"
            mech_just = (
                f"No _missingness_spec entry; conservative MAR assumption. "
                f"Observed effective missingness {pct_missing_total:.2f}% "
                f"(NULL: {pct_null:.2f}%, sentinel: {pct_sentinel:.2f}%)."
            )
            carries_sem = False
            is_primary = False
            rec, rec_just = _recommend(
                col, mechanism, pct_missing_total, is_primary, n_null, n_sentinel
            )

        if col in target_cols and n_total_missing > 0:
            rec = "EXCLUDE_TARGET_NULL_ROWS"
            rec_just = (
                "Per Rule S2: target NULLs/sentinels excluded from prediction "
                "scope, retained in history for feature computation. "
                "NEVER impute target."
            )

        ledger.append(
            {
                "view": view_name,
                "column": col,
                "dtype": dtype_map.get(col, "UNKNOWN"),
                "n_total": int(total_rows),
                "n_null": n_null,
                "pct_null": pct_null,
                "sentinel_value": srow["sentinel_value"],
                "n_sentinel": n_sentinel,
                "pct_sentinel": pct_sentinel,
                "pct_missing_total": pct_missing_total,
                "n_distinct": n_distinct,
                "mechanism": mechanism,
                "mechanism_justification": mech_just,
                "recommendation": rec,
                "recommendation_justification": rec_just,
                "carries_semantic_content": carries_sem,
                "is_primary_feature": is_primary,
            }
        )
    return pd.DataFrame(ledger)


def build_audit_views_block(
    view_ledgers: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Build canonical inline ``missingness_audit.views`` block.

    Args:
        view_ledgers: Mapping of view name to a dict with keys:
            - ``"total_rows"`` (int): total row count of the VIEW.
            - ``"df_ledger"`` (pd.DataFrame): output of ``_consolidate_ledger``.

    Returns:
        ``{"views": {view_name: {"total_rows": int, "columns_audited": int,
        "ledger": list[dict]}}}``.  Callers extract the inner dict via
        ``["views"]``.
    """
    views: dict[str, Any] = {}
    for view_name, entry in view_ledgers.items():
        df_ledger: pd.DataFrame = entry["df_ledger"]
        views[view_name] = {
            "total_rows": entry["total_rows"],
            "columns_audited": len(df_ledger),
            "ledger": df_ledger.to_dict(orient="records"),
        }
    return {"views": views}
