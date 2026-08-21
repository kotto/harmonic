#!/usr/bin/env python3
"""Test final : pipeline complet avec support multi-chaîne (MERGE)."""
import sys, re, torch, numpy as np
sys.path.insert(0, 'E:\\SAAS - Copie\\engine')
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel

NUM_RE = re.compile(r'(\d+(?:\.\d+)?)\s*(%)?', re.IGNORECASE)
OM = {'MUL':'MULTIPLY','SUB':'SUBTRACT','ADD':'ADD','DIV':'DIVIDE','INIT':'INIT','MERGE':'MERGE'}

def encoder_merge(ops):
    frames=[];reg=[];lv=None;pvc=None
    def nv(val,op,pa=None):
        nonlocal lv;vn=f'e{len(reg)+1}'
        reg.append({'name':vn,'value':val,'entity':op.get('entity'),'object':op.get('object'),'op':op.get('op','').upper(),'parent':pa if pa else lv})
        if val is not None:lv=vn;return vn
    def bs(op,reg,lv):
        b,bs_=None,0
        for v in reversed(reg):
            if v.get('value') is None:continue
            s=0
            if op.get('object') and v.get('object') and str(op['object'])==str(v['object']):s+=2
            if s>bs_:bs_,b=s,v['name']
        return b if b else lv
    for op in ops:
        on=op.get('op','').upper()
        if on=='INIT':
            try:v=float(op.get('value',0))
            except:v=0.0
            if lv is not None:
                pvc=next((x['value'] for x in reg if x['name']==lv),None)
            nv(v,op);frames.append({'code':4,'amp':abs(v),'phase':0.0 if v>=0 else 3.14159,'op':'INIT','var':lv,'value':v});continue
        if on=='MERGE':
            if lv is not None and pvc is not None:
                cur=next((x['value'] for x in reg if x['name']==lv),0.0)
                if cur is None:cur=0.0
                nv2=cur+pvc;vn=nv(nv2,op)
                frames.append({'code':3,'amp':1.0,'phase':1.5708,'op':'ADD','var':vn,'value':None})
                d=abs(nv2-cur)
                frames.append({'code':3,'amp':d if d>1e-9 else 1.0,'phase':0.0,'op':'ADD','var':vn,'value':nv2})
            continue
        if on=='QUERY':continue
        sn=bs(op,reg,lv)
        sv=next((v['value'] for v in reg if v['name']==sn),0.0)
        if sv is None:sv=0.0
        if on in ('ADD','SUBTRACT','MULTIPLY','DIVIDE'):
            cd=3 if on=='ADD' else 1 if on=='SUBTRACT' else 2 if on=='MULTIPLY' else 5
            opd=op.get('value') or op.get('multiplier') or op.get('divisor')
            if not isinstance(opd,(int,float)):continue
            opd=float(opd)
            # Règle pourcentage étendue
            if on=='SUBTRACT':
                se=next((v for v in reg if v['name']==sn),None)
                if se and se.get('op')=='MULTIPLY':
                    d=se.get('value');p_=se.get('parent')
                    pe=next((v for v in reg if v['name']==p_),None) if p_ else None
                    p=pe.get('value') if pe else None
                    if d is not None and p is not None and d < p:
                        nv2=p-d;vn=nv(nv2,op,pa=p_)
                        frames.append({'code':cd,'amp':1.0,'phase':1.5708,'op':on,'var':vn,'value':None})
                        delta=abs(nv2-p)
                        frames.append({'code':cd,'amp':delta if delta>1e-9 else 1.0,'phase':3.14159,'op':on,'var':vn,'value':nv2})
                        continue
            if on=='ADD':nv2=sv+opd;ph=0.0
            elif on=='SUBTRACT':nv2=sv-opd;ph=3.14159
            elif on=='MULTIPLY':nv2=sv*opd;ph=0.0
            elif on=='DIVIDE':nv2=sv/opd if opd else sv;ph=-1.5708
            vn=nv(nv2,op,pa=sn)
            frames.append({'code':cd,'amp':1.0,'phase':1.5708,'op':on,'var':vn,'value':None})
            d=abs(nv2-sv)
            frames.append({'code':cd,'amp':d if d>1e-9 else 1.0,'phase':ph,'op':on,'var':vn,'value':nv2})
    return frames

def decoder(frames):
    z=0.0+0.0j;fv=None
    for f in frames:
        z+=f['amp']*np.exp(1j*f['phase'])
        if f.get('value') is not None:fv=f['value']
    return float(z.real) if fv is None else fv

def segs_texte(q):
    nums=[(m.start(),m.end()) for m in NUM_RE.finditer(q)]
    ss=[]
    for i,(s,e) in enumerate(nums):
        d=nums[i-1][1] if i>0 else max(0,s-30)
        f=min(s+15,nums[i+1][0] if i+1<len(nums) else len(q))
        ss.append(q[max(0,d):f].lower())
    return ss

def role(s):
    if not s:return None
    for m in ['shared equally','divided by','bags of','packs of','split among','shared between','per pack','per box','packs contain','pack contains']:
        if m in s:return 'DIV'
    for m in ['per person','per student','per child','per guest','per player']:
        if m in s:return 'DIV'
    for m in ['per hour','per day','per mile','per second','per minute','per week','per kg','mph']:
        if m in s:return 'MUL'
    for m in ['each','every','apiece','doubles','triples','times','twice','for each']:
        if m in s:return 'MUL'
    for m in ['gives away','gives','loses','sells','bought','purchased','spent on','bought something','did not buy','remaining','left over','are used','consumed','drinks','eats','breaks','removes','throws','donates','pays','spends','costs','cost','leftover','left from','had left']:
        if m in s:return 'SUB'
    for m in ['buys','gains','finds','receives','earns','collects','adds','gets','acquires','picks up','invites more','gathers','harvests','wins']:
        if m in s:return 'ADD'
    for m in ['of the','per']:
        if m in s:return 'MUL'
    return None

def post(pred,q):
    pcts=[float(m.group(1))/100.0 for m in NUM_RE.finditer(q) if m.group(2)]
    tn=[float(m.group(1)) for m in NUM_RE.finditer(q)]
    ss=segs_texte(q);ops=[];pr=None;pmf=False
    for t in pred.replace('\n',' ').split():
        m=re.match(r'(INIT|MUL|SUB|ADD|DIV)\(([^)]+)\)',t.strip())
        if not m:continue
        op,v=m.group(1),m.group(2)
        try:v=float(v)
        except:continue
        ep=False
        for p in pcts:
            if abs(v-p*100)<1e-6:v=p;op='MUL';ep=True;break
        if op=='INIT':ops.append({'op':'INIT','value':v});pmf=False;continue
        pos=len(ops)
        if pos<len(ss):
            r=role(ss[pos])
            if r is None and pr is not None:r=pr
            if r:op=r;pr=r
        if not ep and not any(abs(v-x)<1e-6 for x in tn) and not pmf:continue
        mapped=OM.get(op)
        if not mapped:continue
        pmf=(mapped=='MULTIPLY' and v>0 and v<1.0)
        if mapped=='MULTIPLY':ops.append({'op':'MULTIPLY','multiplier':v})
        elif mapped=='DIVIDE':ops.append({'op':'DIVIDE','divisor':v})
        elif mapped=='SUBTRACT':ops.append({'op':'SUBTRACT','value':v})
        elif mapped=='ADD':ops.append({'op':'ADD','value':v})
    return ops

def detect_split(q):
    nums=list(NUM_RE.finditer(q));ql=q.lower()
    for sep in [' then ',' after ',' later ',' finally ',' afterwards ',' next,']:
        p=ql.find(sep)
        if p>=0:
            for i,n in enumerate(nums):
                if n.start()>=p+len(sep):return i-1
    return None

def split_ops(ops,sp):
    if sp is None or sp>=len(ops)-1:return ops
    c1=ops[:sp+1];c2=ops[sp+1:]
    if not c2:return ops
    o2=c2[0];ni={'op':'INIT','value':o2.get('multiplier') or o2.get('value') or o2.get('divisor') or 0}
    c2[0]=ni
    return c1+c2+[{'op':'MERGE'}]

def solve(q):
    inp=tok('translate to operations: '+q,return_tensors='pt',max_length=256,truncation=True)
    with torch.no_grad():out=model.generate(**inp,max_new_tokens=64,num_beams=1)
    pred=tok.decode(out[0],skip_special_tokens=True)
    ops=post(pred,q)
    sp=detect_split(q)
    ops=split_ops(ops,sp)
    if not ops:return None
    try:return decoder(encoder_merge(ops))
    except:return None

tok=AutoTokenizer.from_pretrained('google/flan-t5-small')
base=AutoModelForSeq2SeqLM.from_pretrained('google/flan-t5-small',low_cpu_mem_usage=True)
model=PeftModel.from_pretrained(base,'data/t5_transvertical_v2/final')
model.eval()

tests=[
    ('John has 20 apples. He gives 8 away.',12.0),
    ('John has 20 apples. He gives 8 to Mary and 5 to Tom.',7.0),
    ('John invited 20 people. Each will eat 2 hot dogs. He already has 4 left over. Packs contain 6 and cost 2 each.',12.0),
    ('A store has 150 customers. 60% buy something. The rest leave.',60.0),
    ('A train travels 10 mph for 3 hours. Then 6 mph for 2 hours.',42.0),
    ('There are 5 boxes. Each box has 12 eggs.',60.0),
]
ok=0
for q,exp in tests:
    got=solve(q)
    good=got is not None and abs(got-exp)<1e-6
    ok+=good
    print(f'{"✅" if good else "❌"} got={got:.2f} exp={exp:.2f}')
print(f'Score: {ok}/{len(tests)}')