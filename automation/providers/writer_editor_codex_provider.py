"""Fixture-only Writer and Editor adapters built on the proven direct-Node provider."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from c3_fixture_chain import normalize_writer, normalize_editor
from providers.codex_exec_provider import CodexExecProvider, CodexProviderConfigurationError

def _under(root:Path,path:Path)->bool:
    try:path.resolve().relative_to(root.resolve());return True
    except ValueError:return False

class _C3Provider(CodexExecProvider):
    case_id="glass-river-writing-fixture"
    input_names:set[str]=set(); allowed_actions:set[str]=set(); replacements:dict[str,str]={}
    def validate_request(self,request:dict[str,Any],output_root:Path)->None:
        if request.get("mode")!="controlled-real-fixture" or request.get("case_id")!=self.case_id: raise CodexProviderConfigurationError("C3 fixture identity mismatch")
        if request.get("contract_id")!=self.contract_id or request.get("contract_version")!="1.0.0-c3-fixture" or request.get("stage")!=self.stage: raise CodexProviderConfigurationError("C3 fixture contract mismatch")
        if not _under(self.fixture_root,output_root): raise CodexProviderConfigurationError("C3 output escapes fixture")
        permissions=request.get("permissions",{})
        for flag in ("network","external_commands","external_tools","media_creation","publishing","platform_api","secrets"):
            if permissions.get(flag)is not False: raise CodexProviderConfigurationError(f"C3 permission prohibited: {flag}")
        if set(permissions.get("allowed_actions",[]))!=self.allowed_actions: raise CodexProviderConfigurationError("C3 action allowlist mismatch")
        if {item.get("name") for item in request.get("inputs",[])}!=self.input_names: raise CodexProviderConfigurationError("C3 input set mismatch")
        for item in request["inputs"]:
            path=Path(item.get("path",""))
            if item.get("kind")!="file" or not path.is_file() or not _under(self.fixture_root,path): raise CodexProviderConfigurationError("C3 input escapes fixture")
    def build_prompt(self,request:dict[str,Any])->str:
        docs={item["name"]:json.loads(Path(item["path"]).read_text(encoding="utf-8")) for item in request["inputs"]}
        prompt=self.prompt_template.read_text(encoding="utf-8")
        identity={k:request[k] for k in ("schema_version","contract_id","contract_version","run_id","case_id","stage","idempotency_key")}
        prompt=prompt.replace("{{REQUEST_IDENTITY_JSON}}",json.dumps(identity,sort_keys=True)).replace("{{REQUEST_INPUTS_JSON}}",json.dumps(request["inputs"],sort_keys=True))
        for token,name in self.replacements.items():prompt=prompt.replace(token,json.dumps(docs[name],sort_keys=True))
        return prompt

class WriterCodexProvider(_C3Provider):
    provider_id="codex-exec-controlled-writer-fixture-v1"; normalization_kind="fixture_writer_scalars_to_canonical_script"; contract_id="cold-truth.writer"; stage="writer_fixture"
    input_names={"synthetic_research_verifier_handoff","synthetic_case_brief","synthetic_writer_boundaries"}
    allowed_actions={"compose supplied synthetic claims","attach supplied claim attribution","enforce supplied synthetic exclusions"}
    replacements={"{{VERIFIED_HANDOFF_JSON}}":"synthetic_research_verifier_handoff","{{CASE_BRIEF_JSON}}":"synthetic_case_brief","{{WRITER_BOUNDARIES_JSON}}":"synthetic_writer_boundaries"}
    def normalize_remote_handoff(self,remote_handoff,request):return normalize_writer(remote_handoff,request)

class EditorCodexProvider(_C3Provider):
    provider_id="codex-exec-controlled-editor-fixture-v1"; normalization_kind="fixture_editor_scalars_to_canonical_review"; contract_id="cold-truth.editor"; stage="editor_fixture"
    input_names={"synthetic_writer_handoff","synthetic_editor_boundaries"}
    allowed_actions={"verify supplied sentence attribution","enforce supplied exclusions","apply deterministic redundancy checks","return simulated human checkpoint decision"}
    replacements={"{{WRITER_HANDOFF_JSON}}":"synthetic_writer_handoff","{{EDITOR_BOUNDARIES_JSON}}":"synthetic_editor_boundaries"}
    def normalize_remote_handoff(self,remote_handoff,request):return normalize_editor(remote_handoff,request)
