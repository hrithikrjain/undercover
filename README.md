# Undercover - pass-and-play word party game

Single-file, offline-capable HTML game modelled on the Undercover word party game. Open `index.html` on one phone and pass it around.

- `index.html` - the game (generated, do not edit by hand)
- `src/template.html` - game UI and logic
- `src/words*.txt` - vocabulary: `# Category`, `## Subgroup`, then one comma-separated group per line
- `src/score.py` - embeds every word (sentence-transformers) and scores candidate pairs with cosine similarity plus Damerau-Levenshtein; writes `src/candidates.tsv`
- `src/pairs.tsv` - the hand-authored pair list the game uses: category, word a, word b, level (1 easy, 2 medium, 3 hard), why the pair works, and an optional third sibling word used for a second undercover. Every word appears in at most two pairs. Pairs follow the 70/30 rule: high overlap, one sharp describable difference (pancake / waffle, passport / visa). No sibling pairs (country vs country) and no synonyms
- `src/merge_pairs.py` - merges authored pair files, validates them and flags suspicious ones with embeddings
- `src/drop.txt` - words banned from the bank
- `build.py` - validates the word bank and builds `index.html`

Rebuild with `python build.py`.
