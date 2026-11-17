# Undercover - pass-and-play word party game

Single-file, offline-capable HTML game modelled on the Undercover word party game. Open `index.html` on one phone and pass it around.

- `index.html` - the game (generated, do not edit by hand)
- `src/template.html` - game UI and logic
- `src/words*.txt` - vocabulary: `# Category`, `## Subgroup`, then one comma-separated group per line
- `src/score.py` - embeds every word (sentence-transformers) and scores candidate pairs with cosine similarity plus Damerau-Levenshtein; writes `src/candidates.tsv`
- `src/pairs.tsv` - the reviewed pair list the game actually uses: category, word a, word b, level (1 easy, 2 medium, 3 hard)
- `src/drop.txt` - words banned from the bank
- `build.py` - validates the word bank and builds `index.html`

Rebuild with `python build.py`.
