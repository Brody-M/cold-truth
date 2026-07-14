from __future__ import annotations
import argparse, copy, hashlib, json, os, tempfile, unittest
from contextlib import contextmanager
from pathlib import Path
from c3_fixture_chain import APPROVED, EXCLUDED, SECTIONS, SENTENCES, C3FixtureError, normalize_writer, normalize_editor, redundancy_findings, simulated_checkpoint, validate_fixture_paths
from handoff_validator import file_sha256, load_contract, validate_handoff
from json_schema_subset import SchemaSubsetError, validate as validate_schema, validate_schema_compatibility
from providers.writer_editor_codex_provider import WriterCodexProvider, EditorCodexProvider
from agent_runner import AgentRunBlocked, AgentRunner
from agent_runtime import ProviderRegistry
from run_records import atomic_json

AUTOMATION=Path(__file__).resolve().parent; WORKSPACE=AUTOMATION/"fixtures"/"real_writer_editor_fixture_workspace"; CONTRACTS=WORKSPACE/"contracts"
WRITER_REMOTE=WORKSPACE/"writer_remote.schema.json"; WRITER_CANON=WORKSPACE/"writer_canonical.schema.json"; EDITOR_REMOTE=WORKSPACE/"editor_remote.schema.json"; EDITOR_CANON=WORKSPACE/"editor_canonical.schema.json"
VERIFIED=WORKSPACE/"synthetic_research_verifier_handoff.json"; BRIEF=WORKSPACE/"synthetic_case_brief.json"; WB=WORKSPACE/"synthetic_writer_boundaries.json"; EB=WORKSPACE/"synthetic_editor_boundaries.json"
NODE=Path(r"C:\Program Files\nodejs\node.exe"); NPM=Path(r"C:\Users\brody\AppData\Roaming\npm"); ENTRY=NPM/"node_modules"/"@openai"/"codex"/"bin"/"codex.js"; COMMAND_ENV="COLD_TRUTH_CODEX_RUNTIME_COMMAND"

@contextmanager
def runtime_command():
    if COMMAND_ENV in os.environ: raise RuntimeError(f"{COMMAND_ENV} must be absent; its value was not read")
    os.environ[COMMAND_ENV]=json.dumps([str(NPM/"codex.cmd"),"exec"])
    try: yield
    finally: os.environ.pop(COMMAND_ENV,None)

def writer_provider(): return WriterCodexProvider(WORKSPACE,WRITER_REMOTE,WRITER_CANON,WORKSPACE/"writer_prompt_template.txt",NODE,NPM,ENTRY,WORKSPACE/"output"/"c3_writer_tmp",timeout_seconds=120)
def editor_provider(): return EditorCodexProvider(WORKSPACE,EDITOR_REMOTE,EDITOR_CANON,WORKSPACE/"editor_prompt_template.txt",NODE,NPM,ENTRY,WORKSPACE/"output"/"c3_editor_tmp",timeout_seconds=120)

def descriptors(values):
    return [{"name":n,"type":t,"kind":"file","path":str(p.resolve()),"sha256":file_sha256(p),"size_bytes":p.stat().st_size} for n,(t,p) in sorted(values.items())]
def request(contract,run,stage,inputs,out):
    c=load_contract(CONTRACTS/contract); return {"schema_version":"1.0","run_id":run,"case_id":"glass-river-writing-fixture","stage":stage,"contract_id":c["contract_id"],"contract_version":c["contract_version"],"inputs":descriptors(inputs),"permissions":{"allowed_actions":c["allowed_actions"],"network":False,"external_commands":False,"external_tools":False,"media_creation":False,"publishing":False,"platform_api":False,"secrets":False},"mode":"controlled-real-fixture","provider_id":"c3-fixture-fake","failure_mode":None,"reset_token":"","idempotency_key":"0"*64,"output_root":str(out.resolve()),"execution_origin":"orchestrated_agent"}
def envelope(contract_id,version,run,stage,inputs,result):
    return {"schema_version":"1.0","contract_id":contract_id,"contract_version":version,"run_id":run,"case_id":"glass-river-writing-fixture","stage":stage,"attempt":1,"idempotency_key":"0"*64,"status":"success","started_at":"2026-07-12T00:00:00Z","completed_at":"2026-07-12T00:00:00Z","inputs":inputs,"outputs":[],"result":result,"decisions":[{"rule":"synthetic_writer_only" if "writer" in stage else "simulated_human_checkpoint","result":"pass" if "writer" in stage else "required"}],"warnings":[],"errors":[],"retryable":False,"tool_calls":[],"runtime":{"provider":"codex-exec","runtime":"controlled-real-fixture","model":"not-reported","version":"not-reported"},"publishing_enabled":False,"real_production_enabled":False}
def writer_remote(out):
    req=request("writer.contract.json","phase-c3-writer-fixture","writer_fixture",{"synthetic_research_verifier_handoff":("verified_fixture_handoff",VERIFIED),"synthetic_case_brief":("synthetic_case_brief",BRIEF),"synthetic_writer_boundaries":("synthetic_writer_boundaries",WB)},out); h={i["name"]:i["sha256"] for i in req["inputs"]}
    r={"upstream_research_verifier_handoff_hash":h["synthetic_research_verifier_handoff"],"narration_text":" ".join(SENTENCES),"word_count":38,"unsupported_claim_check":"passed","external_research_used":False,"browser_used":False,"mcp_used":False,"network_used":False,"artifact_hashes":{},"ready_for_editor":True}
    for i in range(1,4): r[f"approved_claim_{i}"]=APPROVED[i-1]; r[f"excluded_claim_{i}"]=EXCLUDED[i-1]; r[f"section_{i}"]=SECTIONS[i-1]; r[f"sentence_{i}"]=SENTENCES[i-1]; r[f"attribution_{i}"]=APPROVED[i-1]
    return req,envelope("cold-truth.writer","1.0.0-c3-fixture","phase-c3-writer-fixture","writer_fixture",req["inputs"],r)
def editor_remote(writer_path,out):
    req=request("editor.contract.json","phase-c3-editor-fixture","editor_fixture",{"synthetic_writer_handoff":("writer_fixture_handoff",writer_path),"synthetic_editor_boundaries":("synthetic_editor_boundaries",EB)},out); h={i["name"]:i["sha256"] for i in req["inputs"]}
    r={"upstream_writer_handoff_hash":h["synthetic_writer_handoff"],"factual_attribution_check":"passed","unsupported_material_check":"passed","redundancy_check":"passed","redundancy_findings":[],"narrative_coherence_check":"passed","editor_decision":"ready_for_human_script_review","simulated_human_checkpoint_required":True,"handoff_to_human_review":True,"later_stage_requested":False,"artifact_hashes":{},"external_research_used":False,"browser_used":False,"mcp_used":False,"network_used":False}
    for i in range(1,4): r[f"approved_seen_{i}"]=APPROVED[i-1]; r[f"excluded_absent_{i}"]=EXCLUDED[i-1]
    return req,envelope("cold-truth.editor","1.0.0-c3-fixture","phase-c3-editor-fixture","editor_fixture",req["inputs"],r)

class C3Tests(unittest.TestCase):
    def test_fixture_provider_adapters_validate_without_launch(self):
        node=Path(r"C:\Program Files\nodejs\node.exe"); npm=Path(r"C:\Users\brody\AppData\Roaming\npm"); entry=npm/"node_modules"/"@openai"/"codex"/"bin"/"codex.js"
        out=WORKSPACE/"output"/"provider-construction"
        wreq,_=writer_remote(out); w=WriterCodexProvider(WORKSPACE,WRITER_REMOTE,WRITER_CANON,WORKSPACE/"writer_prompt_template.txt",node,npm,entry,WORKSPACE/"output"/"c3_writer_tmp",process_runner=lambda *a,**k:None); w.validate_request(wreq,out); self.assertIn("SYN-RV-01",w.build_prompt(wreq))
        with tempfile.TemporaryDirectory(dir=WORKSPACE/"output") as td:
            wp=Path(td)/"writer.json"; wp.write_text(json.dumps({"case_id":"glass-river-writing-fixture"})); ereq,_=editor_remote(wp,out); e=EditorCodexProvider(WORKSPACE,EDITOR_REMOTE,EDITOR_CANON,WORKSPACE/"editor_prompt_template.txt",node,npm,entry,WORKSPACE/"output"/"c3_editor_tmp",process_runner=lambda *a,**k:None); e.validate_request(ereq,out); self.assertIn("human script review",e.build_prompt(ereq).lower())
    def test_remote_schemas_compatible(self): validate_schema_compatibility(json.loads(WRITER_REMOTE.read_text())); validate_schema_compatibility(json.loads(EDITOR_REMOTE.read_text()))
    def test_valid_chain_stops_at_checkpoint(self):
        with tempfile.TemporaryDirectory(dir=WORKSPACE/"output") as td:
            out=Path(td); wreq,wremote=writer_remote(out); validate_schema(wremote,json.loads(WRITER_REMOTE.read_text())); w=normalize_writer(wremote,wreq); validate_schema(w,json.loads(WRITER_CANON.read_text())); validate_handoff(w,load_contract(CONTRACTS/"writer.contract.json"),wreq,out); wp=out/"writer.json"; wp.write_text(json.dumps(w))
            ereq,eremote=editor_remote(wp,out); validate_schema(eremote,json.loads(EDITOR_REMOTE.read_text())); e=normalize_editor(eremote,ereq); validate_schema(e,json.loads(EDITOR_CANON.read_text())); validate_handoff(e,load_contract(CONTRACTS/"editor.contract.json"),ereq,out); self.assertEqual(simulated_checkpoint(w,e)["state"],"AWAITING_SCRIPT_APPROVAL")
    def test_writer_boundaries_block(self):
        out=WORKSPACE/"output"/"negative"; req,base=writer_remote(out)
        changes=[("approved_claim_1","SYN-RV-X1"),("sentence_1","Invented unsupported fact."),("attribution_1",""),("external_research_used",True),("browser_used",True),("mcp_used",True),("network_used",True),("ready_for_editor",False)]
        for field,value in changes:
            bad=copy.deepcopy(base); bad["result"][field]=value
            with self.subTest(field=field),self.assertRaises((C3FixtureError,SchemaSubsetError)): validate_schema(bad,json.loads(WRITER_REMOTE.read_text())); normalize_writer(bad,req)
        for top in ("publishing_enabled","real_production_enabled"):
            bad=copy.deepcopy(base); bad[top]=True
            with self.assertRaises(SchemaSubsetError): validate_schema(bad,json.loads(WRITER_REMOTE.read_text()))
        bad=copy.deepcopy(base); bad["tool_calls"]=[{}]; w=normalize_writer(bad,req)
        with self.assertRaises(SchemaSubsetError): validate_schema(w,json.loads(WRITER_CANON.read_text()))
    def test_editor_and_redundancy_blocks(self):
        with tempfile.TemporaryDirectory(dir=WORKSPACE/"output") as td:
            out=Path(td); wreq,wr=writer_remote(out); w=normalize_writer(wr,wreq); wp=out/"writer.json"; wp.write_text(json.dumps(w)); req,base=editor_remote(wp,out)
            for field,value in (("approved_seen_1","SYN-RV-X1"),("excluded_absent_3","SYN-RV-03"),("unsupported_material_check","failed"),("redundancy_check","failed"),("later_stage_requested",True),("handoff_to_human_review",False)):
                bad=copy.deepcopy(base); bad["result"][field]=value
                with self.subTest(field=field),self.assertRaises((C3FixtureError,SchemaSubsetError)): validate_schema(bad,json.loads(EDITOR_REMOTE.read_text())); normalize_editor(bad,req)
            duplicate=copy.deepcopy(w); duplicate["result"]["script_sections"][1]["sentence"]=duplicate["result"]["script_sections"][0]["sentence"]; self.assertTrue(redundancy_findings(duplicate))
    def test_path_escape_blocks(self):
        out=WORKSPACE/"output"/"path"; req,_=writer_remote(out); req["inputs"][0]["path"]=str((WORKSPACE.parent/"outside.json").resolve())
        with self.assertRaises(C3FixtureError): validate_fixture_paths(req,WORKSPACE)

def run_real_chain_once():
    root=WORKSPACE/"output"/"c3_real_writer_editor_chain"; marker=root/"CHAIN_ATTEMPT.json"
    if marker.exists(): return {"status":"BLOCKED_ALREADY_ATTEMPTED","marker":str(marker)}
    root.mkdir(parents=True,exist_ok=True); atomic_json(marker,{"status":"STARTED","fixture_only":True,"real_production_enabled":False,"publishing_enabled":False,"editor_invoked":False})
    summary={"status":"BLOCKED","fixture_only":True,"real_production_enabled":False,"publishing_enabled":False,"editor_invoked":False}
    try:
        with runtime_command():
            wr=ProviderRegistry(); wr.register(writer_provider(),["cold-truth.writer"]); writer=AgentRunner(CONTRACTS,root/"writer",wr,mode="controlled-real-fixture").run("cold-truth.writer",run_id="phase-c3-writer-fixture",case_id="glass-river-writing-fixture",stage="writer_fixture",inputs={"synthetic_research_verifier_handoff":VERIFIED,"synthetic_case_brief":BRIEF,"synthetic_writer_boundaries":WB},max_retries=0)
            if writer.handoff["result"]["word_count"]!=38: raise RuntimeError("Writer word count mismatch")
            er=ProviderRegistry(); er.register(editor_provider(),["cold-truth.editor"]); summary["editor_invoked"]=True; editor=AgentRunner(CONTRACTS,root/"editor",er,mode="controlled-real-fixture").run("cold-truth.editor",run_id="phase-c3-editor-fixture",case_id="glass-river-writing-fixture",stage="editor_fixture",inputs={"synthetic_writer_handoff":writer.handoff_path,"synthetic_editor_boundaries":EB},max_retries=0)
            state=simulated_checkpoint(writer.handoff,editor.handoff); atomic_json(root/"chain_state.json",state)
            summary={"status":"PASSED","fixture_only":True,"editor_invoked":True,"writer_record":str(writer.record_path),"editor_record":str(editor.record_path),"writer_handoff":str(writer.handoff_path),"editor_handoff":str(editor.handoff_path),"final_state":state["state"],"real_production_enabled":False,"publishing_enabled":False}
    except (AgentRunBlocked,C3FixtureError,OSError,RuntimeError) as exc: summary["blocker"]=f"{type(exc).__name__}: {exc}"
    atomic_json(marker,summary); return summary

if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--run-real",action="store_true"); args=parser.parse_args()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(C3Tests))
    if not result.wasSuccessful(): print(json.dumps({"c3_offline_tests":"failed","real_invocation":"not_requested"},indent=2)); raise SystemExit(1)
    if not args.run_real: print(json.dumps({"c3_offline_tests":"passed","real_invocation":"not_requested"},indent=2)); raise SystemExit(0)
    real=run_real_chain_once(); print(json.dumps({"c3_offline_tests":"passed","real_invocation":real},indent=2)); raise SystemExit(0 if real["status"]=="PASSED" else 2)
