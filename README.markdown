bracoujl - Control Flow Analysis
================================

Introduction
------------

First written to help debug my emulator `nebula`, I thought it needed some
improvements that were enough to have its own repository. This script helps to
understand the control flow of a program.

This is really important when writing an emulator, for example. You can trace
what you execute and understand what instructions are not working properly.
Obviously this is my use-case, but you could find another one if you want.

How do I use it?
----------------

Note: The script is completly broken right now (HEAD), please checkout commit
`592fbe74983c...` ([link](https://bitbucket.org/kushou/bracoujl/changeset/592fbe74983c2e0d9b218f5cc8a1db81))
to get the last working script.

This script is in heavy developement, so these instructions can break any day
now. But here is a idea of how it works:

Format of the logs (this will probably change soon, to be more configurable):

* On one line: `[HEX_NUMBER] Opcode : HEX_NUMBER, PC : HEX_NUMBER`.
    * Opcode should be 2 digits. (for now)
    * PC should be 4 digits. (for now)
* Optionnally, if you want to add a disassembly: `[HEX_NUMBER] DISASS`.
    * HEX\_NUMBER should be PC.
    * DISASS can be any string.

To generate a graph from logs:

* `python2 bracoujl --dotify --input my_logs.logs --output my_logs.dot`
* `dot -Tsvg my_logs.dot -o my_logs.svg`
* Enjoy you graph watching with `eog` or whatever.

To compare two graphs:

* `python2 bracoujl --compare --input my_logs.logs --input my_logs2.logs`

You can serialize logs to avoid loading them each time with `-s` option, see
`--help` for other options.

Other informations
------------------

* Example of result: [1](http://kushou.eu/images/nebula.svg)
* If you see several paths after a call, it probably means the function called
  modifies its return address (for example if it's on the stack).
* Could be named `jarbocul`, you can vote! (I just don't know how)
