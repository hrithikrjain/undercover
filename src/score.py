"""Score candidate word pairs for the Undercover game.

Reads src/words*.txt (category / subgroup / comma clusters), embeds every word with a
sentence-transformer model, and writes src/candidates.tsv with one line per candidate pair:
    category <tab> a <tab> b <tab> cosine <tab> dl_sim <tab> source
where source is 'cluster' (same cluster) or 'knn' (nearest neighbour inside the category).
Damerau-Levenshtein similarity is used to reject spelling variants / substrings (same word twice).
"""
import glob, io, os, sys, itertools
import numpy as np
from rapidfuzz.distance import DamerauLevenshtein as DL
from sentence_transformers import SentenceTransformer

MODEL = os.environ.get('UC_MODEL', 'sentence-transformers/all-mpnet-base-v2')
KNN = 6            # neighbours per word inside its category
MIN_COS = 0.45     # drop anything below this
MAX_DL = 0.80      # reject near-identical spellings
EXCL = {'After Dark'}  # keep After Dark pairs strictly within clusters (no cross-cluster mixing)

words = {}   # (cat, word) -> set of cluster ids
clusters = []  # (cat, [words])
for f in sorted(glob.glob('src/words*.txt')):
    cat = None
    for ln in io.open(f, encoding='utf-8'):
        ln = ln.strip()
        if ln.startswith('# '): cat = ln[2:].strip(); continue
        if not ln or ln.startswith('#'): continue
        ws = [w.strip() for w in ln.split(',') if w.strip()]
        cid = len(clusters); clusters.append((cat, ws))
        for w in ws: words.setdefault((cat, w), set()).add(cid)

keys = sorted(words)
texts = [w for _, w in keys]
print('words', len(keys), 'clusters', len(clusters), 'model', MODEL, file=sys.stderr)
model = SentenceTransformer(MODEL)
E = model.encode(texts, batch_size=128, normalize_embeddings=True, show_progress_bar=True)
idx = {k: i for i, k in enumerate(keys)}

def too_close(a, b):
    if a == b: return True
    if a in b or b in a: return True
    ta, tb = set(a.split()), set(b.split())
    if ta & tb: return True              # share a whole token: "mango" / "mango juice"
    return DL.normalized_similarity(a, b) > MAX_DL

cands = {}
def add(cat, a, b, src):
    if a > b: a, b = b, a
    if too_close(a, b): return
    cos = float(E[idx[(cat, a)]] @ E[idx[(cat, b)]])
    if cos < MIN_COS: return
    k = (cat, a, b)
    if k not in cands or src == 'cluster':
        cands[k] = (cos, DL.normalized_similarity(a, b), src if k not in cands else 'cluster')

for cat, ws in clusters:
    for a, b in itertools.combinations(ws, 2): add(cat, a, b, 'cluster')

cats = sorted({c for c, _ in keys})
for cat in cats:
    if cat in EXCL: continue
    ids = [i for i, (c, _) in enumerate(keys) if c == cat]
    M = E[ids]; S = M @ M.T
    for r, i in enumerate(ids):
        order = np.argsort(-S[r])[1:KNN + 1]
        for c in order: add(cat, keys[i][1], keys[ids[c]][1], 'knn')

with io.open('src/candidates.tsv', 'w', encoding='utf-8') as out:
    for (cat, a, b), (cos, dl, src) in sorted(cands.items(), key=lambda x: -x[1][0]):
        out.write(f'{cat}\t{a}\t{b}\t{cos:.3f}\t{dl:.2f}\t{src}\n')
print('candidates', len(cands), file=sys.stderr)
