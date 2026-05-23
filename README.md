# Ferrum

This is the (semi)-official Github for the game Ferrum!
Currently, the game is in a very early development stage.

## The Game
Ferrum is going to be a 2D metroidvania game, with an art/story inclination to ancient Japanese myth.
The name is called Ferrum, as it is going to have game combat and story centered around a god of metal, and ferrum is iron in Latin.

We hope to see this repo grow.

## Quick start

1. Install pygame (Python 3.10+):
   `pip install pygame`
2. Run the demo:
   `python main.py`
3. Open the world editor:
   `python main.py --edit levels/lv1.world`

## World Editor

The editor writes Ferrum world files using run-length encoding. Save with `Ctrl+S`, then run the game again to let it decode and compile the updated `.world` into the cached JSON the first time it is loaded. Old uncompressed `.txt` levels can still be loaded by the converter if needed, but new saves use `.world`.

<hr>

&copy; 2026, Vishesh Kudva and Ayden Lim. All rights reserved.
