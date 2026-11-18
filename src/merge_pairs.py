"""Merge hand-authored pair files into src/pairs.tsv and sanity-check them.

usage: python src/merge_pairs.py <dir with *.tsv>
Each input line: category<TAB>a<TAB>b<TAB>level<TAB>reason
Checks: format, allowed categories, DROP list, duplicate pairs, words used in >2 pairs,
and (if sentence-transformers is installed) flags pairs whose embedding cosine is very low
(probably unrelated) or very high (probably synonyms) for a human look.
"""
import sys, io, glob, re, collections
from rapidfuzz.distance import DamerauLevenshtein as DL
CATS = {'Food', 'Things', 'Places', 'People & Fun', 'Animals & Nature', 'Mind & Body', 'World & Culture', 'After Dark'}
DROP = {w.strip().lower() for w in io.open('src/drop.txt', encoding='utf-8') if w.strip() and not w.startswith('#')}
BRANDS = set('''maggi coke pepsi uber ola swiggy zomato netflix instagram whatsapp youtube google amazon flipkart paytm
iphone ipad samsung oyo tinder bumble kingfisher budweiser old monk marlboro gold flake dairy milk kitkat oreo lays kurkure
bisleri horlicks bournvita colgate dettol vicks crocin band aid barbie lego uno monopoly ludo king bgmi pubg jio airtel
bollywood hollywood'''.split('\n')) if False else set()
rows = []; bad = []
for f in sorted(glob.glob(sys.argv[1] + '/*.tsv')):
    for i, ln in enumerate(io.open(f, encoding='utf-8'), 1):
        ln = ln.rstrip('\n')
        if not ln.strip(): continue
        p = [x.strip() for x in ln.split('\t')]
        if len(p) < 4: bad.append(f'{f}:{i} too few columns: {ln!r}'); continue
        cat, a, b, lv = p[0], p[1].lower(), p[2].lower(), p[3]
        reason = p[4] if len(p) > 4 else ''
        if cat not in CATS: bad.append(f'{f}:{i} bad category {cat!r}'); continue
        if lv not in ('1', '2', '3'): bad.append(f'{f}:{i} bad level {lv!r}'); continue
        if not re.fullmatch(r"[a-z0-9' ]{2,30}", a) or not re.fullmatch(r"[a-z0-9' ]{2,30}", b):
            bad.append(f'{f}:{i} bad word chars {a!r}/{b!r}'); continue
        if a in DROP or b in DROP: bad.append(f'{f}:{i} dropped word {a!r}/{b!r}'); continue
        if a == b or DL.normalized_similarity(a, b) > 0.92:
            bad.append(f'{f}:{i} words too alike {a!r}/{b!r}'); continue
        rows.append((cat, a, b, int(lv), reason, f'{f}:{i}'))
seen = set(); out = []
for r in rows:
    k = tuple(sorted((r[1], r[2])))
    if k in seen: continue
    seen.add(k); out.append(r)
use = collections.Counter(w for r in out for w in (r[1], r[2]))
over = [(w, n) for w, n in use.items() if n > 3]
for b in bad: print('BAD ', b)
print(f'read {len(rows)}  unique pairs {len(out)}  words used >3 times: {over[:20]}')
lv = collections.Counter(r[3] for r in out); print('levels', dict(sorted(lv.items())))
pc = collections.Counter(r[0] for r in out); print('per category', dict(pc))
try:
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
    E = m.encode([r[1] for r in out] + [r[2] for r in out], normalize_embeddings=True, batch_size=128)
    n = len(out); cos = (E[:n] * E[n:]).sum(1)
    print('\nLOW similarity (possibly unrelated, cos<0.30):')
    for r, c in sorted(zip(out, cos), key=lambda x: x[1]):
        if c < 0.30: print(f'  {c:.2f} {r[0][:8]:8} {r[1]} / {r[2]}  — {r[4]}')
    print('\nHIGH similarity (possibly synonyms, cos>0.85):')
    for r, c in sorted(zip(out, cos), key=lambda x: -x[1]):
        if c > 0.85: print(f'  {c:.2f} {r[0][:8]:8} {r[1]} / {r[2]}  — {r[4]}')
except ImportError:
    print('(sentence-transformers not installed; skipping similarity flags)')
with io.open('src/pairs.tsv', 'w', encoding='utf-8') as fo:
    fo.write('# category\tword a\tword b\tlevel (1 easy, 2 medium, 3 hard)\twhy the pair works\n')
    for r in sorted(out): fo.write(f'{r[0]}\t{r[1]}\t{r[2]}\t{r[3]}\t{r[4]}\n')
print('\nwrote src/pairs.tsv')
