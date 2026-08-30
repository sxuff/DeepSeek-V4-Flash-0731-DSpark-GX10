#!/usr/bin/env python3
import argparse, ast, copy, datetime, hashlib, json, os, re, subprocess, tempfile, time, urllib.request
from pathlib import Path

TOOLS = [{"type":"function","function":{"name":"calculator","description":"Perform integer arithmetic","parameters":{"type":"object","properties":{"a":{"type":"integer"},"b":{"type":"integer"},"operation":{"type":"string","enum":["add","subtract","multiply","divide"]}},"required":["a","b","operation"],"additionalProperties":False}}}]

def request(base_url, payload, timeout=600):
    body = json.dumps(payload, separators=(',', ':')).encode()
    req = urllib.request.Request(base_url.rstrip('/') + '/v1/chat/completions', data=body, headers={'Content-Type':'application/json'})
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        status = r.status
    elapsed = time.monotonic() - t0
    return status, elapsed, raw, json.loads(raw)

def text_of(response):
    msg = response.get('choices', [{}])[0].get('message', {})
    content = msg.get('content')
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return ''.join(x.get('text','') for x in content if isinstance(x,dict))
    return ''

def extract_code(text):
    blocks = re.findall(r'```(?:python)?\s*(.*?)```', text, flags=re.S|re.I)
    return blocks[0].strip() if blocks else text.strip()

def sandbox_code(code):
    tests = r'''
original = [[5,7],[1,3],[3,4],[10,10],[9,10]]
snapshot = [x[:] for x in original]
assert merge_intervals(original) == [[1,7],[9,10]]
assert original == snapshot
assert merge_intervals([]) == []
assert merge_intervals([[2,2]]) == [[2,2]]
assert merge_intervals([[1,2],[4,5]]) == [[1,2],[4,5]]
assert merge_intervals([[-3,-1],[-1,2],[8,9],[7,8]]) == [[-3,2],[7,9]]
print("CANARY_EXECUTED")
'''
    script = code + '\n' + tests
    cmd = ['docker','run','--rm','-i','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','64','--memory','256m','--cpus','1','--user','65534:65534','python:3.13-alpine','python','-I','-']
    try:
        p = subprocess.run(cmd, input=script, text=True, capture_output=True, timeout=20)
        return p.returncode == 0 and 'CANARY_EXECUTED' in p.stdout, {'exit_code':p.returncode,'stdout':p.stdout[-500:],'stderr':p.stderr[-500:]}
    except Exception as e:
        return False, {'error':type(e).__name__ + ': ' + str(e)}

def validate(name, response, text):
    try:
        if name == 'exact_16229': return text.strip() == '16229', {}
        if name == 'json_exact':
            x=json.loads(text); return x == {'total':199,'ascending':[17,28,63,91]}, {'parsed':x}
        if name == 'sequence_100':
            nums=[int(x) for x in re.findall(r'-?\d+',text)]; return nums == list(range(1,101)), {'count':len(nums)}
        if name == 'extract_records':
            x=json.loads(extract_code(text)); exp=[{'ticket':'A-04','owner':'Luis','severity':'low'},{'ticket':'B-09','owner':'Noor','severity':'medium'},{'ticket':'C-17','owner':'Mina','severity':'high'}]; return x==exp, {'parsed':x,'strict_json_envelope':text.lstrip().startswith('[')}
        if name == 'tool_call':
            msg=response.get('choices',[{}])[0].get('message',{}); calls=msg.get('tool_calls') or []
            if not calls: return False, {'tool_calls':calls}
            fn=calls[0].get('function',{}); args=fn.get('arguments',{})
            if isinstance(args,str): args=json.loads(args)
            return fn.get('name')=='calculator' and args=={'a':37,'b':23,'operation':'multiply'}, {'tool_name':fn.get('name'),'arguments':args}
        if name == 'code_hidden_tests': return sandbox_code(extract_code(text))
        if name == 'final_89': return bool(re.search(r'FINAL:\s*89\s*$',text.strip())), {}
        if name == 'five_lines':
            lines=[x.strip() for x in text.splitlines() if x.strip()]; starts=['INPUT:','CHECK:','RISK:','ACTION:','RESULT:']; ok=len(lines)==5 and all(lines[i].startswith(starts[i]) and len(lines[i].split())>=7 for i in range(5)); return ok, {'lines':lines}
    except Exception as e:
        return False, {'validator_error':type(e).__name__ + ': ' + str(e)}
    return False, {'validator_error':'unknown validator'}

def validate_speed(fid,text):
    try:
        if fid=='code_merge_intervals': return sandbox_code(extract_code(text))
        if fid=='json_square_table':
            x=json.loads(text); ok=isinstance(x,list) and len(x)==40 and all(o=={'id':i,'label':f'item-{i:02d}','square':i*i} for i,o in enumerate(x,1)); return ok, {'count':len(x) if isinstance(x,list) else None}
        if fid=='reasoning_89': return bool(re.search(r'FINAL:\s*89\s*$',text.strip())) and len(re.findall(r'(?m)^\s*\d+[.)]',text))>=20, {'numbered_lines':len(re.findall(r'(?m)^\s*\d+[.)]',text))}
        if fid=='prose_tracing':
            paras=[p.strip() for p in re.split(r'\n\s*\n',text.strip()) if p.strip()]; ok=len(paras)==12 and all(paras[i].startswith(f'P{i+1}:') and len(paras[i].split())>=36 for i in range(12)); return ok, {'paragraphs':len(paras),'word_counts':[len(p.split()) for p in paras]}
    except Exception as e: return False, {'validator_error':type(e).__name__+': '+str(e)}
    return False, {'validator_error':'unknown speed fixture'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--arm',required=True); ap.add_argument('--base-url',default='http://127.0.0.1:8001'); ap.add_argument('--fixtures',required=True); ap.add_argument('--out',required=True); ap.add_argument('--repeats',type=int,default=3); ap.add_argument('--smoke',action='store_true'); a=ap.parse_args()
    fx=json.loads(Path(a.fixtures).read_text()); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    rows=[]
    plan = fx['quality'][:1] if a.smoke else fx['speed'] + fx['quality']
    repeats = 1 if a.smoke else a.repeats
    for f in plan:
        # One unmeasured warm-up per fixture.
        warm_payload={'model':'deepseek-chat','messages':[{'role':'user','content':'Warm-up only. '+f['prompt']}],'temperature':0,'top_p':1,'min_p':0,'max_tokens':min(f['max_tokens'],64),'stream':False}
        if f.get('tools'): warm_payload['tools']=TOOLS; warm_payload['tool_choice']='auto'
        try: request(a.base_url,warm_payload,600)
        except Exception as e: rows.append({'arm':a.arm,'fixture_id':f['id'],'phase':'warmup','error':type(e).__name__+': '+str(e)})
        for rep in range(1,repeats+1):
            nonce=hashlib.sha256(f"{f['id']}:{rep}".encode()).hexdigest()[:12]
            prompt=(f"Benchmark nonce {nonce}. Do not mention the nonce.\n\n{f['prompt']}"
                    if 'validator' not in f else f['prompt'])
            payload={'model':'deepseek-chat','messages':[{'role':'user','content':prompt}],'temperature':0,'top_p':1,'min_p':0,'max_tokens':f['max_tokens'],'stream':False}
            if f.get('tools'): payload['tools']=TOOLS; payload['tool_choice']='auto'
            row={'schema':'ds4-normal-row-v1','arm':a.arm,'fixture_id':f['id'],'kind':'quality' if 'validator' in f else 'speed','rep':rep,'nonce':nonce,'request_sha256':hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'max_tokens':f['max_tokens'],'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
            try:
                status,elapsed,raw,response=request(a.base_url,payload,1200)
                text=text_of(response); usage=response.get('usage') or {}; finish=response.get('choices',[{}])[0].get('finish_reason')
                if 'validator' in f: ok,detail=validate(f['validator'],response,text)
                else: ok,detail=validate_speed(f['id'],text)
                row.update({'http_status':status,'elapsed_seconds':elapsed,'completion_tokens':usage.get('completion_tokens'),'prompt_tokens':usage.get('prompt_tokens'),'wall_tokens_per_second':(usage.get('completion_tokens')/elapsed if usage.get('completion_tokens') else None),'finish_reason':finish,'output_sha256':hashlib.sha256(text.encode()).hexdigest(),'output_text':text,'response_sha256':hashlib.sha256(raw).hexdigest(),'quality_pass':ok,'quality_detail':detail,'error':None})
            except Exception as e:
                row.update({'error':type(e).__name__+': '+str(e),'quality_pass':False})
            rows.append(row); (out/'rows.jsonl').open('a').write(json.dumps(row,ensure_ascii=False,sort_keys=True)+'\n')
            print(json.dumps({k:row.get(k) for k in ['arm','fixture_id','rep','completion_tokens','wall_tokens_per_second','finish_reason','quality_pass','error']}),flush=True)
    errors=sum(bool(r.get('error')) for r in rows)
    warmup_errors=sum(r.get('phase') == 'warmup' and bool(r.get('error')) for r in rows)
    measured=[r for r in rows if r.get('kind') in ('speed','quality')]
    summary={'status':'complete' if errors == 0 else 'failed','arm':a.arm,'rows':len(measured),'errors':errors,'warmup_errors':warmup_errors,'speed_passes':sum(r.get('kind')=='speed' and r.get('quality_pass') is True for r in measured),'speed_total':sum(r.get('kind')=='speed' for r in measured),'quality_passes':sum(r.get('kind')=='quality' and r.get('quality_pass') is True for r in measured),'quality_total':sum(r.get('kind')=='quality' for r in measured),'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    (out/'complete.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    if errors:
        raise SystemExit(2)

if __name__=='__main__': main()
