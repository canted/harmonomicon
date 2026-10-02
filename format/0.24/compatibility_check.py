"""Exact comparison with the complete retained 0.23 executable traces."""
import copy,json,subprocess,sys
from pathlib import Path
from runtime import run
from check import package
from image_check import witnesses as image_cases
from artifact_check import cases as artifact_cases
from voting_check import fixture_request
from input_check import request as input_request
from pooling_check import request as pooling_request
HERE=Path(__file__).resolve().parent

def check():
 requests=[]
 for case in json.loads((HERE/'conformance/cases.json').read_text()):
  p=copy.deepcopy(case['definition']) if 'definition' in case else package(case['package'])
  requests.append(dict(package=p,participants=case.get('participants',['a','b','c']),organizer='organizer',events=case['events'],settings=case.get('settings',{}),seed=case.get('seed')))
 requests += [req for req,_ in image_cases()]+[req for req,_ in artifact_cases()]
 requests += [fixture_request(case) for case in json.loads((HERE/'conformance/voting-cases.json').read_text())]
 requests += [input_request(case) for case in json.loads((HERE/'conformance/input-cases.json').read_text())]
 requests += [pooling_request(case) for case in json.loads((HERE/'conformance/pooling-cases.json').read_text())]
 for req in requests:
  expected=run(req)
  for language,file in [(sys.executable,'runtime.py'),('node','runtime.mjs')]:
   retained=copy.deepcopy(req);retained['package']['format']='harmonomicon.activity-package/0.23'
   actual=json.loads(subprocess.check_output([language,str(HERE.parent/'0.23'/file)],input=json.dumps(retained),text=True))
   assert actual==expected,(file,req.get('id'))
 print(f'All {len(requests)} retained 0.23 traces preserve full state, views and outcomes in both historical engines; envelope translation only')
 return len(requests)
if __name__=='__main__':check()
