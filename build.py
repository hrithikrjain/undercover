"""Build index.html from src/template.html + src/words.txt and validate the word bank."""
import json,re,sys,itertools,collections
DROP=[w.strip().lower() for w in open('src/drop.txt',encoding='utf-8') if w.strip() and not w.startswith('#')]
cat=sub=None;groups=collections.OrderedDict();clusters=[]
import glob
lines=[(f,i,l) for f in sorted(glob.glob('src/words*.txt')) for i,l in enumerate(open(f,encoding='utf-8'),1)]
for (fn,ln,raw) in lines:
    ln=f'{fn}:{ln}'
    line=raw.strip()
    if not line: continue
    if line.startswith('## '): sub=line[3:].strip(); continue
    if line.startswith('# '): cat=line[2:].strip(); sub=None; continue
    if line.startswith('#'): continue
    ws=[w.strip() for w in line.split(',') if w.strip()]
    if not cat or not sub: sys.exit(f'line {ln}: cluster before category/subgroup')
    clusters.append((cat,sub,ws,ln)); 
seen={};dups=0;dropped=[];bad=[];groups=collections.OrderedDict();kept=[]
for cat,sub,ws,ln in clusters:   # keep first occurrence of every word; later repeats are removed
    uniq=[]
    for w in ws:
        k=w.lower()
        if k in DROP: dropped.append((w,ln)); continue
        if k in [u.lower() for u in uniq]: dups+=1; continue
        seen[k]=ln; uniq.append(w)
    if len(uniq)<2: bad.append(f'line {ln}: cluster too small after dedupe: {uniq}')
    if len(uniq)>14: bad.append(f'line {ln}: cluster size {len(uniq)}')
    kept.append((cat,sub,uniq,ln)); groups.setdefault((cat,sub),[]).append(uniq)
clusters=kept
print(f'repeats removed: {dups}')
for d in dropped: print(f'DROP  {d[0]!r} line {d[1]}')
for b in bad: print('BAD  ',b)
W=[[c,s,'|'.join(','.join(ws) for ws in lst)] for (c,s),lst in groups.items()]
tpl=open('src/template.html',encoding='utf-8').read()
out=tpl.replace('/*WORDS*/','const W='+json.dumps(W,ensure_ascii=False,separators=(',',':'))+';')
open('index.html','w',encoding='utf-8').write(out)
total=len(seen);pairs=sum(len(ws)*(len(ws)-1)//2 for _,_,ws,_ in clusters)
print('\nPer category (words / clusters / easy>6 / hard<=6):')
pc=collections.defaultdict(lambda:[0,0,0,0])
for cat,sub,ws,_ in clusters:
    p=pc[cat];p[0]+=len(ws);p[1]+=1;p[2]+=len(ws)>6;p[3]+=len(ws)<=6
for c,p in pc.items(): print(f'  {c:18s} {p[0]:6d} {p[1]:5d} {p[2]:5d} {p[3]:5d}')
print(f'\nUNIQUE WORDS: {total}   CLUSTERS: {len(clusters)}   POSSIBLE PAIRS: {pairs}   size: {len(out)//1024} KB')
if dropped or bad: print('** FIX THE ISSUES ABOVE **')
