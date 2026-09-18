"""Gate and corruption tests in isolated workspaces; no experiment/API calls."""

import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from src.synthetic import load_dataset, _sha256_file
from src.synthetic_pipeline import (prepare_synthetic, validate_synthetic, freeze_synthetic,
    verify_synthetic, default_candidate, default_frozen, select_spotcheck, write_json,
    SEMANTIC_FILES, FROZEN_FILES, _hashes, _manual_review, prerequisites)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def workspace(tmp_path_factory):
    ws = tmp_path_factory.mktemp("synthetic-freeze")
    for name in ["config/synthetic_templates.json", "config/synthetic_approval.json", "config/data_ground_truth.json",
                 "data/metadata/attack_manifest.json", "attack/raw/enterprise-v19.2/enterprise-attack-19.2.json"]:
        target = ws / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    (ws / ".tmp").mkdir()
    prepare_synthetic(ws)
    return ws


def test_prepare_requires_valid_reference_and_approval(workspace, tmp_path):
    ws = tmp_path / "missing"
    with pytest.raises(OSError): prepare_synthetic(ws)
    source = workspace / "config/synthetic_templates.json"
    data = source.read_bytes()
    try:
        source.write_bytes(data + b" ")
        with pytest.raises(ValueError, match="registry SHA"):
            prerequisites(workspace)
    finally: source.write_bytes(data)


def test_prepare_refuses_to_overwrite_candidates(workspace):
    with pytest.raises(ValueError, match="must be empty"):
        prepare_synthetic(workspace)


def test_freeze_requires_validation_and_manual_inspection(workspace):
    with pytest.raises(ValueError, match="validate-synthetic"):
        freeze_synthetic(workspace)
    result = validate_synthetic(workspace)
    assert result['passed'] and result['statistics']['total_pairs']==670
    with pytest.raises(FileNotFoundError, match="synthetic_manual_review"):
        freeze_synthetic(workspace)


@pytest.fixture(scope="module")
def frozen(workspace):
    validate_synthetic(workspace)
    directory=default_candidate(workspace)
    pairs=load_dataset(directory)
    package=(workspace/'data/audit/synthetic_manual_spotcheck.md').read_bytes()
    metadata=json.loads((directory/'generation_metadata.json').read_text())
    # Explicit TEST-ONLY stand-in to exercise the review gate. It does not certify
    # a research dataset or write the production review record.
    review={'reviewer':'pytest fixture, not research approval',
            'review_method':'agent_inspected_raw_inference_ground_truth',
            'package_sha256':hashlib.sha256(package).hexdigest(),
            'registry_sha256':metadata['registry_sha256'],
            'semantic_artifact_sha256':_hashes(directory,SEMANTIC_FILES),
            'cases':{p.pair_id:{'status':'PASS','notes':'TEST ONLY gate fixture'} for p in select_spotcheck(pairs)},
            'unresolved_findings':[]}
    write_json(workspace/'data/audit/synthetic_manual_review.json',review)
    freeze_synthetic(workspace)
    return default_frozen(workspace)


def test_frozen_roundtrip_and_same_seed_reproduction(workspace, frozen):
    result=verify_synthetic(workspace)
    assert result['passed'] and result['pairs']==670 and result['views']==1340
    assert result['run_a_sha256']==result['run_b_sha256']
    assert result['reproducibility_hash_mismatches']==0
    assert set(p.name for p in frozen.iterdir()) == FROZEN_FILES | {'dataset_manifest.json'}


@pytest.mark.parametrize("filename", ["events.jsonl", "views.jsonl", "pairs.jsonl", "ground_truth.jsonl", "inference.jsonl", "statistics.json"])
def test_frozen_artifact_tampering_rejected(workspace, frozen, filename):
    path=frozen/filename;data=path.read_bytes()
    try:
        path.write_bytes(data+b' ')
        with pytest.raises(ValueError,match='SHA-256 mismatch'):
            verify_synthetic(workspace)
    finally:path.write_bytes(data)


def test_missing_manifest_entry_rejected(workspace,frozen):
    path=frozen/'dataset_manifest.json';data=path.read_bytes()
    try:
        manifest=json.loads(data);del manifest['files']['events.jsonl'];write_json(path,manifest)
        with pytest.raises(ValueError,match='file set mismatch'):verify_synthetic(workspace)
    finally:path.write_bytes(data)


def test_rehashed_sidecar_cannot_disagree_with_pairs(workspace,frozen):
    path=frozen/'views.jsonl';manifest_path=frozen/'dataset_manifest.json'
    data,original=path.read_bytes(),manifest_path.read_bytes()
    try:
        rows=data.splitlines();record=json.loads(rows[0]);record['event_ids']=[]
        rows[0]=json.dumps(record).encode();path.write_bytes(b'\n'.join(rows)+b'\n')
        manifest=json.loads(original);manifest['files']['views.jsonl']=_sha256_file(path);write_json(manifest_path,manifest)
        with pytest.raises(ValueError,match='sidecar content mismatch'):verify_synthetic(workspace)
    finally:path.write_bytes(data);manifest_path.write_bytes(original)


def test_manual_review_cannot_leave_unresolved_findings(workspace,frozen):
    pairs=load_dataset(frozen);package=(frozen/'manual_spotcheck.md').read_bytes()
    review=json.loads((frozen/'manual_review.json').read_text())
    review['unresolved_findings']=['semantic inconsistency']
    with pytest.raises(ValueError,match='remain unresolved'):
        _manual_review(pairs,package,review,review['registry_sha256'],_hashes(frozen,SEMANTIC_FILES))


def test_cli_verification_failure_returns_nonzero(tmp_path):
    result=subprocess.run([sys.executable,'-m','src.data_ground_truth','verify-synthetic','--workspace',str(tmp_path)],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode==1 and 'Synthetic gate FAILED' in result.stdout
