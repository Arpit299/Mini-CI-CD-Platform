import argparse
import json
import shutil
import subprocess
import sys
import time
import uuid
from collections import deque
from pathlib import Path
class CICDPipeline:
    def __init__(self,workspace):
        self.workspace=Path(workspace).expanduser().resolve()
        self.root=self.workspace/".mini_cicd"
        self.artifacts=self.root/"artifacts"
        self.reports=self.root/"reports"
        self.artifacts.mkdir(parents=True,exist_ok=True)
        self.reports.mkdir(parents=True,exist_ok=True)
        self.queue=deque()
        self.steps=[]
    def project_type(self):
        names={p.name.lower() for p in self.workspace.iterdir() if p.exists()}
        if "package.json" in names:return "node"
        if "pyproject.toml" in names or "requirements.txt" in names or any(self.workspace.glob("*.py")):return "python"
        return "generic"
    def commands(self):
        kind=self.project_type()
        if kind=="python":
            tests=(self.workspace/"tests").exists() or bool(list(self.workspace.glob("test_*.py"))) or bool(list(self.workspace.glob("*_test.py")))
            test=f'"{sys.executable}" -m pytest -q' if tests else f'"{sys.executable}" -m compileall -q .'
            return kind,[("test",test),("build",f'"{sys.executable}" -m compileall -q .')]
        if kind=="node":return kind,[("test","npm test --if-present"),("build","npm run build --if-present")]
        return kind,[("build","echo Build stage completed")]
    def run_command(self,command):
        started=time.perf_counter()
        try:
            result=subprocess.run(command,cwd=self.workspace,shell=True,text=True,capture_output=True,timeout=180)
            return {"status":"PASS" if result.returncode==0 else "FAIL","returncode":result.returncode,"duration":round(time.perf_counter()-started,3),"stdout":result.stdout[-10000:],"stderr":result.stderr[-10000:]}
        except subprocess.TimeoutExpired:return {"status":"FAIL","returncode":124,"duration":round(time.perf_counter()-started,3),"stdout":"","stderr":"Command timed out."}
        except Exception as error:return {"status":"FAIL","returncode":1,"duration":round(time.perf_counter()-started,3),"stdout":"","stderr":str(error)}
    def collect_artifacts(self,run_id):
        target=self.artifacts/run_id
        target.mkdir(parents=True,exist_ok=True)
        excluded={".mini_cicd",".git",".venv","venv","node_modules","__pycache__"}
        files=[]
        for item in self.workspace.rglob("*"):
            if not item.is_file():continue
            rel=item.relative_to(self.workspace)
            if any(part in excluded for part in rel.parts):continue
            dest=target/rel
            dest.parent.mkdir(parents=True,exist_ok=True)
            try:
                shutil.copy2(item,dest)
                files.append(str(rel))
            except OSError:pass
        (target/"manifest.json").write_text(json.dumps({"run_id":run_id,"files":files,"count":len(files)},indent=2),encoding="utf-8")
        return str(target),len(files)
    def execute(self):
        kind,commands=self.commands()
        run_id=time.strftime("%Y%m%d_%H%M%S")+"_"+uuid.uuid4().hex[:8]
        self.queue.extend(commands)
        failed=False
        while self.queue:
            name,command=self.queue.popleft()
            result=self.run_command(command)
            result["name"]=name
            result["command"]=command
            self.steps.append(result)
            if result["status"]=="FAIL":
                failed=True
                break
        status="FAIL" if failed else "PASS"
        artifact_path=""
        artifact_count=0
        if status=="PASS":artifact_path,artifact_count=self.collect_artifacts(run_id)
        report={"run_id":run_id,"project_type":kind,"workspace":str(self.workspace),"status":status,"steps":self.steps,"artifact_path":artifact_path,"artifact_count":artifact_count,"created_at":time.strftime("%Y-%m-%d %H:%M:%S")}
        report_path=self.reports/f"{run_id}.json"
        report_path.write_text(json.dumps(report,indent=2),encoding="utf-8")
        report["report_path"]=str(report_path)
        return report
def create_demo(path):
    path=Path(path)
    path.mkdir(parents=True,exist_ok=True)
    (path/"app.py").write_text("def add(a,b):\n    return a+b\n",encoding="utf-8")
    (path/"test_app.py").write_text("from app import add\ndef test_add():\n    assert add(2,3)==5\n",encoding="utf-8")
def main():
    parser=argparse.ArgumentParser(prog="mini_cicd_platform")
    parser.add_argument("workspace",nargs="?")
    parser.add_argument("--demo",action="store_true")
    parser.add_argument("--json",dest="json_path",default="")
    args=parser.parse_args()
    workspace=Path(args.workspace).expanduser().resolve() if args.workspace else Path.cwd().resolve()
    if args.demo:
        workspace=workspace/"cicd_demo_project"
        if workspace.exists():shutil.rmtree(workspace)
        create_demo(workspace)
    workspace.mkdir(parents=True,exist_ok=True)
    try:report=CICDPipeline(workspace).execute()
    except Exception as error:
        print(f"ERROR: {error}")
        return
    print("MINI CI/CD PLATFORM")
    print("="*60)
    print(f"Workspace: {report['workspace']}")
    print(f"Project Type: {report['project_type']}")
    print(f"Pipeline Status: {report['status']}")
    print(f"Run ID: {report['run_id']}")
    print("\nPIPELINE")
    for step in report["steps"]:print(f"[{step['status']}] {step['name']} | {step['duration']}s")
    if report["artifact_path"]:print(f"\nArtifacts: {report['artifact_path']}\nArtifact Files: {report['artifact_count']}")
    print(f"Report: {report['report_path']}")
    if args.json_path:
        out=Path(args.json_path).expanduser().resolve()
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(report,indent=2),encoding="utf-8")
        print(f"JSON: {out}")
if __name__=="__main__":main()