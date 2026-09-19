"""Stage B generation and independent behavior/semantic regression gates."""

from dataclasses import asdict, replace
from pathlib import Path
import copy
import hashlib
import json

import pytest

from src.synthetic import serialize_dataset, load_dataset, find_near_duplicates, get_inference_payload, check_leakage
from src.synthetic_generator import generate_dataset, generate_pair, SEED
from src.synthetic_predicates import validate_relation_contract, evaluate_predicate
from src.synthetic_stage_b_validation import audit_pair, validate_stage_b

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def generated():
    path = ROOT / "config/synthetic_templates.json"
    registry = json.loads(path.read_text(encoding="utf-8"))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return registry, digest, generate_dataset(registry, digest)


def test_exact_generated_quotas_and_all_structural_gates(generated, tmp_path):
    registry, digest, pairs = generated
    result = validate_stage_b(pairs, tmp_path, ROOT / "attack/raw/enterprise-v19.2/enterprise-attack-19.2.json", registry, ROOT / "config/synthetic_templates.json", digest)
    assert result.passed, result.errors
    assert result.warnings == []
    assert len(pairs) == 670 and result.statistics["views"] == 1340
    for split, total, single, multi, unmapped, ambiguous, per_tech in [
        ("test",640,400,40,150,50,50), ("dev",30,16,4,6,4,2),
    ]:
        actual = result.statistics["splits"][split]
        assert actual["pairs"] == total
        assert actual["categories"] == dict(mapped_single=single,mapped_multi=multi,unmapped=unmapped,ambiguous=ambiguous)
        assert actual["mapped_single_per_technique"] == {tid:per_tech for tid in registry["benchmark_catalog"]["technique_ids"]}
    assert result.statistics["near_duplicates"] == []
    assert {p.template_family_id for p in pairs if p.split == "test"}.isdisjoint({p.template_family_id for p in pairs if p.split == "dev"})
    for pair in pairs:
        assert len(pair.single_view.event_ids) == 1
        assert 2 <= len(pair.contextual_view.event_ids) <= 6
        assert pair.single_view.event_ids[0] in pair.contextual_view.event_ids
        assert not any(check_leakage(get_inference_payload(e)) for e in pair.events.values())


def test_parent_command_line_matches_visible_parent_and_rejects_mismatch(generated):
    registry, digest, pairs = generated
    pair = copy.deepcopy(next(p for p in pairs if p.template_family_id == "TF_T1059_001_A"))
    family = next(f for f in registry["families"] if f["template_family_id"] == pair.template_family_id)
    visible_processes = {
        event.fields["ProcessGuid"]: event
        for event in pair.events.values()
        if event.windows_event_id == 1
    }
    child = next(
        event for event in pair.events.values()
        if event.windows_event_id == 1 and event.fields.get("ParentProcessGuid") in visible_processes
    )
    parent = visible_processes[child.fields["ParentProcessGuid"]]
    assert child.fields["ParentCommandLine"] == parent.fields["CommandLine"]
    assert audit_pair(pair, family, digest) == []

    pair.events[child.event_id] = replace(
        child,
        fields={**child.fields, "ParentCommandLine": "C:\\Windows\\explorer.exe"},
    )
    assert any(
        "ParentCommandLine disagrees with visible parent process" in error
        for error in audit_pair(pair, family, digest)
    )


def test_inference_has_no_fixed_unmapped_vendor_or_maintenance_shortcut(generated):
    pairs = generated[2]
    for pair in pairs:
        for event in pair.events.values():
            payload = json.dumps(get_inference_payload(event), ensure_ascii=False)
            assert "contoso" not in payload.casefold()
            assert "maintenance" not in payload.casefold()


def test_same_seed_serialization_roundtrip_and_different_instances(generated, tmp_path):
    registry, digest, pairs = generated
    other = generate_dataset(registry, digest)
    a, b = tmp_path / "a", tmp_path / "b"
    assert serialize_dataset(pairs, a) == serialize_dataset(list(reversed(other)), b)
    assert load_dataset(a) == pairs
    family = registry["families"][0]
    assert generate_pair(family, SEED, 0, digest).pair_id != generate_pair(family, SEED, 1, digest).pair_id
    for path in a.glob("*.jsonl"):
        contents = path.read_bytes()
        assert contents.endswith(b"\n") and b"\r" not in contents and not contents.startswith(b"\xef\xbb\xbf")
    rows = [json.loads(line) for line in (a / "inference.jsonl").read_text().splitlines()]
    assert len(rows) == 1340
    assert all(set(row) == {"sample_id", "endpoint_evidence"} for row in rows)


@pytest.mark.parametrize("mutation,expected", [
    (lambda p: replace(p, split="dev" if p.split=="test" else "test"), "split"),
    (lambda p: replace(p, pair_id="pair_invalid"), "pair_id"),
    (lambda p: replace(p, generation_seed=1), "seed"),
    (lambda p: replace(p, single_view=replace(p.single_view, event_ids=p.contextual_view.event_ids)), "view event set"),
    (lambda p: replace(p, contextual_ground_truth=replace(p.contextual_ground_truth,label_status="ambiguous")), "ground truth"),
    (lambda p: replace(p, contextual_ground_truth=replace(p.contextual_ground_truth,technique_ids=("T1003",))), "ground truth"),
    (lambda p: replace(p, contextual_ground_truth=replace(p.contextual_ground_truth,technique_names=("Wrong Name",))), "ground truth"),
    (lambda p: replace(p, single_ground_truth=replace(p.single_ground_truth,evidence_refs={})), "reference"),
    (lambda p: replace(p, contextual_ground_truth=replace(p.contextual_ground_truth,approval_reference="unapproved")), "approval"),
])
def test_generated_pair_mutations_rejected(generated, mutation, expected):
    registry, digest, pairs = generated
    p = next(p for p in pairs if p.template_family_id == "TF_T1059_001_A")
    family = next(f for f in registry["families"] if f["template_family_id"]==p.template_family_id)
    assert any(expected in error for error in audit_pair(mutation(copy.deepcopy(p)),family,digest))


@pytest.mark.parametrize("mutation,expected", [
    (lambda e: replace(e,provider="Wrong-Provider"), "specification"),
    (lambda e: replace(e,windows_event_id=7045), "specification"),
    (lambda e: replace(e,computer="DC01",fields={**e.fields,"Computer":"DC01"}), "domain controller"),
    (lambda e: replace(e,fields={**e.fields,"TargetUserName":"T1059.001 ground_truth"}), "leakage"),
])
def test_telemetry_host_and_leakage_mutations(generated, mutation, expected):
    registry,digest,pairs=generated
    p=copy.deepcopy(next(p for p in pairs if p.template_family_id=="TF_T1136_001_A"))
    f=next(f for f in registry['families'] if f['template_family_id']==p.template_family_id)
    event=next(e for e in p.events.values() if e.windows_event_id==4720)
    p.events[event.event_id]=mutation(event)
    assert any(expected in e for e in audit_pair(p,f,digest))


@pytest.mark.parametrize("indicator", ["8.8.8.8", "https://real.example.com/payload"])
def test_unsafe_indicators_rejected(generated, indicator):
    registry,digest,pairs=generated
    p=copy.deepcopy(next(p for p in pairs if p.template_family_id=="TF_T1105_A"))
    f=next(f for f in registry['families'] if f['template_family_id']==p.template_family_id)
    e=p.events[p.single_view.event_ids[0]]
    p.events[e.event_id]=replace(e,fields={**e.fields,"CommandLine":e.fields['CommandLine']+' '+indicator})
    assert any("unsafe" in error for error in audit_pair(p,f,digest))


def test_duplicate_gate_ignores_decorative_logon_changes(generated):
    pair=generated[2][0]
    other=copy.deepcopy(replace(pair,pair_id="pair_other"))
    for eid,e in other.events.items():
        fields=dict(e.fields)
        if "SubjectLogonId" in fields: fields["SubjectLogonId"]="0x99999"
        if "LogonId" in fields: fields["LogonId"]="0x99999"
        other.events[eid]=replace(e,fields=fields)
    assert find_near_duplicates([pair,other],threshold=0.95)[0][2] == 1.0


def test_approved_relation_corrections_reject_original_defects(generated):
    registry=generated[0]
    family=copy.deepcopy(next(f for f in registry['families'] if f['template_family_id']=='TF_T1059_001_F'))
    assert validate_relation_contract(family)==[]
    family['contextual_event_specs'][0]['windows_event_id']=1
    assert any('two distinct process creations' in e for e in validate_relation_contract(family))
    family=copy.deepcopy(next(f for f in registry['families'] if f['template_family_id']=='TF_UNMAP_EVTCLR'))
    family['contextual_ground_truth']['evidence_predicate']['all'].append({'relation':'process_then_task','process':'context_2','task':'context_1'})
    assert any('cycle' in e for e in validate_relation_contract(family))


def test_frozen_seed_cannot_be_changed(generated):
    with pytest.raises(ValueError,match="Frozen seed"):
        generate_dataset(generated[0],generated[1],SEED+1)


def test_manual_audit_regressions(generated):
    from xml.etree import ElementTree
    from src.synthetic_predicates import same_process
    for p in generated[2]:
        for e in p.events.values():
            if e.windows_event_id == 4720:
                assert len(e.fields['TargetUserName']) <= 20
            for field in ['Image','NewProcessName','ParentImage','ParentProcessName']:
                assert e.fields.get(field) != r'C:\Windows\System32\explorer.exe'
            if e.windows_event_id == 13:
                assert e.fields['TargetObject'].startswith('HKU\\')
        if p.template_family_id == 'TF_T1053_005_A':
            task=p.events[p.single_view.event_ids[0]]
            xml=ElementTree.fromstring(task.fields['TaskContent'])
            args=xml.find('.//{*}Arguments').text
            assert '-WorkingDirectory' not in args
            assert xml.find('.//{*}WorkingDirectory') is not None
        if p.template_family_id == 'TF_T1059_001_DEV':
            events=list(p.events.values())
            assert same_process(events[0],events[1])


def test_task_namespace_is_not_an_unsafe_network_indicator(generated):
    registry,digest,pairs=generated
    pair=copy.deepcopy(next(p for p in pairs if p.template_family_id=='TF_T1053_005_A'))
    family=next(f for f in registry['families'] if f['template_family_id']==pair.template_family_id)
    assert not audit_pair(pair,family,digest)
    anchor=pair.events[pair.single_view.event_ids[0]]
    fields=dict(anchor.fields)
    fields['TaskContent']=fields['TaskContent'].replace('</Arguments>',' https://schemas.microsoft.com/download</Arguments>')
    pair.events[anchor.event_id]=replace(anchor,fields=fields)
    assert any('unsafe domain' in e for e in audit_pair(pair,family,digest))
