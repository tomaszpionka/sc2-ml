"""Tests for features/registry.py."""

from sc2ml.features.registry import FEATURE_GROUPS, FeatureGroup, get_groups


class TestFeatureGroup:
    def test_enum_has_five_members(self) -> None:
        assert len(FeatureGroup) == 5

    def test_ordering(self) -> None:
        ordered = list(FeatureGroup)
        assert ordered == [
            FeatureGroup.A,
            FeatureGroup.B,
            FeatureGroup.C,
            FeatureGroup.D,
            FeatureGroup.E,
        ]


class TestGetGroups:
    def test_up_to_a(self) -> None:
        assert get_groups(FeatureGroup.A) == [FeatureGroup.A]

    def test_up_to_c(self) -> None:
        assert get_groups(FeatureGroup.C) == [
            FeatureGroup.A, FeatureGroup.B, FeatureGroup.C
        ]

    def test_up_to_e_is_all(self) -> None:
        assert get_groups(FeatureGroup.E) == list(FeatureGroup)


class TestFeatureGroupsRegistry:
    def test_all_groups_registered(self) -> None:
        for g in FeatureGroup:
            assert g in FEATURE_GROUPS, f"{g} not registered"

    def test_compute_fns_are_callable(self) -> None:
        for spec in FEATURE_GROUPS.values():
            assert callable(spec.compute_fn)
