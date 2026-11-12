# Undercover - pass-and-play word party game

Single-file, offline-capable HTML game modelled on the Undercover word party game. Open `index.html` on one phone and pass it around.

- `index.html` - the game (generated, do not edit by hand)
- `src/template.html` - game UI and logic
- `src/words*.txt` - word bank: `# Category`, `## Subgroup`, then one near-twin cluster per line
- `src/drop.txt` - words banned from the bank
- `build.py` - validates the word bank and builds `index.html`

Rebuild with `python build.py`.
