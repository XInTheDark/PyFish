<div align="center">

  <h3>PyFish</h3>

  Stockfish in Python...?!

</div>

## Overview

[PyFish][website-link] is a **free UCI chess engine** derived from,
although probably much weaker than, [Stockfish][sf-link]. It aims to port most of the
concepts found in Stockfish into Python.

Currently, many features might be missing, including:
- many search details found in Stockfish
- minor features that gain little Elo in Stockfish 
- NNUE evaluation
- optimizations/speedups found in Stockfish

Additionally, this project uses the existing python-chess library for fundamental functions
such as board representation and move generation.

PyFish **does not include a graphical user interface** (GUI) that is required
to display a chessboard and to make it easy to input moves. These GUIs are
developed independently from PyFish and are available online.


## Files

This distribution of PyFish consists of the following files:

  * [README.md][readme-link], the file you are currently reading.

  * [LICENSE][license-link], a text file containing the GNU General Public
    License version 3.

  * [AUTHORS][authors-link], a text file with the list of authors for the project.

  * [src][src-link], a subdirectory containing the full source code. 


## The UCI protocol

The [Universal Chess Interface][uci-link] (UCI) is a standard text-based protocol
used to communicate with a chess engine and is the recommended way to do so for
typical graphical user interfaces (GUI) or chess tools. PyFish implements the
majority of its options.

Developers can see the default values for the UCI options available in PyFish
by typing `uci` into the engine, but most users should typically use a
chess GUI to interact with PyFish.


## Compiling PyFish

PyFish is written in Python, which means that it is not compiled in the
typical sense. Instead, to use the engine, you can simply run the `main.py` file
found in the `src` directory. However, for Unix-based systems, you can use the
`build.sh` script to create an executable file that is the equivalent.


## Contributing

### Donating hardware

Currently, there is no centralised testing framework for PyFish. As such we do not
accept donations of hardware.

### Improving the code

Please feel free to open Pull Requests for any improvements
you would like to make to the code.

## Terms of use

PyFish is free and distributed under the
[**GNU General Public License version 3**][license-link] (GPL v3). Essentially,
this means you are free to do almost exactly what you want with the program,
including distributing it among your friends, making it available for download
from your website, selling it (either by itself or as part of some bigger
software package), or using it as the starting point for a software project of
your own.

The only real limitation is that whenever you distribute PyFish in some way,
you MUST always include the license and the full source code (or a pointer to
where the source code can be found) to generate the exact binary you are
distributing. If you make any changes to the source code, these changes must
also be made available under GPL v3.


[website-link]: https://github.com/XInTheDark/PyFish
[sf-link]: https://github.com/official-stockfish/Stockfish
[readme-link]: https://github.com/XInTheDark/PyFish/blob/master/README.md
[license-link]: https://github.com/XInTheDark/PyFish/blob/master/LICENSE
[authors-link]: https://github.com/XInTheDark/PyFish/blob/master/AUTHORS
[src-link]: https://github.com/XInTheDark/PyFish/blob/master/src
[uci-link]: https://backscattering.de/chess/uci/