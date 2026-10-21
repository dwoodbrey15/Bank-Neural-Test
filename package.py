from pathlib import Path
import ast
import re
import tempfile
import zipfile
import subprocess
import json

root=Path(__file__).resolve().parent
lookup='globalThis.BankTrainingLookup=BankMultiplayer.create(BankGoals.create('+ (root/'goal-data.json').read_text().strip() +'));'
(root/'training-lookup.js').write_text(lookup)
bundle='\n;\n'.join([(root/name).read_text() for name in ['goal-engine.js','multiplayer-policy.js','training-lookup.js','engine.js','neural.js','learning.js','neural-league.js']]+[(root/'trainer-worker.js').read_text().split('\n',1)[1]])
assert 'importScripts(' not in bundle
assert '</script' not in bundle.lower()
p=root/'index.html';shell=p.read_text();block='<script id="trainer-source" type="text/plain">'+bundle+'</script>'
if 'id="trainer-source"' in shell:shell=re.sub(r'<script id="trainer-source" type="text/plain">[\s\S]*?</script>',lambda _:block,shell,count=1)
else:shell=shell.replace('<script id="engine-source"',block+'\n<script id="engine-source"',1)
p.write_text(shell)
worker=(root/'sw.js').read_text()
core=ast.literal_eval(re.search(r'CORE=(\[[^\]]+\])',worker)[1])
optional=ast.literal_eval(re.search(r'OPTIONAL=(\[[^\]]+\])',worker)[1])
runtime=list(dict.fromkeys(['index.html','sw.js']+core+optional))
html=(root/'index.html').read_text()
for source in re.findall(r'<script[^>]+src="([^"]+)"',html):
 assert source.removeprefix('./') in runtime,source
manifest=json.loads((root/'manifest.webmanifest').read_text())
for icon in manifest['icons']:
 assert icon['src'] in runtime
names=runtime+['model-spec.json','training-notes.txt','solo-method.txt','multiplayer-method.txt','package.py']
names+=['tests/'+name for name in ['neural-only.test.js','scripted-compatibility.test.js','browser-neural-only.test.js','offline.test.js','target-selector.test.js','neural.test.js','paired-learning.test.js','engine.test.js','solo.test.js','target.test.js']]
names+=sorted(str(p.relative_to(root)) for p in (root/'validation').glob('v5.0-*.json'))
archive=root.parent/'bank-pilot-neural-v5.0.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as output:
 for name in names:
  assert (root/name).is_file(),name
  output.write(root/name,name)
with tempfile.TemporaryDirectory(dir=root.parent) as directory:
 with zipfile.ZipFile(archive) as source:
  assert source.testzip() is None
  assert set(runtime).issubset(source.namelist())
  source.extractall(directory)
 extracted=Path(directory)
 for name in runtime:
  assert (extracted/name).read_bytes()==(root/name).read_bytes(),name
 subprocess.run(['node','--check',str(extracted/'sw.js')],check=True)
 for test in ['neural-only.test.js','scripted-compatibility.test.js','offline.test.js','target-selector.test.js']:
  subprocess.run(['node',str(extracted/'tests'/test)],check=True)
print(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size,'files':len(names),'requiredRuntimeFiles':len(runtime),'includesServiceWorker':True,'testedExtractedArchive':True}))
