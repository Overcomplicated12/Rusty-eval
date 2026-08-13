"""Reproducible, conservative Mako Raft DSL/safety summary."""
from __future__ import annotations

import argparse, csv, hashlib, json, re, subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

SUFFIXES={".cc",".cpp",".h",".hh",".hpp",".cxx"}
TEST_NAMES={"test.cc","test.h","testconf.cc","testconf.h","test_cluster.hpp","raft_lab_standalone.cc"}
BEGIN="/*RUSTYCPP:GEN-BEGIN"; END="/*RUSTYCPP:GEN-END"

def meta(repo):
    def run(*args): return subprocess.run(args,cwd=repo,text=True,capture_output=True).stdout.strip()
    return {"head_sha":run("git","rev-parse","HEAD"),"branch":run("git","branch","--show-current"),"dirty":bool(run("git","status","--porcelain"))}

def code_lines(lines):
    return sum(bool((x:=l.strip())) and not x.startswith("//") and not x.startswith("*") and not (x.startswith("/*") and x.endswith("*/")) for l in lines)

def scan_file(path):
    lines=path.read_text(errors="replace").splitlines(); dsl=[]; cpp=[]; gen=[]; in_dsl=in_gen=False
    for i,l in enumerate(lines,1):
        if l.startswith("#if RUSTYCPP_RUST"): in_dsl=True
        if l.startswith(BEGIN): in_gen=True
        target=dsl if in_dsl else gen if in_gen else cpp
        target.append((i,l))
        if l.startswith(END): in_gen=False
        if l.startswith("#endif") and in_dsl: in_dsl=False
    text="\n".join(l for _,l in lines and dsl)
    funcs=[]
    # Deliberately conservative: declarations are logical units; unmatched spans remain unknown.
    rx=re.compile(r"(?m)^\s*(?:pub\s+)?fn\s+(\w+)\s*\([^)]*\)[^{;]*\{")
    for m in rx.finditer(text):
        start=text[:m.start()].count("\n")+1; end=start+text[m.end():].find("}") if "}" in text[m.end():] else start
        body=text[m.end():text.find("}",m.end()) if "}" in text[m.end():] else len(text)]
        funcs.append((m.group(1),start,end,"RUST_DSL","DSL_EXPLICIT_UNSAFE" if "unsafe" in body else "DSL_SAFE",""))
    return lines,dsl,cpp,gen,funcs

def classify_cpp(body):
    if re.search(r"rocksdb|\b(?:open|read|write|close|fstat|memcpy|pthread|std::thread)\b|Function<|\b(?:void|char|uint8_t)\s*\*",body): return "D_BOUNDARY","external/runtime/raw-pointer boundary"
    if re.search(r"virtual|callback|condition_variable|mutex|shared_ptr|unique_ptr|template\s*<",body): return "C_LOCAL_REFACTOR","ownership, callback, threading, or template shape"
    return "B_DIRECT_MIGRATION","ordinary C++ control/data-flow without detected boundary"

def run(config):
    cfg=json.loads("{}") if False else None
    root=Path(config).resolve().parent; raw=config.read_text(); vals={}
    for line in raw.splitlines():
        m=re.match(r'\s*(repo|scope|results_root)\s*=\s*"([^"]+)"',line)
        if m: vals[m.group(1)]=m.group(2)
    repo=(root/vals["repo"]).resolve(); scope=(repo/vals["scope"]).resolve(); files=[]; excluded=[]
    for p in sorted(scope.rglob("*")):
        if not p.is_file() or p.suffix not in SUFFIXES: continue
        if p.name in TEST_NAMES or "/test" in p.name.lower(): excluded.append((str(p.relative_to(repo)),"test-only or harness"))
        else: files.append(p)
    records=[]; dloc=cloc=gloc=0; byfile=defaultdict(lambda: Counter())
    for p in files:
        lines,dsl,cpp,gen,df=scan_file(p); dloc+=code_lines([x for _,x in dsl]); cloc+=code_lines([x for _,x in cpp]); gloc+=code_lines([x for _,x in gen])
        for name,st,en,kind,status,reason in df:
            records.append({"file":str(p.relative_to(repo)),"qualified_name":name,"start_line":st,"end_line":en,"source_kind":kind,"generated":False,"rustycpp_status":status,"migration_class":"A_ALREADY_SAFE","reason":"Rust DSL function; no explicit unsafe detected"})
        # C++ function spans are intentionally conservative and one-per-brace declaration.
        txt="\n".join(x for _,x in cpp)
        for m in re.finditer(r"(?m)^\s*(?:[\w:<>~]+\s+)+([~\w]+)\s*\([^;{}]*\)\s*\{",txt):
            body=txt[m.end():txt.find("}",m.end()) if "}" in txt[m.end():] else len(txt)]; cls,why=classify_cpp(body)
            records.append({"file":str(p.relative_to(repo)),"qualified_name":m.group(1),"start_line":txt[:m.start()].count("\n")+1,"end_line":txt[:m.end()].count("\n")+1,"source_kind":"HANDWRITTEN_CPP","generated":False,"rustycpp_status":"CPP_UNVERIFIED","migration_class":cls,"reason":why})
    counts=Counter(r["migration_class"] for r in records); safe=sum(r["rustycpp_status"]=="DSL_SAFE" for r in records); total=len(records); authored=dloc+cloc
    dsl_count=sum(r["source_kind"]=="RUST_DSL" for r in records); explicit=sum(r["rustycpp_status"]=="DSL_EXPLICIT_UNSAFE" for r in records); cpp_unverified=sum(r["rustycpp_status"]=="CPP_UNVERIFIED" for r in records); boundaries=counts["D_BOUNDARY"]
    boundary_files={r["file"] for r in records if r["migration_class"]=="D_BOUNDARY"}
    result={"schema_version":1,"repository":meta(repo),"included_files":[str(p.relative_to(repo)) for p in files],"excluded_files":[{"file":f,"reason":r} for f,r in excluded],"functions_total_logical":total,"functions_verified_safe":safe,"current_verified_safe_function_pct":100*safe/total if total else 0,"dsl_function_count":dsl_count,"dsl_function_pct":100*dsl_count/total if total else 0,"dsl_safe_function_count":safe-explicit,"dsl_explicit_unsafe_function_count":explicit,"cpp_verified_safe_function_count":0,"cpp_explicit_unsafe_function_count":0,"cpp_unverified_function_count":cpp_unverified,"unknown_function_count":0,"rust_dsl_nonblank_loc":dloc,"handwritten_cpp_nonblank_loc":cloc,"generated_cpp_nonblank_loc":gloc,"authored_nonblank_loc":authored,"dsl_authored_loc_pct":100*dloc/authored if authored else 0,"migration_counts":dict(counts),"boundary_functions":boundaries,"boundary_function_pct":100*boundaries/total if total else 0,"boundary_files":len(boundary_files),"boundary_file_pct":100*len(boundary_files)/len(files) if files else 0,"potential_safe_envelope_functions":counts["A_ALREADY_SAFE"]+counts["B_DIRECT_MIGRATION"]+counts["C_LOCAL_REFACTOR"],"direct_safe_envelope_functions":counts["A_ALREADY_SAFE"]+counts["B_DIRECT_MIGRATION"]}
    result["potential_safe_envelope_pct"]=100*result["potential_safe_envelope_functions"]/total if total else 0; result["direct_safe_envelope_pct"]=100*result["direct_safe_envelope_functions"]/total if total else 0
    rid=datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")+"_"+hashlib.sha1(json.dumps(result,sort_keys=True).encode()).hexdigest()[:8]; out=(root/vals["results_root"])/rid; out.mkdir(parents=True)
    (out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); (out/"metadata.json").write_text(json.dumps(result["repository"],indent=2)+"\n")
    with (out/"functions.csv").open("w",newline="") as f: w=csv.DictWriter(f,fieldnames=records[0].keys() if records else ["file"]); w.writeheader(); w.writerows(records)
    with (out/"files.csv").open("w",newline="") as f: w=csv.writer(f); w.writerow(["file","included"]); w.writerows([[x,True] for x in result["included_files"]]+[[x["file"],False] for x in result["excluded_files"]])
    (out/"summary.csv").write_text("metric,value\n"+"\n".join(f"{k},{v}" for k,v in result.items() if not isinstance(v,(list,dict)))+"\n")
    (out/"summary.md").write_text("# Mako Raft Summary\n\nMeasured metrics; inventory estimates are not safety results.\n\n```json\n"+json.dumps(result,indent=2,sort_keys=True)+"\n```\n")
    return out

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--config",required=True); print(run(Path(p.parse_args(argv).config)))
if __name__=="__main__": main()
