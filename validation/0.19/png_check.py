"""Actual host PNG validators: output-bound and IDAT-order regression witnesses."""
import ast,base64,json,struct,subprocess,zlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
SIGNATURE=b'\x89PNG\r\n\x1a\n'
def chunk(kind,body):return struct.pack('>I',len(body))+kind+body+struct.pack('>I',zlib.crc32(kind+body)&0xffffffff)
def image(raw=None,width=1,height=1,channels=3,split=False,interleave=False,ancillary=False):
 if raw is None:raw=bytes([0])*(height*(1+width*channels))
 zipped=zlib.compress(raw);header=chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2 if channels==3 else 6,0,0,0));parts=[SIGNATURE,header]
 if ancillary:parts.append(chunk(b'tEXt',b'label\0before'))
 if split:
  pivot=max(1,len(zipped)//2);parts.append(chunk(b'IDAT',zipped[:pivot]))
  if interleave:parts.append(chunk(b'tEXt',b'label\0between'))
  parts.append(chunk(b'IDAT',zipped[pivot:]))
 else:parts.append(chunk(b'IDAT',zipped))
 if ancillary:parts.append(chunk(b'tEXt',b'label\0after'))
 parts.append(chunk(b'IEND',b''));return b''.join(parts)
def fixtures():
 return [('rgb',image(),True),('rgba',image(channels=4),True),('contiguous-idat',image(split=True),True),('ancillary-before-after',image(split=True,ancillary=True),True),('max-rgba',image(width=1024,height=1024,channels=4),True),('all-filter-types',image(raw=b''.join(bytes([i,0,0,0]) for i in range(5)),height=5),True),('noncontiguous-idat',image(split=True,interleave=True),False),('decoded-output-bomb',image(raw=bytes(8*1024*1024)),False),('oversized-decoded-stream',image(raw=bytes(5)),False),('short-decoded-stream',image(raw=bytes(3)),False),('invalid-filter',image(raw=bytes([5,0,0,0])),False),('crc-error',image()[:-1]+b'\x01',False),('trailing-bytes',image()+b'extra',False),('missing-iend',image()[:-12],False),('unsupported-dimensions',image(width=1025),False)]
def python_validator(authority=zlib):
 # Compile only the checked-in function, avoiding CLI/server side effects.
 tree=ast.parse((HERE/'python_host.py').read_text());function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='valid_png');namespace={'zlib':authority,'MAX_IMAGE_BYTES':524288};exec(compile(ast.Module(body=[function],type_ignores=[]),str(HERE/'python_host.py'),'exec'),namespace);return namespace['valid_png']
def node_results(fixtures):
 host=(HERE/'node_host.mjs').read_text();source=host[host.index('const MAX_IMAGE_BYTES'):host.index('function authorized(')]
 js="import {inflateSync} from 'node:zlib';import fs from 'node:fs';\n"+source+"\nconsole.log(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(x=>validPng(Buffer.from(x,'base64')))));"
 return json.loads(subprocess.check_output(['node','--input-type=module','-e',js],input=json.dumps([base64.b64encode(blob).decode() for _,blob,_ in fixtures]),text=True))
class BoundedZlib:
 error=zlib.error
 crc32=staticmethod(zlib.crc32)
 def __init__(self):self.returned=[]
 def decompressobj(self):
  owner=self;decoder=zlib.decompressobj()
  class Decoder:
   def decompress(self,data,limit):
    assert limit==5,'1x1 RGB bomb must decode at most expected+1 bytes';value=decoder.decompress(data,limit);owner.returned.append(len(value));assert len(value)<=limit;return value
   def flush(self,*args):raise AssertionError('flush is not an output-bound operation and must not be called')
   def __getattr__(self,name):return getattr(decoder,name)
  return Decoder()
def check():
 data=fixtures();validator=python_validator();got=[validator(blob) for _,blob,_ in data];expected=[expected for _,_,expected in data];assert got==expected,[(data[i][0],a,b) for i,(a,b) in enumerate(zip(got,expected)) if a!=b];assert node_results(data)==expected
 guard=BoundedZlib();assert python_validator(guard)(next(blob for name,blob,_ in data if name=='decoded-output-bomb')) is False;assert guard.returned==[5]
 print(f'{len(data)} actual-validator PNG witnesses pass in Python/Node; 8MiB bomb returns only five decoded bytes and never calls flush; noncontiguous IDAT rejects')
if __name__=='__main__':check()
