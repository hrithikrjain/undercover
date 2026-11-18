"""Merge hand-authored pair files into src/pairs.tsv and sanity-check them.

usage: python src/merge_pairs.py <dir with *.tsv> [--append] [--cap N]
Each input line: category<TAB>a<TAB>b<TAB>level<TAB>reason[<TAB>third word]
--append keeps the pairs already in src/pairs.tsv and adds the new ones after them.
Checks: format, allowed categories, DROP list, duplicate pairs (either order, any category),
subset pairs (every token of one word inside the other: tea / green tea), spelling twins,
and a per-word cap (default 3 pairs per word counting a and b).
If sentence-transformers is installed, pairs with very low / very high cosine are flagged for a look.
"""
import sys, io, glob, re, collections
from rapidfuzz.distance import DamerauLevenshtein as DL
CATS = {'Food', 'Things', 'Places', 'People & Fun', 'Animals & Nature', 'Mind & Body', 'World & Culture', 'After Dark'}
DROP = {w.strip().lower() for w in io.open('src/drop.txt', encoding='utf-8') if w.strip() and not w.startswith('#')}
args = sys.argv[1:]; APPEND = '--append' in args
CAP = int(args[args.index('--cap') + 1]) if '--cap' in args else 3
src = [a for a in args if not a.startswith('--') and not a.isdigit()][0]
WORD = re.compile(r"[a-z0-9' ]{2,30}")
def canon(w):
    w = w.lower().strip(); w = re.sub(r'\s+', ' ', w)
    return w.replace('saree', 'sari')
def subset(a, b):
    ta, tb = set(a.split()), set(b.split())
    return ta <= tb or tb <= ta or a in b or b in a

out = []; bad = []; seen = set(); use = collections.Counter()
def take(cat, a, b, lv, reason, c, where):
    k = tuple(sorted((a, b)))
    if k in seen: bad.append(f'{where} duplicate pair {a!r}/{b!r}'); return
    if use[a] >= CAP or use[b] >= CAP: bad.append(f'{where} word cap: {a!r}/{b!r}'); return
    seen.add(k); use[a] += 1; use[b] += 1
    out.append((cat, a, b, lv, reason, c))

if APPEND:
    for i, ln in enumerate(io.open('src/pairs.tsv', encoding='utf-8'), 1):
        if not ln.strip() or ln.startswith('#'): continue
        p = (ln.rstrip('\n').split('\t') + [''] * 6)[:6]
        take(p[0], p[1], p[2], int(p[3]), p[4], p[5], f'pairs.tsv:{i}')
    base = len(out)
else: base = 0

for f in sorted(glob.glob(src + '/*.tsv')):
    for i, ln in enumerate(io.open(f, encoding='utf-8'), 1):
        ln = ln.rstrip('\n')
        if not ln.strip() or ln.startswith('#'): continue
        p = [x.strip() for x in ln.split('\t')]
        if len(p) < 4: bad.append(f'{f}:{i} too few columns: {ln!r}'); continue
        cat, a, b, lv = p[0], canon(p[1]), canon(p[2]), p[3]
        reason = p[4] if len(p) > 4 else ''; c = canon(p[5]) if len(p) > 5 else ''
        if cat not in CATS: bad.append(f'{f}:{i} bad category {cat!r}'); continue
        if lv not in ('1', '2', '3'): bad.append(f'{f}:{i} bad level {lv!r}'); continue
        if not WORD.fullmatch(a) or not WORD.fullmatch(b) or (c and not WORD.fullmatch(c)):
            bad.append(f'{f}:{i} bad word chars {a!r}/{b!r}/{c!r}'); continue
        if a in DROP or b in DROP or c in DROP: bad.append(f'{f}:{i} dropped word {a!r}/{b!r}/{c!r}'); continue
        if a == b or c in (a, b): bad.append(f'{f}:{i} same word twice {a!r}/{b!r}/{c!r}'); continue
        if subset(a, b): bad.append(f'{f}:{i} subset pair {a!r}/{b!r}'); continue
        if DL.normalized_similarity(a, b) > 0.92: bad.append(f'{f}:{i} spelling twins {a!r}/{b!r}'); continue
        if c and (subset(a, c) or subset(b, c)): c = ''
        take(cat, a, b, int(lv), reason, c, f'{f}:{i}')

for b in bad: print('BAD ', b)
print(f'\nrejected {len(bad)}  kept {len(out)} ({len(out) - base} new)')
print('levels', dict(sorted(collections.Counter(r[3] for r in out).items())))
print('per category', dict(collections.Counter(r[0] for r in out)))
print('word use', dict(sorted(collections.Counter(use.values()).items())), 'unique words', len(use))
new = out[base:]
if new and '--nosim' not in args:
    try:
        from sentence_transformers import SentenceTransformer
        m = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
        E = m.encode([r[1] for r in new] + [r[2] for r in new], normalize_embeddings=True, batch_size=128)
        n = len(new); cos = (E[:n] * E[n:]).sum(1)
        print('\nLOW similarity (possibly unrelated, cos<0.30):')
        for r, x in sorted(zip(new, cos), key=lambda x: x[1]):
            if x < 0.30: print(f'  {x:.2f} {r[0][:8]:8} {r[1]} / {r[2]}  - {r[4]}')
        print('\nHIGH similarity (possibly synonyms, cos>0.85):')
        for r, x in sorted(zip(new, cos), key=lambda x: -x[1]):
            if x > 0.85: print(f'  {x:.2f} {r[0][:8]:8} {r[1]} / {r[2]}  - {r[4]}')
    except ImportError:
        print('(sentence-transformers not installed; skipping similarity flags)')
with io.open('src/pairs.tsv', 'w', encoding='utf-8') as fo:
    fo.write('# category\tword a\tword b\tlevel (1 easy, 2 medium, 3 hard)\twhy the pair works\tthird word (optional)\n')
    for r in sorted(out): fo.write('\t'.join([r[0], r[1], r[2], str(r[3]), r[4], r[5]]) + '\n')
print('\nwrote src/pairs.tsv')
