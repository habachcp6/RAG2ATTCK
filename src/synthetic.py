"""
Core synthetic benchmark data model and generator infrastructure for RAG2ATTCK.
"""

import hashlib
import json
import random
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Optional

# ==============================================================================
# 1. Data Model (Frozen Dataclasses)
# ==============================================================================

@dataclass(frozen=True)
class SyntheticEvent:
    event_id: str           # Unique in dataset, format: 'evt_XXXXXXXX'
    provider: str           # 'Microsoft-Windows-Security-Auditing' or 'Microsoft-Windows-Sysmon'
    channel: str            # 'Security' or 'Microsoft-Windows-Sysmon/Operational'
    event_record_id: int
    windows_event_id: int   # Windows EventID (4688, 4698, 7045, 1, 3, 11, 13...)
    computer: str
    timestamp_utc: str      # ISO 8601 UTC
    fields: Dict[str, Any]  # Provider-specific telemetry fields

@dataclass(frozen=True)
class ViewGroundTruth:
    view_id: str
    label_status: str       # 'mapped', 'unmapped', 'ambiguous'
    technique_ids: Tuple[str, ...]
    technique_names: Tuple[str, ...]
    evidence_refs: Dict[str, List[Dict[str, Any]]]  # technique_id -> [{event_id, fields}]
    rationale: str
    approval_reference: str

@dataclass(frozen=True)
class View:
    view_id: str            # 'view_XXXXXXXX'
    pair_id: str
    view_type: str          # 'single' or 'contextual'
    event_ids: Tuple[str, ...]

@dataclass(frozen=True)
class ScenarioPair:
    pair_id: str            # 'pair_XXXXXXXX'
    scenario_id: str        # 'scen_XXXXXXXX'
    template_family_id: str
    split: str              # 'dev' or 'test'
    single_view: View
    contextual_view: View
    events: Dict[str, SyntheticEvent]  # event_id -> event
    single_ground_truth: ViewGroundTruth
    contextual_ground_truth: ViewGroundTruth
    generation_seed: int
    generation_provenance: Dict[str, Any]

@dataclass(frozen=True)
class TemplateFamilySpec:
    template_family_id: str
    description: str
    behavior_description: str
    mitre_source: str       # ATT&CK URL
    windows_event_doc: str  # Windows event documentation reference
    telemetry_providers: Tuple[str, ...]
    relevant_windows_event_ids: Tuple[int, ...]
    anchor_event_rule: str  # How anchor is selected
    anchor_windows_event_id: int
    contextual_event_descriptions: Tuple[str, ...]
    contextual_label_status: str
    contextual_technique_ids: Tuple[str, ...]
    contextual_technique_names: Tuple[str, ...]
    contextual_evidence_predicates: Dict[str, List[str]]  # technique_id -> [predicate descriptions]
    contextual_rationale: str
    single_label_status: str
    single_technique_ids: Tuple[str, ...]
    single_technique_names: Tuple[str, ...]
    single_evidence_predicates: Dict[str, List[str]]
    single_rationale: str
    counter_evidence: str
    benign_near_miss_criteria: str
    ambiguous_criteria: str
    allowed_variations: Tuple[str, ...]
    disallowed_variations: Tuple[str, ...]
    planned_instances: int
    expected_label_transition: str  # e.g., 'mapped -> mapped', 'ambiguous -> mapped'
    category: str  # 'mapped_single', 'mapped_multi', 'unmapped', 'ambiguous'

# ==============================================================================
# 2. ID Generation Functions
# ==============================================================================

def generate_deterministic_id(prefix: str, seed: int, *components: str) -> str:
    """Generate deterministic ID: prefix + '_' + SHA256(seed || components)[:8]"""
    payload = f"{seed}|{'|'.join(components)}".encode('utf-8')
    hash_val = hashlib.sha256(payload).hexdigest()[:8]
    return f"{prefix}_{hash_val}"

# ==============================================================================
# 3. Safe Indicator Pools
# ==============================================================================

SAFE_IPS = [
    '192.0.2.10', '192.0.2.20', '192.0.2.30', '192.0.2.40', '192.0.2.50',
    '198.51.100.10', '198.51.100.20', '198.51.100.30', '198.51.100.40',
    '203.0.113.10', '203.0.113.20', '203.0.113.30', '203.0.113.40', '203.0.113.50'
]
SAFE_DOMAINS = [
    'mail.example.invalid', 'update.example.invalid', 'auth.example.invalid',
    'admin.example.invalid', 'files.example.invalid', 'web.example.invalid'
]
SAFE_HOSTS = [
    'WORKSTATION01', 'WORKSTATION02', 'DC01', 'FILESVR01', 'APPSVR01',
    'DB01', 'EXCH01', 'WEB01'
]
SAFE_USERS = [
    'jsmith', 'agarcia', 'mchen', 'admin.svc', 'system', 'network.service',
    'local.service', 'tjones', 'wlee'
]

# Host-role constraints for T1136.001 (Local Account)
# Local account creation must NOT be generated on domain controllers
HOSTS_WORKSTATION = ['WORKSTATION01', 'WORKSTATION02']
HOSTS_MEMBER_SERVER = ['FILESVR01', 'APPSVR01', 'DB01', 'EXCH01', 'WEB01']
HOSTS_DOMAIN_CONTROLLER = ['DC01']
HOSTS_ALLOWED_LOCAL_ACCOUNT = HOSTS_WORKSTATION + HOSTS_MEMBER_SERVER

# ==============================================================================
# 4. Event Builder Functions
# ==============================================================================

def build_security_4688(timestamp_utc: str, computer: str, new_process: str,
                        command_line: str, parent_process: str,
                        subject_user: str, target_user: str,
                        new_process_id: str, creator_process_id: str,
                        logon_id: str, **kwargs) -> Dict[str, Any]:
    """Build Windows Security Event 4688 - Process Creation."""
    fields = {
        'TimeCreated': timestamp_utc,
        'Computer': computer,
        'EventID': 4688,
        'NewProcessName': new_process,
        'CommandLine': command_line,
        'ParentProcessName': parent_process,
        'SubjectUserName': subject_user,
        'TargetUserName': target_user,
        'NewProcessId': new_process_id,
        'ProcessId': creator_process_id,
        'SubjectLogonId': logon_id,
    }
    fields.update(kwargs)
    return fields

def build_security_4698(timestamp_utc: str, computer: str, task_name: str,
                        task_content: str, subject_user: str,
                        logon_id: str, **kwargs) -> Dict[str, Any]:
    """Build Windows Security Event 4698 - Scheduled Task Created."""
    fields = {
        'TimeCreated': timestamp_utc,
        'Computer': computer,
        'EventID': 4698,
        'TaskName': task_name,
        'TaskContent': task_content,
        'SubjectUserName': subject_user,
        'SubjectLogonId': logon_id,
    }
    fields.update(kwargs)
    return fields

def build_security_4697(timestamp_utc: str, computer: str, service_name: str,
                        service_file_name: str, service_type: str,
                        service_start_type: str, service_account: str,
                        subject_user: str, subject_domain: str,
                        logon_id: str, **kwargs) -> Dict[str, Any]:
    """Build Windows Security Event 4697 - A service was installed in the system.

    This is the Security-auditing event for service installation.
    NOT EID 7045, which belongs to Service Control Manager / System channel.
    """
    fields = {
        'TimeCreated': timestamp_utc,
        'Computer': computer,
        'EventID': 4697,
        'ServiceName': service_name,
        'ServiceFileName': service_file_name,
        'ServiceType': service_type,
        'ServiceStartType': service_start_type,
        'ServiceAccount': service_account,
        'SubjectUserName': subject_user,
        'SubjectDomainName': subject_domain,
        'SubjectLogonId': logon_id,
    }
    fields.update(kwargs)
    return fields

def build_security_4720(timestamp_utc: str, computer: str, target_user: str,
                        subject_user: str, logon_id: str, **kwargs) -> Dict[str, Any]:
    """Build Windows Security Event 4720 - User Account Created."""
    fields = {
        'TimeCreated': timestamp_utc,
        'Computer': computer,
        'EventID': 4720,
        'TargetUserName': target_user,
        'SubjectUserName': subject_user,
        'SubjectLogonId': logon_id,
    }
    fields.update(kwargs)
    return fields

def build_security_1102(timestamp_utc: str, computer: str,
                         subject_user: str, logon_id: str, **kwargs) -> Dict[str, Any]:
    """Build Windows Security Event 1102 - Audit Log Cleared."""
    fields = {
        'TimeCreated': timestamp_utc,
        'Computer': computer,
        'EventID': 1102,
        'SubjectUserName': subject_user,
        'SubjectLogonId': logon_id,
    }
    fields.update(kwargs)
    return fields

def build_sysmon_1(timestamp_utc: str, computer: str, image: str,
                   command_line: str, parent_image: str,
                   parent_command_line: str, user: str,
                   process_id: int, parent_process_id: int,
                   process_guid: str, parent_process_guid: str,
                   logon_guid: str, logon_id: str,
                   hashes: str, **kwargs) -> Dict[str, Any]:
    """Build Sysmon Event 1 - Process Create."""
    fields = {
        'UtcTime': timestamp_utc,
        'Computer': computer,
        'EventID': 1,
        'Image': image,
        'CommandLine': command_line,
        'ParentImage': parent_image,
        'ParentCommandLine': parent_command_line,
        'User': user,
        'ProcessId': process_id,
        'ParentProcessId': parent_process_id,
        'ProcessGuid': process_guid,
        'ParentProcessGuid': parent_process_guid,
        'LogonGuid': logon_guid,
        'LogonId': logon_id,
        'Hashes': hashes,
    }
    fields.update(kwargs)
    return fields

def build_sysmon_3(timestamp_utc: str, computer: str, image: str,
                   user: str, source_ip: str, source_port: int,
                   destination_ip: str, destination_port: int,
                   protocol: str, process_id: int,
                   process_guid: str, **kwargs) -> Dict[str, Any]:
    """Build Sysmon Event 3 - Network Connection."""
    fields = {
        'UtcTime': timestamp_utc,
        'Computer': computer,
        'EventID': 3,
        'Image': image,
        'User': user,
        'SourceIp': source_ip,
        'SourcePort': source_port,
        'DestinationIp': destination_ip,
        'DestinationPort': destination_port,
        'Protocol': protocol,
        'ProcessId': process_id,
        'ProcessGuid': process_guid,
    }
    fields.update(kwargs)
    return fields

def build_sysmon_11(timestamp_utc: str, computer: str, image: str,
                    target_filename: str, process_id: int,
                    process_guid: str, user: str, **kwargs) -> Dict[str, Any]:
    """Build Sysmon Event 11 - File Create."""
    fields = {
        'UtcTime': timestamp_utc,
        'Computer': computer,
        'EventID': 11,
        'Image': image,
        'TargetFilename': target_filename,
        'ProcessId': process_id,
        'ProcessGuid': process_guid,
        'User': user,
    }
    fields.update(kwargs)
    return fields

def build_sysmon_13(timestamp_utc: str, computer: str, image: str,
                    event_type: str, target_object: str, details: str,
                    process_id: int, process_guid: str,
                    user: str, **kwargs) -> Dict[str, Any]:
    """Build Sysmon Event 13 - Registry Value Set."""
    fields = {
        'UtcTime': timestamp_utc,
        'Computer': computer,
        'EventID': 13,
        'Image': image,
        'EventType': event_type,
        'TargetObject': target_object,
        'Details': details,
        'ProcessId': process_id,
        'ProcessGuid': process_guid,
        'User': user,
    }
    fields.update(kwargs)
    return fields


# ==============================================================================
# 5. Inference Accessor
# ==============================================================================

# Allowlisted fields for inference - NO leakage
INFERENCE_ALLOWLIST = {
    'Security': {
        1102: ['TimeCreated', 'Computer', 'EventID', 'SubjectUserName', 'SubjectLogonId'],
        4688: ['TimeCreated', 'Computer', 'EventID', 'NewProcessName', 'CommandLine',
               'ParentProcessName', 'SubjectUserName', 'TargetUserName', 'NewProcessId',
               'ProcessId', 'SubjectLogonId'],
        4698: ['TimeCreated', 'Computer', 'EventID', 'TaskName', 'TaskContent',
               'SubjectUserName', 'SubjectLogonId'],
        4720: ['TimeCreated', 'Computer', 'EventID', 'TargetUserName', 'SubjectUserName', 'SubjectLogonId'],
        4697: ['TimeCreated', 'Computer', 'EventID', 'ServiceName', 'ServiceFileName',
               'ServiceType', 'ServiceStartType', 'ServiceAccount', 'SubjectUserName',
               'SubjectDomainName', 'SubjectLogonId'],
    },
    'Sysmon': {
        1: ['UtcTime', 'Computer', 'EventID', 'Image', 'CommandLine', 'ParentImage',
            'ParentCommandLine', 'User', 'ProcessId', 'ParentProcessId',
            'ProcessGuid', 'ParentProcessGuid', 'LogonGuid', 'LogonId', 'Hashes'],
        3: ['UtcTime', 'Computer', 'EventID', 'Image', 'User', 'SourceIp',
            'SourcePort', 'DestinationIp', 'DestinationPort', 'Protocol',
            'ProcessId', 'ProcessGuid'],
        11: ['UtcTime', 'Computer', 'EventID', 'Image', 'TargetFilename', 'ProcessId', 'ProcessGuid', 'User'],
        13: ['UtcTime', 'Computer', 'EventID', 'Image', 'EventType', 'TargetObject', 'Details', 'ProcessId', 'ProcessGuid', 'User'],
    }
}

def get_inference_payload(event: SyntheticEvent) -> Dict[str, Any]:
    """Return only allowlisted fields for model inference. No leakage."""
    event_id_val = event.windows_event_id
    channel_key = 'Security' if 'Security' in event.channel else 'Sysmon'
    allowlist = INFERENCE_ALLOWLIST.get(channel_key, {}).get(event_id_val, [])
    
    payload = {}
    for field in allowlist:
        if field in event.fields:
            payload[field] = event.fields[field]
    return payload

def check_leakage(payload: Dict[str, Any]) -> List[str]:
    """Check for obvious label leakage patterns in inference payload."""
    leaks = []
    payload_str = json.dumps(payload).lower()
    
    # Check for T####, T####.###
    if re.search(r't\d{4}(\.\d{3})?', payload_str):
        leaks.append("Potential ATT&CK technique ID (T####) found.")
        
    if "ground_truth" in payload_str or "expected_technique" in payload_str or "rationale" in payload_str:
        leaks.append("Potential ground truth keywords found.")
        
    return leaks


# ==============================================================================
# 6. Near-Duplicate Detection
# ==============================================================================

def character_ngrams(text: str, n: int = 5) -> Set[str]:
    """Extract character n-grams from text."""
    if len(text) < n:
        return {text}
    return {text[i:i+n] for i in range(len(text) - n + 1)}

def jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 1.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union > 0 else 0.0

def normalize_for_dedup(event: SyntheticEvent) -> str:
    """Normalize event by removing decorative fields (PID, timestamp, hostname)."""
    fields_copy = dict(event.fields)
    decorative_keys = {'TimeCreated', 'UtcTime', 'Computer', 'ProcessId', 'NewProcessId', 'ParentProcessId',
                       'ProcessGuid', 'ParentProcessGuid', 'LogonGuid', 'LogonId'}
    
    for key in decorative_keys:
        fields_copy.pop(key, None)
        
    return json.dumps(fields_copy, sort_keys=True)

def find_near_duplicates(pairs: List[ScenarioPair], threshold: float = 0.95) -> List[Tuple[str, str, float]]:
    """Find near-duplicate scenario pairs using 5-gram Jaccard."""
    pair_signatures = {}
    for pair in pairs:
        events_str = " ".join(normalize_for_dedup(e) for e in pair.events.values())
        pair_signatures[pair.pair_id] = character_ngrams(events_str)
        
    duplicates = []
    pair_ids = list(pair_signatures.keys())
    for i in range(len(pair_ids)):
        for j in range(i + 1, len(pair_ids)):
            id_a, id_b = pair_ids[i], pair_ids[j]
            sim = jaccard_similarity(pair_signatures[id_a], pair_signatures[id_b])
            if sim >= threshold:
                duplicates.append((id_a, id_b, sim))
                
    return duplicates


# ==============================================================================
# 7. Deterministic Split Assignment
# ==============================================================================

def compute_split_key(seed: int, group_id: str, scenario_id: str) -> str:
    """SHA-256(seed || group_id || scenario_id) for deterministic ranking."""
    payload = f"{seed}|{group_id}|{scenario_id}".encode('utf-8')
    return hashlib.sha256(payload).hexdigest()

def assign_splits(pairs: List[ScenarioPair], seed: int,
                  dev_quota: Dict[str, int],
                  test_quota: Dict[str, int]) -> Tuple[List[ScenarioPair], List[ScenarioPair]]:
    """Deterministically assign pairs to dev/test splits.
    Groups stay together. Returns (dev_pairs, test_pairs)."""
    groups: Dict[str, List[ScenarioPair]] = {}
    for pair in pairs:
        groups.setdefault(pair.template_family_id, []).append(pair)
        
    dev_pairs = []
    test_pairs = []
    
    sorted_group_ids = sorted(groups.keys(), key=lambda g: compute_split_key(seed, g, ""))
    
    dev_counts: Dict[str, int] = {k: 0 for k in dev_quota}
    test_counts: Dict[str, int] = {k: 0 for k in test_quota}
    
    for group_id in sorted_group_ids:
        group_pairs = groups[group_id]
        category = group_pairs[0].template_family_id # using family id as category here
        
        group_pairs.sort(key=lambda p: compute_split_key(seed, group_id, p.scenario_id))
        
        assigned_dev = False
        if dev_counts.get(category, 0) < dev_quota.get(category, float('inf')):
            assigned_dev = True
            
        for pair in group_pairs:
            new_pair = ScenarioPair(
                pair_id=pair.pair_id,
                scenario_id=pair.scenario_id,
                template_family_id=pair.template_family_id,
                split='dev' if assigned_dev else 'test',
                single_view=pair.single_view,
                contextual_view=pair.contextual_view,
                events=pair.events,
                single_ground_truth=pair.single_ground_truth,
                contextual_ground_truth=pair.contextual_ground_truth,
                generation_seed=pair.generation_seed,
                generation_provenance=pair.generation_provenance
            )
            if assigned_dev:
                dev_pairs.append(new_pair)
                dev_counts[category] = dev_counts.get(category, 0) + 1
            else:
                test_pairs.append(new_pair)
                test_counts[category] = test_counts.get(category, 0) + 1
                
    return dev_pairs, test_pairs


# ==============================================================================
# 8. Serialization
# ==============================================================================

def _default_serializer(obj: Any) -> Any:
    if hasattr(obj, '__dataclass_fields__'):
        return asdict(obj)
    if isinstance(obj, set):
        return list(obj)
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def _sha256_file(path: Path) -> str:
    hash_sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def serialize_dataset(pairs: List[ScenarioPair], output_dir: Path) -> Dict[str, str]:
    """Serialize complete dataset to output_dir. Returns file->sha256 manifest."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    events_path = output_dir / "events.jsonl"
    views_path = output_dir / "views.jsonl"
    pairs_path = output_dir / "pairs.jsonl"
    gt_path = output_dir / "ground_truth.jsonl"
    split_manifest_path = output_dir / "split_manifest.json"
    dataset_manifest_path = output_dir / "dataset_manifest.json"
    
    all_events = {}
    all_views = {}
    all_gt = {}
    splits = {'dev': [], 'test': []}
    
    with open(pairs_path, 'w', encoding='utf-8') as f_pairs:
        for pair in pairs:
            for ev_id, ev in pair.events.items():
                if ev_id not in all_events:
                    all_events[ev_id] = ev
                    
            all_views[pair.single_view.view_id] = pair.single_view
            all_views[pair.contextual_view.view_id] = pair.contextual_view
            
            all_gt[pair.single_ground_truth.view_id] = pair.single_ground_truth
            all_gt[pair.contextual_ground_truth.view_id] = pair.contextual_ground_truth
            
            splits[pair.split].append(pair.pair_id)
            
            pair_dict = asdict(pair)
            f_pairs.write(json.dumps(pair_dict, default=_default_serializer) + "\n")
            
    with open(events_path, 'w', encoding='utf-8') as f:
        for ev in all_events.values():
            f.write(json.dumps(asdict(ev), default=_default_serializer) + "\n")
            
    with open(views_path, 'w', encoding='utf-8') as f:
        for v in all_views.values():
            f.write(json.dumps(asdict(v), default=_default_serializer) + "\n")
            
    with open(gt_path, 'w', encoding='utf-8') as f:
        for gt in all_gt.values():
            f.write(json.dumps(asdict(gt), default=_default_serializer) + "\n")
            
    with open(split_manifest_path, 'w', encoding='utf-8') as f:
        json.dump(splits, f, indent=2)
        
    manifest = {
        "events.jsonl": _sha256_file(events_path),
        "views.jsonl": _sha256_file(views_path),
        "pairs.jsonl": _sha256_file(pairs_path),
        "ground_truth.jsonl": _sha256_file(gt_path),
        "split_manifest.json": _sha256_file(split_manifest_path)
    }
    
    with open(dataset_manifest_path, 'w', encoding='utf-8') as f:
        json.dump({
            "schema_version": "1.0.0",
            "files": manifest
        }, f, indent=2)
        
    return manifest

def load_dataset(input_dir: Path) -> List[ScenarioPair]:
    """Load serialized dataset."""
    pairs_path = input_dir / "pairs.jsonl"
    pairs = []
    
    if pairs_path.exists():
        with open(pairs_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                
                events = {
                    k: SyntheticEvent(**v) for k, v in data['events'].items()
                }
                
                sv_data = data['single_view']
                sv_data['event_ids'] = tuple(sv_data['event_ids'])
                single_view = View(**sv_data)
                
                cv_data = data['contextual_view']
                cv_data['event_ids'] = tuple(cv_data['event_ids'])
                contextual_view = View(**cv_data)
                
                sgt_data = data['single_ground_truth']
                sgt_data['technique_ids'] = tuple(sgt_data['technique_ids'])
                sgt_data['technique_names'] = tuple(sgt_data['technique_names'])
                single_ground_truth = ViewGroundTruth(**sgt_data)
                
                cgt_data = data['contextual_ground_truth']
                cgt_data['technique_ids'] = tuple(cgt_data['technique_ids'])
                cgt_data['technique_names'] = tuple(cgt_data['technique_names'])
                contextual_ground_truth = ViewGroundTruth(**cgt_data)
                
                pair = ScenarioPair(
                    pair_id=data['pair_id'],
                    scenario_id=data['scenario_id'],
                    template_family_id=data['template_family_id'],
                    split=data['split'],
                    single_view=single_view,
                    contextual_view=contextual_view,
                    events=events,
                    single_ground_truth=single_ground_truth,
                    contextual_ground_truth=contextual_ground_truth,
                    generation_seed=data['generation_seed'],
                    generation_provenance=data['generation_provenance']
                )
                pairs.append(pair)
                
    return pairs
