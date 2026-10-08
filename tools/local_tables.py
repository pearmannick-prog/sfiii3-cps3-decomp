"""List jump tables that PS2 functions build locally and the arcade table the same function reads.
Names by position are proposals: arcade tables often differ in length, and the reader runs on into the next table."""
import re,csv,json,struct,sys,glob,collections
import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from sh2 import Image
W,REF=sys.argv[1],sys.argv[2]  # usage: local_tables.py <work dir> <3s-decomp dir>
d=open(W+"/sfiii3r1.bin","rb").read(); img=Image(d,0x06000000,0x06000400,0x0613BDFA)
rows=list(csv.DictReader(open(W+'/symbols.csv'))); A2N={int(r['arcade_addr'],16):r for r in rows}; N2A={r['name']:int(r['arcade_addr'],16) for r in rows}
j=json.load(open(W+'/split-r1/functions.json')); F={f['addr'] for f in j['functions']}
def table_at(a):
    out=[]
    while a-0x06000000+4<=len(d):
        v=struct.unpack_from('>I',d,a-0x06000000)[0]
        if v not in F: break
        out.append(v); a+=4
    return out
res=[]
for path in glob.glob(REF+'/src/anniversary/sf33rd/Source/Game/**/*.c',recursive=True):
    src=open(path,errors='replace').read()
    for m in re.finditer(r'\n(?:static )?[\w\*]+ (\w+)\([^;{)]*\) \{\n(.*?)\n\}\n',src,re.S):
        fn=m.group(1); tb=re.findall(r'\(\*(?:const )?(\w+)\[(\d*)\]\)\([^)]*\)\s*=\s*\{([^}]*)\}',m.group(2))
        if not tb or fn not in N2A: continue
        f=img.analyze(N2A[fn])
        lits=[]
        for l,n in sorted(f.lits.items()):
            if n==4:
                v=struct.unpack_from('>I',d,l-0x06000000)[0]
                if 0x0613BDFA<=v<0x06000000+len(d) and v%4==0:
                    t=table_at(v)
                    if len(t)>=2 and v not in [x[0] for x in lits]: lits.append((v,t))
        res.append((fn,[(t[0],[x.strip() for x in t[2].split(',') if x.strip()]) for t in tb],lits))
json.dump(res,open(W+'/localtbl.json','w'))
c=collections.Counter()
for fn,pt,at in res:
    if len(pt)==len(at):
        for (tn,names),(ta,ents) in zip(pt,at):
            k='equal-len' if len(names)==len(ents) else 'len-differs'
            c[k]+=1
            ok=sum(1 for n,e in zip(names,ents) if A2N.get(e,{}).get('name')==n)
            new=[(n,e) for n,e in zip(names,ents) if e not in A2N and n not in N2A]
            conf=[(n,'%08X'%e,A2N[e]['name'],A2N[e]['grade']) for n,e in zip(names,ents) if e in A2N and A2N[e]['name']!=n]
            if k=='len-differs' or new or conf: print(fn,tn,k,len(names),len(ents),'agree',ok,'new',len(new),'conflict',conf[:4])
    else: c['table-count-differs']+=1; print(fn,'tables ps2/arcade',len(pt),len(at))
print(c)
