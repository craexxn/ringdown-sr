"""Inject isolated scheduler counterexamples; this branch must never be merged."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

script = Path(__file__).with_name('check_ci.py')
case = os.environ['PROOF_CASE']
if sys.argv[1] == 'gate':
    actual = json.loads(os.environ['CI_NEEDS'])
    assert all(key.startswith(case+'-') for key in actual)
    os.environ['CI_NEEDS'] = json.dumps({key.removeprefix(case+'-'): value for key,value in actual.items()})
    os.execv(sys.executable,[sys.executable,str(script),'gate'])

root = Path(tempfile.mkdtemp(prefix='scope-proof-'))
def git(*args):
    return subprocess.run(['git',*args],cwd=root,capture_output=True,check=True,text=True).stdout.strip()
git('init','-b','main')
git('config','user.name','Isolated CI proof')
git('config','user.email','ci-proof@example.invalid')
(root/'README.md').write_text('Initial prose.\n')
git('add','.')
git('commit','-m','Initial fixture')
base = git('rev-parse','HEAD')
(root / ('README.md' if case=='docs' else 'source.py')).write_text('Updated fixture.\n')
git('add','.')
git('commit','-m','Fixture change')
head = git('rev-parse','HEAD')
event_path=root/'event.json'
event_path.write_text(json.dumps({'before':base,'after':head,'forced':False}))
os.environ['GITHUB_EVENT_PATH']=str(event_path)
os.environ['GITHUB_EVENT_NAME']='push'
if case=='scope-error': os.environ['GITHUB_OUTPUT']=str(root)
spec=importlib.util.spec_from_file_location('ci',script)
ci=importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci)
ci.ROOT=root
sys.argv=[str(script),'scope']
ci.main()
if case in {'missing','invalid'}:
    Path(os.environ['GITHUB_OUTPUT']).write_text('' if case=='missing' else 'full=invalid\n')
