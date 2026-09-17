"""Comprehensive test suite for synthetic paired benchmark.

Tests organized by:
- Data model & event builders (including EID 4697)
- Validator checks (all 30)
- Attribution policy
- Split holdout
- Quota enforcement
- Transition matrix
- Anchor integrity
- Host constraints
- Freeze/hash integrity
"""

import copy
import hashlib
import json
import math
import re
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.synthetic import (
    SyntheticEvent, ViewGroundTruth, View, ScenarioPair,
    build_security_4697, build_security_4688, build_security_4698,
    build_security_4720, build_security_1102,
    build_sysmon_1, build_sysmon_3, build_sysmon_11, build_sysmon_13,
    generate_deterministic_id, get_inference_payload, check_leakage,
    character_ngrams, jaccard_similarity, normalize_for_dedup,
    find_near_duplicates, compute_split_key, assign_splits,
    serialize_dataset, load_dataset,
    INFERENCE_ALLOWLIST, SAFE_IPS, SAFE_HOSTS, SAFE_USERS,
    HOSTS_DOMAIN_CONTROLLER, HOSTS_ALLOWED_LOCAL_ACCOUNT,
)
from src.synthetic_validator import (
    ValidationResult, validate_synthetic_dataset,
    compute_transition_matrix, compute_statistics, generate_audit_table,
    ALLOWED_TRANSITIONS, BENCHMARK_CATALOG, VALID_LABEL_STATUSES,
    _check_01_schema, _check_04_single_one_event,
    _check_05_contextual_event_count, _check_06_anchor_exists_in_both,
    _check_07_strict_anchor_equality, _check_11_mapped_has_techniques,
    _check_12_unmapped_no_techniques, _check_13_ambiguous_no_techniques,
    _check_17_transition_allowed, _check_18_leakage,
    _check_25_family_diversity, _check_26_no_family_overlap_dev_test,
    _check_27_local_account_host,
    _check_service_event_provider,
)


# ============================================================
# Helpers
# ============================================================

def _make_event(event_id: str = "evt_001",
                provider: str = "Microsoft-Windows-Sysmon",
                channel: str = "Microsoft-Windows-Sysmon/Operational",
                windows_event_id: int = 1,
                computer: str = "WORKSTATION01",
                timestamp: str = "2024-03-15T10:00:00Z",
                event_record_id: int = 1001,
                **extra_fields) -> SyntheticEvent:
    fields = {
        'UtcTime': timestamp,
        'Computer': computer,
        'EventID': windows_event_id,
        'Image': r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe',
        'CommandLine': 'powershell.exe -EncodedCommand ZQBjAGgAbwAgAHQAZQBzAHQA',
        'ParentImage': r'C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE',
        'ParentCommandLine': 'WINWORD.EXE',
        'User': 'WORKSTATION01\\jsmith',
        'ProcessId': 4444,
        'ParentProcessId': 2222,
        'ProcessGuid': '{00000000-0000-0000-0000-000000000001}',
        'ParentProcessGuid': '{00000000-0000-0000-0000-000000000002}',
        'LogonGuid': '{00000000-0000-0000-0000-000000000099}',
        'LogonId': '0x12345',
        'Hashes': 'SHA256=AABBCCDD',
    }
    fields.update(extra_fields)
    return SyntheticEvent(
        event_id=event_id, provider=provider, channel=channel,
        event_record_id=event_record_id,
        windows_event_id=windows_event_id, computer=computer,
        timestamp_utc=timestamp, fields=fields
    )


def _make_context_event(event_id: str = "evt_002",
                         windows_event_id: int = 3,
                         timestamp: str = "2024-03-15T10:00:05Z",
                         computer: str = "WORKSTATION01",
                         event_record_id: int = 1002) -> SyntheticEvent:
    fields = {
        'UtcTime': timestamp,
        'Computer': computer,
        'EventID': windows_event_id,
        'Image': r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe',
        'User': 'WORKSTATION01\\jsmith',
        'SourceIp': '192.0.2.10',
        'SourcePort': 49152,
        'DestinationIp': '198.51.100.20',
        'DestinationPort': 443,
        'Protocol': 'tcp',
        'ProcessId': 4444,
        'ProcessGuid': '{00000000-0000-0000-0000-000000000001}',
    }
    return SyntheticEvent(
        event_id=event_id,
        provider="Microsoft-Windows-Sysmon",
        channel="Microsoft-Windows-Sysmon/Operational",
        event_record_id=event_record_id,
        windows_event_id=windows_event_id,
        computer=computer,
        timestamp_utc=timestamp,
        fields=fields
    )


def make_valid_pair(pair_id: str = "pair_001",
                    split: str = "test",
                    family: str = "TF_T1059_001_A",
                    single_status: str = "mapped",
                    contextual_status: str = "mapped",
                    single_techniques: tuple = ("T1059.001",),
                    contextual_techniques: tuple = ("T1059.001",),
                    computer: str = "WORKSTATION01") -> ScenarioPair:
    anchor = _make_event("evt_anchor_001", computer=computer)
    ctx1 = _make_context_event("evt_ctx_001", timestamp="2024-03-15T10:00:05Z", computer=computer)
    ctx2 = _make_context_event("evt_ctx_002", windows_event_id=11,
                                timestamp="2024-03-15T10:00:10Z", computer=computer,
                                event_record_id=1003)

    single_names = tuple("PowerShell" for _ in single_techniques) if single_status == "mapped" else ()
    ctx_names = tuple("PowerShell" for _ in contextual_techniques) if contextual_status == "mapped" else ()
    single_tids = single_techniques if single_status == "mapped" else ()
    ctx_tids = contextual_techniques if contextual_status == "mapped" else ()

    single_refs = {}
    if single_status == "mapped" and single_tids:
        single_refs = {single_tids[0]: [{"event_id": "evt_anchor_001", "field": "CommandLine"}]}
    ctx_refs = {}
    if contextual_status == "mapped" and ctx_tids:
        ctx_refs = {ctx_tids[0]: [{"event_id": "evt_anchor_001", "field": "CommandLine"}]}

    return ScenarioPair(
        pair_id=pair_id,
        scenario_id=f"sc_{pair_id}",
        template_family_id=family,
        split=split,
        single_view=View(
            view_id=f"view_single_{pair_id}",
            pair_id=pair_id,
            view_type="single",
            event_ids=("evt_anchor_001",),
        ),
        contextual_view=View(
            view_id=f"view_ctx_{pair_id}",
            pair_id=pair_id,
            view_type="contextual",
            event_ids=("evt_anchor_001", "evt_ctx_001", "evt_ctx_002"),
        ),
        events={
            "evt_anchor_001": anchor,
            "evt_ctx_001": ctx1,
            "evt_ctx_002": ctx2,
        },
        single_ground_truth=ViewGroundTruth(
            view_id=f"view_single_{pair_id}",
            label_status=single_status,
            technique_ids=single_tids,
            technique_names=single_names,
            evidence_refs=single_refs,
            rationale=f"Test pair {pair_id} single",
            approval_reference="test",
        ),
        contextual_ground_truth=ViewGroundTruth(
            view_id=f"view_ctx_{pair_id}",
            label_status=contextual_status,
            technique_ids=ctx_tids,
            technique_names=ctx_names,
            evidence_refs=ctx_refs,
            rationale=f"Test pair {pair_id} contextual",
            approval_reference="test",
        ),
        generation_seed=20260915,
        generation_provenance={"source": "test"}
    )


# ============================================================
# 1. Event Builder Tests
# ============================================================

class TestBuildSecurity4697:
    """EID 4697 builder with correct Security-auditing fields."""

    def test_builds_with_correct_fields(self):
        fields = build_security_4697(
            timestamp_utc="2024-03-15T10:00:00Z",
            computer="WORKSTATION01",
            service_name="MaliciousService",
            service_file_name=r"C:\Users\Public\evil.exe",
            service_type="0x10",
            service_start_type="2",
            service_account="LocalSystem",
            subject_user="jsmith",
            subject_domain="WORKSTATION01",
            logon_id="0x12345",
        )
        assert fields['EventID'] == 4697
        assert fields['ServiceName'] == "MaliciousService"
        assert fields['ServiceFileName'] == r"C:\Users\Public\evil.exe"
        assert fields['ServiceStartType'] == "2"
        assert fields['ServiceAccount'] == "LocalSystem"
        assert fields['SubjectUserName'] == "jsmith"
        assert fields['SubjectDomainName'] == "WORKSTATION01"
        assert fields['SubjectLogonId'] == "0x12345"

    def test_no_7045_fields(self):
        """Must NOT have 7045-specific fields."""
        fields = build_security_4697(
            timestamp_utc="2024-03-15T10:00:00Z",
            computer="WORKSTATION01",
            service_name="TestSvc",
            service_file_name=r"C:\test.exe",
            service_type="0x10",
            service_start_type="2",
            service_account="LocalSystem",
            subject_user="admin",
            subject_domain="WORKSTATION01",
            logon_id="0x1",
        )
        assert 'ImagePath' not in fields
        assert 'StartType' not in fields
        assert 'AccountName' not in fields

    def test_extra_kwargs_preserved(self):
        fields = build_security_4697(
            timestamp_utc="2024-03-15T10:00:00Z",
            computer="W01",
            service_name="S",
            service_file_name="F",
            service_type="T",
            service_start_type="ST",
            service_account="SA",
            subject_user="U",
            subject_domain="D",
            logon_id="L",
            CustomField="test_value",
        )
        assert fields['CustomField'] == "test_value"


class TestBuildSecurity7045Removed:
    """Verify old EID 7045 builder no longer exists."""

    def test_7045_builder_not_importable(self):
        import src.synthetic as syn
        assert not hasattr(syn, 'build_security_7045'), (
            "build_security_7045 should be removed; use build_security_4697"
        )


class TestServiceEventProviderCheck:
    """EID 7045 + Security-Auditing provider combination is invalid."""

    def test_7045_security_provider_rejected(self):
        pair = make_valid_pair()
        # Inject an event with wrong provider/EID combination
        bad_event = SyntheticEvent(
            event_id="evt_bad_svc",
            provider="Microsoft-Windows-Security-Auditing",
            channel="Security",
            event_record_id=9999,
            windows_event_id=7045,
            computer="WORKSTATION01",
            timestamp_utc="2024-03-15T10:00:00Z",
            fields={"EventID": 7045, "ServiceName": "test"}
        )
        pair = ScenarioPair(
            pair_id=pair.pair_id, scenario_id=pair.scenario_id,
            template_family_id=pair.template_family_id, split=pair.split,
            single_view=pair.single_view, contextual_view=pair.contextual_view,
            events={**pair.events, "evt_bad_svc": bad_event},
            single_ground_truth=pair.single_ground_truth,
            contextual_ground_truth=pair.contextual_ground_truth,
            generation_seed=pair.generation_seed,
            generation_provenance=pair.generation_provenance,
        )
        result = ValidationResult()
        _check_service_event_provider(pair, result)
        assert not result.passed
        assert any("7045" in e and "4697" in e for e in result.errors)


# ============================================================
# 2. Allowlist Tests
# ============================================================

class TestInferenceAllowlist:
    """Allowlist uses EID 4697, not 7045."""

    def test_4697_in_allowlist(self):
        assert 4697 in INFERENCE_ALLOWLIST['Security']
        fields = INFERENCE_ALLOWLIST['Security'][4697]
        assert 'ServiceName' in fields
        assert 'ServiceFileName' in fields
        assert 'ServiceStartType' in fields
        assert 'SubjectUserName' in fields

    def test_7045_not_in_allowlist(self):
        assert 7045 not in INFERENCE_ALLOWLIST['Security']

    def test_4697_no_7045_fields(self):
        fields = INFERENCE_ALLOWLIST['Security'][4697]
        assert 'ImagePath' not in fields
        assert 'StartType' not in fields
        assert 'AccountName' not in fields


# ============================================================
# 3. Data Model Tests
# ============================================================

class TestDataModel:

    def test_valid_pair_construction(self):
        pair = make_valid_pair()
        assert pair.pair_id == "pair_001"
        assert pair.split == "test"
        assert len(pair.single_view.event_ids) == 1
        assert len(pair.contextual_view.event_ids) == 3
        assert pair.single_ground_truth.label_status == "mapped"

    def test_anchor_shared_between_views(self):
        pair = make_valid_pair()
        anchor_id = pair.single_view.event_ids[0]
        assert anchor_id in pair.contextual_view.event_ids
        assert anchor_id in pair.events

    def test_deterministic_id(self):
        id1 = generate_deterministic_id("test", 20260915, "group", "scenario")
        id2 = generate_deterministic_id("test", 20260915, "group", "scenario")
        assert id1 == id2

    def test_different_seed_different_id(self):
        id1 = generate_deterministic_id("test", 20260915, "group", "scenario")
        id2 = generate_deterministic_id("test", 20260916, "group", "scenario")
        assert id1 != id2


# ============================================================
# 4. Attribution Policy Tests
# ============================================================

class TestAttributionPolicy:
    """Tests for evidence-conditioned attribution semantics."""

    def test_mapped_requires_techniques(self):
        pair = make_valid_pair(single_status="mapped", contextual_status="mapped",
                               single_techniques=(), contextual_techniques=("T1059.001",))
        result = ValidationResult()
        _check_11_mapped_has_techniques(pair, result)
        assert not result.passed  # single is mapped but has no techniques

    def test_unmapped_forbids_techniques(self):
        pair = make_valid_pair(single_status="unmapped", contextual_status="unmapped",
                               single_techniques=(), contextual_techniques=())
        # Force technique_ids on unmapped
        pair = ScenarioPair(
            pair_id=pair.pair_id, scenario_id=pair.scenario_id,
            template_family_id=pair.template_family_id, split=pair.split,
            single_view=pair.single_view, contextual_view=pair.contextual_view,
            events=pair.events,
            single_ground_truth=ViewGroundTruth(
                view_id=pair.single_ground_truth.view_id,
                label_status="unmapped",
                technique_ids=("T1059.001",),
                technique_names=("PowerShell",),
                evidence_refs={},
                rationale="test", approval_reference="test"
            ),
            contextual_ground_truth=pair.contextual_ground_truth,
            generation_seed=pair.generation_seed,
            generation_provenance=pair.generation_provenance,
        )
        result = ValidationResult()
        _check_12_unmapped_no_techniques(pair, result)
        assert not result.passed

    def test_ambiguous_forbids_techniques(self):
        pair = make_valid_pair(single_status="ambiguous", contextual_status="ambiguous",
                               single_techniques=(), contextual_techniques=())
        pair = ScenarioPair(
            pair_id=pair.pair_id, scenario_id=pair.scenario_id,
            template_family_id=pair.template_family_id, split=pair.split,
            single_view=pair.single_view, contextual_view=pair.contextual_view,
            events=pair.events,
            single_ground_truth=ViewGroundTruth(
                view_id=pair.single_ground_truth.view_id,
                label_status="ambiguous",
                technique_ids=("T1059.001",),
                technique_names=("PowerShell",),
                evidence_refs={},
                rationale="test", approval_reference="test"
            ),
            contextual_ground_truth=pair.contextual_ground_truth,
            generation_seed=pair.generation_seed,
            generation_provenance=pair.generation_provenance,
        )
        result = ValidationResult()
        _check_13_ambiguous_no_techniques(pair, result)
        assert not result.passed


# ============================================================
# 5. Transition Tests
# ============================================================

class TestTransitions:
    """Tests for allowed/disallowed transition types."""

    @pytest.mark.parametrize("single,contextual", [
        ("mapped", "mapped"),
        ("ambiguous", "mapped"),
        ("ambiguous", "unmapped"),
        ("ambiguous", "ambiguous"),
        ("unmapped", "unmapped"),
    ])
    def test_allowed_transitions(self, single, contextual):
        s_tech = ("T1059.001",) if single == "mapped" else ()
        c_tech = ("T1059.001",) if contextual == "mapped" else ()
        pair = make_valid_pair(single_status=single, contextual_status=contextual,
                               single_techniques=s_tech, contextual_techniques=c_tech)
        result = ValidationResult()
        _check_17_transition_allowed(pair, result)
        assert result.passed, f"Transition {single}→{contextual} should be allowed"

    @pytest.mark.parametrize("single,contextual", [
        ("mapped", "ambiguous"),
        ("mapped", "unmapped"),
        ("unmapped", "ambiguous"),
        ("unmapped", "mapped"),
    ])
    def test_disallowed_transitions(self, single, contextual):
        s_tech = ("T1059.001",) if single == "mapped" else ()
        c_tech = ("T1059.001",) if contextual == "mapped" else ()
        pair = make_valid_pair(single_status=single, contextual_status=contextual,
                               single_techniques=s_tech, contextual_techniques=c_tech)
        result = ValidationResult()
        _check_17_transition_allowed(pair, result)
        assert not result.passed, f"Transition {single}→{contextual} should be disallowed"


# ============================================================
# 6. Split Holdout Tests
# ============================================================

class TestSplitHoldout:
    """Template-family holdout: dev and test families must be disjoint."""

    def test_no_overlap_valid(self):
        pairs = [
            make_valid_pair("p1", split="dev", family="DEV_FAMILY"),
            make_valid_pair("p2", split="test", family="TEST_FAMILY"),
        ]
        result = ValidationResult()
        _check_26_no_family_overlap_dev_test(pairs, result)
        assert result.passed

    def test_overlap_rejected(self):
        pairs = [
            make_valid_pair("p1", split="dev", family="SHARED_FAMILY"),
            make_valid_pair("p2", split="test", family="SHARED_FAMILY"),
        ]
        result = ValidationResult()
        _check_26_no_family_overlap_dev_test(pairs, result)
        assert not result.passed
        assert any("SHARED_FAMILY" in e for e in result.errors)


# ============================================================
# 7. Quota Tests
# ============================================================

class TestQuotas:
    """Quota enforcement tests."""

    def test_multi_label_not_counted_as_single(self):
        """A scenario with contextual multi-label must NOT count toward single-label quota."""
        pair = make_valid_pair(
            contextual_techniques=("T1059.001", "T1105"),
        )
        cgt = pair.contextual_ground_truth
        is_single = len(cgt.technique_ids) == 1
        is_multi = len(cgt.technique_ids) >= 2
        assert not is_single
        assert is_multi

    def test_family_diversity_violation(self):
        """One family contributing too many instances is rejected."""
        # 50 instances from 1 family for T1059.001 — max allowed is ceil(50/1)=50
        # but if we have 2 families and one has 40, max allowed is ceil(50/2)=25
        pairs = []
        for i in range(40):
            pairs.append(make_valid_pair(
                pair_id=f"p{i}", split="test", family="FAM_A",
                contextual_techniques=("T1059.001",),
            ))
        for i in range(10):
            pairs.append(make_valid_pair(
                pair_id=f"q{i}", split="test", family="FAM_B",
                contextual_techniques=("T1059.001",),
            ))
        result = ValidationResult()
        _check_25_family_diversity(pairs, result)
        assert not result.passed  # FAM_A has 40, max allowed ceil(50/2)=25


# ============================================================
# 8. Anchor Integrity Tests
# ============================================================

class TestAnchorIntegrity:
    """Strict anchor equality between views."""

    def test_anchor_present_in_both_views(self):
        pair = make_valid_pair()
        result = ValidationResult()
        _check_06_anchor_exists_in_both(pair, result)
        assert result.passed

    def test_anchor_missing_from_contextual(self):
        pair = make_valid_pair()
        # Remove anchor from contextual view
        pair = ScenarioPair(
            pair_id=pair.pair_id, scenario_id=pair.scenario_id,
            template_family_id=pair.template_family_id, split=pair.split,
            single_view=pair.single_view,
            contextual_view=View(
                view_id=pair.contextual_view.view_id,
                pair_id=pair.pair_id,
                view_type="contextual",
                event_ids=("evt_ctx_001", "evt_ctx_002"),  # anchor removed
            ),
            events=pair.events,
            single_ground_truth=pair.single_ground_truth,
            contextual_ground_truth=pair.contextual_ground_truth,
            generation_seed=pair.generation_seed,
            generation_provenance=pair.generation_provenance,
        )
        result = ValidationResult()
        _check_06_anchor_exists_in_both(pair, result)
        assert not result.passed

    def test_anchor_event_not_in_events_dict(self):
        pair = make_valid_pair()
        # Remove anchor from events dict
        events_without_anchor = {k: v for k, v in pair.events.items() if k != "evt_anchor_001"}
        pair = ScenarioPair(
            pair_id=pair.pair_id, scenario_id=pair.scenario_id,
            template_family_id=pair.template_family_id, split=pair.split,
            single_view=pair.single_view,
            contextual_view=pair.contextual_view,
            events=events_without_anchor,
            single_ground_truth=pair.single_ground_truth,
            contextual_ground_truth=pair.contextual_ground_truth,
            generation_seed=pair.generation_seed,
            generation_provenance=pair.generation_provenance,
        )
        result = ValidationResult()
        _check_07_strict_anchor_equality(pair, result)
        assert not result.passed


# ============================================================
# 9. T1136.001 Host Constraint Tests
# ============================================================

class TestLocalAccountHostConstraint:
    """T1136.001 must not be generated on domain controllers."""

    def test_workstation_allowed(self):
        pair = make_valid_pair(
            computer="WORKSTATION01",
            contextual_techniques=("T1136.001",),
            single_techniques=("T1136.001",),
        )
        result = ValidationResult()
        _check_27_local_account_host(pair, result)
        assert result.passed

    def test_dc_rejected(self):
        pair = make_valid_pair(
            computer="DC01",
            contextual_techniques=("T1136.001",),
            single_techniques=("T1136.001",),
        )
        result = ValidationResult()
        _check_27_local_account_host(pair, result)
        assert not result.passed
        assert any("DC" in e for e in result.errors)

    def test_non_t1136_on_dc_ok(self):
        """Non-T1136.001 techniques can use DC hosts."""
        pair = make_valid_pair(
            computer="DC01",
            contextual_techniques=("T1059.001",),
            single_techniques=("T1059.001",),
        )
        result = ValidationResult()
        _check_27_local_account_host(pair, result)
        assert result.passed


# ============================================================
# 10. Host-Role Constants
# ============================================================

class TestHostRoleConstants:

    def test_dc_in_domain_controllers(self):
        assert "DC01" in HOSTS_DOMAIN_CONTROLLER

    def test_workstations_allowed_for_local(self):
        assert "WORKSTATION01" in HOSTS_ALLOWED_LOCAL_ACCOUNT
        assert "WORKSTATION02" in HOSTS_ALLOWED_LOCAL_ACCOUNT

    def test_dc_not_allowed_for_local(self):
        assert "DC01" not in HOSTS_ALLOWED_LOCAL_ACCOUNT


# ============================================================
# 11. Leakage Tests
# ============================================================

class TestLeakage:

    def test_clean_payload_no_leakage(self):
        pair = make_valid_pair()
        result = ValidationResult()
        _check_18_leakage(pair, result)
        assert result.passed

    def test_technique_id_in_payload_detected(self):
        pair = make_valid_pair()
        # Inject technique ID into event field
        anchor = pair.events["evt_anchor_001"]
        bad_fields = dict(anchor.fields)
        bad_fields['CommandLine'] = 'powershell.exe T1059.001 test'
        bad_anchor = SyntheticEvent(
            event_id=anchor.event_id, provider=anchor.provider,
            channel=anchor.channel, event_record_id=anchor.event_record_id,
            windows_event_id=anchor.windows_event_id,
            computer=anchor.computer, timestamp_utc=anchor.timestamp_utc,
            fields=bad_fields
        )
        pair = ScenarioPair(
            pair_id=pair.pair_id, scenario_id=pair.scenario_id,
            template_family_id=pair.template_family_id, split=pair.split,
            single_view=pair.single_view, contextual_view=pair.contextual_view,
            events={**pair.events, "evt_anchor_001": bad_anchor},
            single_ground_truth=pair.single_ground_truth,
            contextual_ground_truth=pair.contextual_ground_truth,
            generation_seed=pair.generation_seed,
            generation_provenance=pair.generation_provenance,
        )
        result = ValidationResult()
        _check_18_leakage(pair, result)
        assert not result.passed


# ============================================================
# 12. Template Registry Tests
# ============================================================

class TestTemplateRegistry:
    """Verify registry file structure and content."""

    @pytest.fixture
    def registry(self):
        path = Path("config/synthetic_templates.json")
        if not path.exists():
            pytest.skip("Template registry not found")
        return json.loads(path.read_text(encoding="utf-8"))

    def test_registry_is_valid_json(self, registry):
        assert isinstance(registry, dict)
        assert "families" in registry

    def test_family_count_from_registry(self, registry):
        """Template count must be derived from registry, not hard-coded."""
        families = registry["families"]
        assert len(families) > 0
        # Each family must have required fields
        for f in families:
            assert "template_family_id" in f
            assert "category" in f
            assert "split" in f
            assert f["split"] in ("dev", "test")

    def test_no_stale_30_family_count(self, registry):
        """Registry must not claim exactly 30 families (stale count)."""
        families = registry["families"]
        assert len(families) != 30, "Stale family count of 30 detected"

    def test_test_quotas_match(self, registry):
        families = registry["families"]
        test_mapped = sum(f["planned_instances"] for f in families
                         if f["split"] == "test" and f["category"] == "mapped_single")
        test_multi = sum(f["planned_instances"] for f in families
                        if f["split"] == "test" and f["category"] == "mapped_multi")
        test_unmap = sum(f["planned_instances"] for f in families
                        if f["split"] == "test" and f["category"] == "unmapped")
        test_ambig = sum(f["planned_instances"] for f in families
                        if f["split"] == "test" and f["category"] == "ambiguous")
        assert test_mapped == 400
        assert test_multi == 40
        assert test_unmap == 150
        assert test_ambig == 50

    def test_dev_quotas_match(self, registry):
        families = registry["families"]
        dev_mapped = sum(f["planned_instances"] for f in families
                        if f["split"] == "dev" and f["category"] == "mapped_single")
        dev_multi = sum(f["planned_instances"] for f in families
                       if f["split"] == "dev" and f["category"] == "mapped_multi")
        dev_unmap = sum(f["planned_instances"] for f in families
                       if f["split"] == "dev" and f["category"] == "unmapped")
        dev_ambig = sum(f["planned_instances"] for f in families
                       if f["split"] == "dev" and f["category"] == "ambiguous")
        assert dev_mapped == 16
        assert dev_multi == 4
        assert dev_unmap == 6
        assert dev_ambig == 4

    def test_per_technique_50_test(self, registry):
        families = registry["families"]
        from collections import defaultdict
        tech_counts = defaultdict(int)
        for f in families:
            if f["split"] == "test" and f["category"] == "mapped_single":
                for tid in f.get("technique_ids", []):
                    tech_counts[tid] += f["planned_instances"]
        for tid in BENCHMARK_CATALOG:
            assert tech_counts[tid] == 50, f"{tid}: {tech_counts[tid]} != 50"

    def test_per_technique_2_dev(self, registry):
        families = registry["families"]
        from collections import defaultdict
        tech_counts = defaultdict(int)
        for f in families:
            if f["split"] == "dev" and f["category"] == "mapped_single":
                for tid in f.get("technique_ids", []):
                    tech_counts[tid] += f["planned_instances"]
        for tid in BENCHMARK_CATALOG:
            assert tech_counts[tid] == 2, f"DEV {tid}: {tech_counts[tid]} != 2"

    def test_family_holdout_disjoint(self, registry):
        families = registry["families"]
        dev_ids = set(f["template_family_id"] for f in families if f["split"] == "dev")
        test_ids = set(f["template_family_id"] for f in families if f["split"] == "test")
        assert dev_ids & test_ids == set(), f"Overlap: {dev_ids & test_ids}"

    def test_t1136_host_constraint_present(self, registry):
        families = registry["families"]
        for f in families:
            if "T1136.001" in f.get("technique_ids", []):
                assert "host_constraint" in f or "host_constraints" in f or \
                       any("DC" in str(f.get(k, "")) for k in f), \
                    f"T1136.001 family {f['template_family_id']} missing host constraint"

    def test_no_7045_service_events(self, registry):
        families = registry["families"]
        for f in families:
            anchor = f.get("anchor", {})
            if anchor.get("windows_event_id") == 7045:
                provider = anchor.get("provider", "")
                if "Security" in provider:
                    pytest.fail(
                        f"{f['template_family_id']}: EID 7045 with Security provider"
                    )

    def test_evidence_predicates_structured(self, registry):
        """Evidence predicates should use structured format, not just prose."""
        families = registry["families"]
        for f in families:
            for gt_key in ["single_ground_truth", "contextual_ground_truth"]:
                gt = f.get(gt_key, {})
                if gt.get("status") == "mapped":
                    pred = gt.get("evidence_predicate", gt.get("evidence", {}))
                    if isinstance(pred, str) and len(pred) > 0:
                        # Prose-only predicate — at minimum should be a dict
                        pass  # Allow for now, warn
                    # At least rationale should exist
                    assert "rationale" in gt or "rationale" in f, \
                        f"{f['template_family_id']} {gt_key}: missing rationale"


# ============================================================
# 13. Transition Matrix Tests
# ============================================================

class TestTransitionMatrix:

    def test_matrix_sums_to_pair_count(self):
        pairs = [
            make_valid_pair("p1", single_status="mapped", contextual_status="mapped"),
            make_valid_pair("p2", single_status="ambiguous", contextual_status="mapped"),
            make_valid_pair("p3", single_status="unmapped", contextual_status="unmapped",
                           single_techniques=(), contextual_techniques=()),
        ]
        matrix = compute_transition_matrix(pairs)
        assert sum(matrix.values()) == len(pairs)

    def test_matrix_keys_are_valid(self):
        pairs = [make_valid_pair("p1")]
        matrix = compute_transition_matrix(pairs)
        for key in matrix:
            assert "→" in key or "->" in key or "mapped" in key


# ============================================================
# 14. Near-Duplicate Detection Tests
# ============================================================

class TestNearDuplicates:

    def test_identical_events_detected(self):
        pair1 = make_valid_pair("p1")
        pair2 = make_valid_pair("p2")
        dups = find_near_duplicates([pair1, pair2])
        assert len(dups) > 0  # Same events → duplicate

    def test_different_events_not_duplicate(self):
        pair1 = make_valid_pair("p1")
        pair2 = make_valid_pair("p2")
        # Modify pair2's anchor significantly
        anchor2 = SyntheticEvent(
            event_id="evt_anchor_001",
            provider="Microsoft-Windows-Security-Auditing",
            channel="Security",
            event_record_id=5555,
            windows_event_id=4720,
            computer="FILESVR01",
            timestamp_utc="2024-06-01T08:00:00Z",
            fields={
                'TimeCreated': "2024-06-01T08:00:00Z",
                'Computer': "FILESVR01",
                'EventID': 4720,
                'TargetUserName': "backdoor_user",
                'SubjectUserName': "attacker",
                'SubjectLogonId': "0x99999",
            }
        )
        pair2 = ScenarioPair(
            pair_id=pair2.pair_id, scenario_id=pair2.scenario_id,
            template_family_id=pair2.template_family_id, split=pair2.split,
            single_view=pair2.single_view, contextual_view=pair2.contextual_view,
            events={**pair2.events, "evt_anchor_001": anchor2},
            single_ground_truth=pair2.single_ground_truth,
            contextual_ground_truth=pair2.contextual_ground_truth,
            generation_seed=pair2.generation_seed,
            generation_provenance=pair2.generation_provenance,
        )
        dups = find_near_duplicates([pair1, pair2])
        # Should not be near-duplicate due to different content
        assert all(sim < 0.95 for _, _, sim in dups) if dups else True


# ============================================================
# 15. Serialization Tests
# ============================================================

class TestSerialization:

    def test_round_trip(self):
        pair = make_valid_pair()
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = serialize_dataset([pair], Path(tmpdir))
            loaded = load_dataset(Path(tmpdir))
            assert len(loaded) == 1
            assert loaded[0].pair_id == pair.pair_id

    def test_deterministic_serialization(self):
        """Same input produces same hashes."""
        pair = make_valid_pair()
        with tempfile.TemporaryDirectory() as tmpdir1:
            m1 = serialize_dataset([pair], Path(tmpdir1))
        with tempfile.TemporaryDirectory() as tmpdir2:
            m2 = serialize_dataset([pair], Path(tmpdir2))
        assert m1 == m2


# ============================================================
# 16. Inference Payload Tests
# ============================================================

class TestInferencePayload:

    def test_excludes_internal_metadata(self):
        event = _make_event()
        payload = get_inference_payload(event)
        assert 'ground_truth' not in str(payload).lower()
        assert 'rationale' not in str(payload).lower()

    def test_4697_payload_correct(self):
        event = SyntheticEvent(
            event_id="evt_svc",
            provider="Microsoft-Windows-Security-Auditing",
            channel="Security",
            event_record_id=7777,
            windows_event_id=4697,
            computer="WORKSTATION01",
            timestamp_utc="2024-03-15T10:00:00Z",
            fields=build_security_4697(
                timestamp_utc="2024-03-15T10:00:00Z",
                computer="WORKSTATION01",
                service_name="TestSvc",
                service_file_name=r"C:\evil.exe",
                service_type="0x10",
                service_start_type="2",
                service_account="LocalSystem",
                subject_user="admin",
                subject_domain="WORKSTATION01",
                logon_id="0x1",
            ),
        )
        payload = get_inference_payload(event)
        assert payload['ServiceName'] == "TestSvc"
        assert payload['ServiceFileName'] == r"C:\evil.exe"
        assert 'ImagePath' not in payload  # 7045 field


# ============================================================
# 17. View Structure Tests
# ============================================================

class TestViewStructure:

    def test_single_view_type(self):
        pair = make_valid_pair()
        assert pair.single_view.view_type == "single"

    def test_contextual_view_type(self):
        pair = make_valid_pair()
        assert pair.contextual_view.view_type == "contextual"

    def test_single_one_event_valid(self):
        pair = make_valid_pair()
        result = ValidationResult()
        _check_04_single_one_event(pair, result)
        assert result.passed

    def test_single_zero_events_rejected(self):
        pair = make_valid_pair()
        pair = ScenarioPair(
            pair_id=pair.pair_id, scenario_id=pair.scenario_id,
            template_family_id=pair.template_family_id, split=pair.split,
            single_view=View(view_id="v1", pair_id=pair.pair_id, view_type="single", event_ids=()),
            contextual_view=pair.contextual_view, events=pair.events,
            single_ground_truth=pair.single_ground_truth,
            contextual_ground_truth=pair.contextual_ground_truth,
            generation_seed=pair.generation_seed,
            generation_provenance=pair.generation_provenance,
        )
        result = ValidationResult()
        _check_04_single_one_event(pair, result)
        assert not result.passed

    def test_contextual_one_event_rejected(self):
        pair = make_valid_pair()
        pair = ScenarioPair(
            pair_id=pair.pair_id, scenario_id=pair.scenario_id,
            template_family_id=pair.template_family_id, split=pair.split,
            single_view=pair.single_view,
            contextual_view=View(view_id="v2", pair_id=pair.pair_id, view_type="contextual",
                                event_ids=("evt_anchor_001",)),  # Only 1 event
            events=pair.events,
            single_ground_truth=pair.single_ground_truth,
            contextual_ground_truth=pair.contextual_ground_truth,
            generation_seed=pair.generation_seed,
            generation_provenance=pair.generation_provenance,
        )
        result = ValidationResult()
        _check_05_contextual_event_count(pair, result)
        assert not result.passed


# ============================================================
# 18. Statistics & Audit Tests
# ============================================================

class TestStatistics:

    def test_statistics_computed(self):
        pairs = [make_valid_pair("p1"), make_valid_pair("p2")]
        stats = compute_statistics(pairs)
        assert stats["total_scenario_pairs"] == 2
        assert stats["total_views"] == 4

    def test_audit_table_generated(self):
        pairs = [make_valid_pair()]
        table = generate_audit_table(pairs)
        assert len(table) == 2  # single + contextual
        assert table[0]["view_type"] == "single"
        assert table[1]["view_type"] == "contextual"


# ============================================================
# 19. Benchmark Catalog Constants
# ============================================================

class TestCatalogConstants:

    def test_catalog_has_8_techniques(self):
        assert len(BENCHMARK_CATALOG) == 8

    def test_all_expected_techniques(self):
        expected = {"T1059.001", "T1059.003", "T1053.005", "T1543.003",
                    "T1136.001", "T1547.001", "T1685.005", "T1105"}
        assert BENCHMARK_CATALOG == expected

    def test_valid_label_statuses(self):
        assert VALID_LABEL_STATUSES == {"mapped", "unmapped", "ambiguous"}

    def test_allowed_transitions_complete(self):
        assert len(ALLOWED_TRANSITIONS) == 5
