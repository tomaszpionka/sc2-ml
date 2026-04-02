"""Feature group registry for incremental ablation studies.

Each group maps to one compute function.  The :func:`get_groups` helper
returns an ordered subset of groups suitable for the ablation protocol
described in methodology Section 7.1.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Callable, NamedTuple

if TYPE_CHECKING:
    import pandas as pd


class FeatureGroup(str, Enum):
    """Pre-match feature groups (methodology Section 3.1)."""

    A = "elo"
    B = "historical"
    C = "matchup_map"
    D = "form_momentum"
    E = "context"


class GroupSpec(NamedTuple):
    """Metadata for a single feature group."""

    group: FeatureGroup
    compute_fn: Callable[..., "pd.DataFrame"]
    description: str


def get_groups(up_to: FeatureGroup) -> list[FeatureGroup]:
    """Return all groups from A up to (and including) *up_to*.

    >>> get_groups(FeatureGroup.C)
    [<FeatureGroup.A: 'elo'>, <FeatureGroup.B: 'historical'>, <FeatureGroup.C: 'matchup_map'>]
    """
    ordered = list(FeatureGroup)
    cutoff = ordered.index(up_to)
    return ordered[: cutoff + 1]


# ---------------------------------------------------------------------------
# Registry — populated by _populate() at first import
# ---------------------------------------------------------------------------

FEATURE_GROUPS: dict[FeatureGroup, GroupSpec] = {}


def _populate() -> None:
    """Import each group module and register its compute function.

    Deferred to avoid circular imports (group modules import from common.py,
    but not from registry.py).
    """
    from sc2ml.features.group_a_elo import compute_elo_features
    from sc2ml.features.group_b_historical import compute_historical_features
    from sc2ml.features.group_c_matchup import compute_matchup_features
    from sc2ml.features.group_d_form import compute_form_features
    from sc2ml.features.group_e_context import compute_context_features

    FEATURE_GROUPS[FeatureGroup.A] = GroupSpec(
        FeatureGroup.A, compute_elo_features, "Dynamic K-factor Elo ratings"
    )
    FEATURE_GROUPS[FeatureGroup.B] = GroupSpec(
        FeatureGroup.B, compute_historical_features, "Historical aggregates + variance"
    )
    FEATURE_GROUPS[FeatureGroup.C] = GroupSpec(
        FeatureGroup.C, compute_matchup_features, "Matchup & map features"
    )
    FEATURE_GROUPS[FeatureGroup.D] = GroupSpec(
        FeatureGroup.D, compute_form_features, "Form & momentum features"
    )
    FEATURE_GROUPS[FeatureGroup.E] = GroupSpec(
        FeatureGroup.E, compute_context_features, "Context features"
    )


_populate()
