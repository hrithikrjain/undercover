"""Build index.html from src/template.html + src/pairs.tsv.

src/pairs.tsv: category <TAB> word a <TAB> word b <TAB> level (1 easy, 2 medium, 3 hard) [<TAB> reason]
Pairs are hand-authored to the 70/30 rule (src/merge_pairs.py merges and sanity-checks them).
"""
import json, sys, collections, io
DROP = [w.strip().lower() for w in open('src/drop.txt', encoding='utf-8') if w.strip() and not w.startswith('#')]
pairs = []; seen = set(); bad = []
for i, ln in enumerate(io.open('src/pairs.tsv', encoding='utf-8'), 1):
    ln = ln.rstrip('\n')
    if not ln.strip() or ln.startswith('#'): continue
    f = ln.split('\t')
    if len(f) not in (4, 5): bad.append(f'line {i}: expected 4 or 5 columns: {ln!r}'); continue
    cat, a, b, lvl = f[0].strip(), f[1].strip().lower(), f[2].strip().lower(), f[3].strip()
    if lvl not in '123' or not lvl: bad.append(f'line {i}: level must be 1/2/3'); continue
    if a in DROP or b in DROP: bad.append(f'line {i}: dropped word {a!r}/{b!r}'); continue
    if a == b: bad.append(f'line {i}: words identical {a!r}'); continue
    k = (cat, *sorted((a, b)))
    if k in seen: continue
    seen.add(k); pairs.append((cat, a, b, int(lvl)))
for b in bad: print('BAD  ', b)
groups = collections.OrderedDict()
for cat, a, b, l in pairs: groups.setdefault(cat, []).append(f'{a}|{b}|{l}')
P = [[c, ';'.join(v)] for c, v in groups.items()]
tpl = open('src/template.html', encoding='utf-8').read()
out = tpl.replace('/*WORDS*/', 'const P=' + json.dumps(P, ensure_ascii=False, separators=(',', ':')) + ';')
open('index.html', 'w', encoding='utf-8').write(out)
words = {w for _, a, b, _ in pairs for w in (a, b)}
print('\nPer category (pairs / easy / medium / hard):')
pc = collections.defaultdict(lambda: [0, 0, 0, 0])
for cat, a, b, l in pairs: p = pc[cat]; p[0] += 1; p[l] += 1
for c, p in pc.items(): print(f'  {c:18s} {p[0]:6d} {p[1]:5d} {p[2]:5d} {p[3]:5d}')
print(f'\nUNIQUE WORDS: {len(words)}   PAIRS: {len(pairs)}   size: {len(out)//1024} KB')
if bad: print('** FIX THE ISSUES ABOVE **')
