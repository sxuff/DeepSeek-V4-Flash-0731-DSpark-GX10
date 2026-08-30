#!/usr/bin/env python3
import argparse, json, re, subprocess
from pathlib import Path

def extract_fence(text):
    m=re.search(r'```[^\n]*\n(.*?)```',text,re.S)
    return m.group(1).strip() if m else text.strip()

def code_ok(text):
    code=extract_fence(text)
    tests=r'''
original = [[5,7],[1,3],[3,4],[4,7],[10,10],[9,10]]
snapshot = [x[:] for x in original]
canon = lambda xs: [list(x) for x in xs]
assert canon(merge_intervals(original)) == [[1,7],[9,10]]
assert original == snapshot
assert canon(merge_intervals([])) == []
assert canon(merge_intervals([[2,2]])) == [[2,2]]
assert canon(merge_intervals([[1,2],[4,5]])) == [[1,2],[4,5]]
assert canon(merge_intervals([[-3,-1],[-1,2],[8,9],[7,8]])) == [[-3,2],[7,9]]
print("CANARY_EXECUTED")
'''
    cmd=['docker','run','--rm','-i','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','64','--memory','256m','--cpus','1','--user','65534:65534','python:3.13-alpine','python','-I','-']
    try:
        p=subprocess.run(cmd,input=code+'\n'+tests,text=True,capture_output=True,timeout=20)
        return p.returncode==0 and 'CANARY_EXECUTED' in p.stdout, {'exit_code':p.returncode,'stdout':p.stdout[-300:],'stderr':p.stderr[-300:]}
    except Exception as e:return False,{'error':type(e).__name__+': '+str(e)}

def rescore(r):
    fid=r['fixture_id']; text=r.get('output_text','')
    try:
        if fid=='arithmetic_exact':
            nums=re.findall(r'-?\d+',text); return bool(nums and int(nums[-1])==16229),{'last_integer':int(nums[-1]) if nums else None,'strict_exact':text.strip()=='16229'}
        if fid=='json_exact': return json.loads(extract_fence(text))=={'total':199,'ascending':[17,28,63,91]},{}
        if fid=='sequence_100': return [int(x) for x in re.findall(r'-?\d+',text)]==list(range(1,101)),{}
        if fid=='extract_records':
            x=json.loads(extract_fence(text)); exp=[{'ticket':'A-04','owner':'Luis','severity':'low'},{'ticket':'B-09','owner':'Noor','severity':'medium'},{'ticket':'C-17','owner':'Mina','severity':'high'}]; return x==exp,{'strict_json_envelope':text.lstrip().startswith('[')}
        if fid=='tool_call': return bool(r.get('quality_pass')),r.get('quality_detail',{})
        if fid in ('code_hidden_tests','code_merge_intervals'): return code_ok(text)
        if fid in ('reasoning_final','reasoning_89'): return bool(re.search(r'FINAL:\s*89\s*$',text.strip())),{}
        if fid=='five_lines':
            lines=[x.strip() for x in text.splitlines() if x.strip()]; starts=['INPUT:','CHECK:','RISK:','ACTION:','RESULT:']; return len(lines)==5 and all(lines[i].startswith(starts[i]) and len(lines[i].split())>=7 for i in range(5)),{'lines':lines}
        if fid=='json_square_table':
            x=json.loads(extract_fence(text)); return isinstance(x,list) and len(x)==40 and all(o=={'id':i,'label':f'item-{i:02d}','square':i*i} for i,o in enumerate(x,1)),{'count':len(x) if isinstance(x,list) else None}
        if fid=='prose_tracing':
            ps=[p.strip() for p in re.split(r'\n\s*\n',text.strip()) if p.strip()]; return len(ps)==12 and all(ps[i].startswith(f'P{i+1}:') and len(ps[i].split())>=36 for i in range(12)),{'paragraphs':len(ps),'word_counts':[len(p.split()) for p in ps]}
    except Exception as e:return False,{'error':type(e).__name__+': '+str(e)}
    return False,{'error':'unknown fixture'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--run',required=True); a=ap.parse_args(); root=Path(a.run)
    all_rows=[]; summary={}
    for arm in ['plain','dspark']:
        rows=[json.loads(x) for x in (root/arm/'rows.jsonl').read_text().splitlines()]
        resc=[]
        for r in rows:
            ok,detail=rescore(r); x={'arm':arm,'fixture_id':r['fixture_id'],'kind':r['kind'],'rep':r['rep'],'request_sha256':r['request_sha256'],'output_sha256':r['output_sha256'],'semantic_pass':ok,'detail':detail}; resc.append(x); all_rows.append(x)
        q=[x for x in resc if x['kind']=='quality']; s=[x for x in resc if x['kind']=='speed']
        summary[arm]={'quality_passes':sum(x['semantic_pass'] for x in q),'quality_total':len(q),'speed_validator_passes':sum(x['semantic_pass'] for x in s),'speed_validator_total':len(s),'failed_quality':[{'fixture_id':x['fixture_id'],'rep':x['rep'],'detail':x['detail']} for x in q if not x['semantic_pass']]}
        (root/arm/'semantic-rescore.jsonl').write_text('\n'.join(json.dumps(x,sort_keys=True) for x in resc)+'\n')
    summary['paired_quality_regression_count']=sum(1 for p,d in zip([x for x in all_rows if x['arm']=='plain' and x['kind']=='quality'],[x for x in all_rows if x['arm']=='dspark' and x['kind']=='quality']) if p['semantic_pass'] and not d['semantic_pass'])
    (root/'semantic-rescore-summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n'); print(json.dumps(summary,indent=2,sort_keys=True))
if __name__=='__main__': main()
