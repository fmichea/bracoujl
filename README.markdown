bracoujl - Control Flow Analysis
================================

Introduction
------------

This program helps rebuild graphs of the program executed by a CPU. This is
useful when you are writing it and you end up with crashes or unexpected
behavior. If you don't really know where the bug is in your CPU, it will be
hard to follow the execution step by step of your emulator. You could implement
a little debugger for your CPU and try to use it on the ROM, or you could try
this tool. It will show you in a readable format what you executed.

If this README is not easy to read or understand, please shout me an email,
thanks!

### Why use this tool?

#### What will I find out?

This project aims to provide an easier way to debug CPU emulation through
control analysis of it executes. It helps spot a lot of easy-to-make errors,
like:

  - Bad instruction implementations
    * Flags not set correctly on operations (making loops not work as
      expected).
    * Program counter operations not working correctly (relative jumps, call
      not returning correctly).
  - Instructions claiming the wrong size, making the emulator execute wrong
    program.
  - Invalid memory behavior can also be spotted sometimes.

Comparing graphs with another emulator, it also helps find:

  - Find sub functions that never work the same (function that checks a
    register, and your emulator never takes one of the checks? Is the register
    miss-behaving ?)
  - Find synchronization loops and compare how much they are used.

And maybe a lot more.

#### Why can't I just step through my CPU?

First, you really don't want if you don't already know where to search. Within
20 instructions, you'll fall into a loop that copies 512 bytes of data, byte by
byte, in like 4 instructions per byte, then another loop that does it with
anohter 512 bytes, then... You get it.

Also, it will become really painful, really quickly, to follow what call you
are in and what was executed before in that function. Also your CPU will switch
to interrupts all the time, .... So you probably want to try this tool if you
have no idea where to search for.

### What does it support?

It supports:

 - (Conditional) Call backtracking and detection.
 - (Conditional) Jumps detection, with triggering/fall-through edge detection.
 - Interrupts detection.
 - Function and interrupt separation, in multiple files, for readability.
 - Memory changes support (if your ROM executes banked memory, you might
   execute two totally different functions that share the same address).
 - Disassembly support directly in bracoujl if the processor supports it:
    * The emulator you want to see traces from doesn't need to have one.
    * It reduces the amount you need to put in the emulator to have a nice
      render of the graphs. One printf and you get nice results!

### What does the results look like?

They are not all from the last version, but you will basically get those
results.

 - Small function: [[1]](http://kushou.eu/images/pub/bracoujl/demo/sub_0419.svg)
 - Function with inner calls: [[1]](http://kushou.eu/images/pub/bracoujl/demo/sub_0819.svg)
 - Bigger function: [[1]]( http://kushou.eu/images/pub/bracoujl/demo/sub_14AB.svg)
 - Function with a loop and jump detection: [[1]](http://kushou.eu/images/pub/bracoujl/demo/sub_0202.svg)

Game: What is wrong with the second graph? [[1]](http://kushou.eu/images/pub/bracoujl/demo/bbman.sub_0819.good.svg) [[2]](http://kushou.eu/images/pub/bracoujl/demo/bbman.sub_0819.bad.svg)
(It happens after ROM initialization, nothing before it is
interesting/different, FF00 is an IO port to JOYPAD (did I give the answer? :())

How do I use it?
----------------

First thing you need to know is that I wrote it for GameBoy Z80, so this
processor is implemented, BUT it was designed with the fact that you might not
want to use it for this processor, so the process of writing another one is
hopefully easy.

### Example: Using GB z80 processor.

#### Generating and reading graphs.

You must first edit your emulator to log each and every instruction you are
executing. Note: this will most likely slow down your emulator when using it, so
and log A LOT of lines. Mine executes millions of instructions only for the
introduction of the games.

GB z80 defines the format of each lines as `".* PC: $pc | OPCODE: $opcode + MEM:
$mem" ` where:

  - `$pc` is a 4 digit, hexadecimal number being the program number.
  - `$opcode` a 2 digit, hexadecimal number representing the current executed
    opcode.
  - `$mem` a 4 digit, hexadecimal number representing the two bytes following the
    opcode in memory. This is used by diassembler.
  - `.*` can be replaced by anything.

Every line not matching this pattern will be ignored.

Now you need to get the logs of execution of a ROM, example:

    $ mkdir logs
    $ ./myGB roms/game.gb > logs/myGB.game.log

You now have millions of lines of executed instructions. You can try to read
them to understand what the program does, but honestly, you will have a bad
time, this is where bracoujl comes in.

You will first generate SVG files of the functions executed. It will help you
read what you executed.

    $ mkdir myGB.game
    $ bracoujl --svg -o myGB.game{,.log}

The last command may take some minutes, and will report all the functions found
at the end, its output would look like this:

    Found 103 functions in foo.log:
     - sub_53A8
     - sub_1964
     - sub_1E2E
     - int_0050
     - sub_4ABE
     - sub_231E
     - sub_19F9
     - sub_1C6B
     - sub_19C9
     - sub_524F
     - sub_3059
     - sub_53C2
     - sub_1E74
     - sub_2708
     - sub_2D0D
     - sub_1352
     - sub_5038
     - sub_10000S
     [...]
     - sub_533B within the functions sub_4F5D
     - sub_2784 within the functions sub_286F
     - sub_1E67 within the functions sub_1C0A
     - sub_4E76 within the functions sub_4E0B, sub_4F5D

As you can see there is a special function in this list, that as an address
wider than the possible addresses. It is \_start, and should start with a BEGIN
block. The function marked as "within" other functions mean that they don't have
a special file for them, and you should check the files of the function within
which they are.

Now you have nice SVGs graphs, you can move around and read them to find out
what your emulator executes and if the program means anything!

#### Comparing two graphs.

If you have another emulator that can help you debug yours, you could add the
same logging line in it, generate graphs too for it and then generate graphs.
This is a nice idea, but you'll soon notice that it will output a lot of
functions, with a lot of code in them, sooooooo here is a good solution:

Waiiiit, don't kill the SVG generation! You'll need them anyway, so go ahead,
continue generating them! :)


Now you two to sets of functions graphs, you will need a last information: the
comparison between both graphs. Here is how to do it:

    $ bracoujl --cmp reference.game.log myGB.game.log
    Begin comparison of function: sub_294F
    Block loc_2953 is only reached from first function from block sub_294F
    ----------------------------------------
    Begin comparison of function: sub_2D2D
    Block loc_2C96 is only reached from first function from block loc_2C77
    Block loc_0269 is only reached from first function from block loc_2F2B
    Block loc_50AB_7fc006ef2110 is only reached from first function from block
    loc_2F2B
    Block loc_50AB_7fc0068f1910 is only reached from second function from block
    loc_2F2B
    Block loc_2F19 is different in functions sub_2D2D.
    Block loc_2F1A is only reached from first function from block loc_2F19
    Block loc_2B26S is only reached from second function from block loc_2F19
    Block loc_2F26 is only reached from second function from block loc_2F19
    Block loc_0664 is different in functions sub_2D2D.
    Block loc_0664 is only reached from first function from block loc_0664
    Block loc_0668 is only reached from first function from block loc_0664
    Block loc_0666 is only reached from second function from block loc_0664
    Block loc_1913 is different in functions sub_2D2D.
    Block loc_1919 is only reached from first function from block loc_1913
    Block loc_192F is only reached from second function from block loc_1913
    ----------------------------------------
    Begin comparison of function: sub_2B26
    Block loc_2C0E is only reached from first function from block loc_2C04
    Block loc_2C0C is different in functions sub_2B26.
    Block loc_2C0E is only reached from first function from block loc_2C0C
    Block loc_2C18 is only reached from second function from block loc_2C0C
    Block loc_2C96 is only reached from first function from block loc_2C77
    Block loc_0269 is only reached from first function from block loc_2F2B
    Block loc_50AB_7fc006ef2110 is only reached from first function from block
    loc_2F2B
    Block loc_50AB_7fc0068f1910 is only reached from second function from block
    loc_2F2B
    Block loc_2F19 is different in functions sub_2B26.
    Block loc_2F1A is only reached from first function from block loc_2F19
    Block loc_2B26S is only reached from second function from block loc_2F19
    Block loc_2F26 is only reached from second function from block loc_2F19
    Block loc_1913 is different in functions sub_2B26.
    Block loc_1919 is only reached from first function from block loc_1913
    Block loc_192F is only reached from second function from block loc_1913
    Block loc_0664 is different in functions sub_2B26.
    Block loc_0664 is only reached from first function from block loc_0664
    Block loc_0668 is only reached from first function from block loc_0664
    Block loc_0666 is only reached from second function from block loc_0664
    ----------------------------------------
    [...]
    Total error count: 171

For now, there is no serialization so it will generate again both graphs.... but
then it will give you all this information! I think the messages are explicit
enough :)

Notes: non-uniq blocks are not compared correctly for now (the blocks with
another address appended), so they will appear "only reached from". This bug
will hopefully be fixed soon.

### Writing a CPU description.

Please read the current gameboy CPU written in `bracoujl/processor/gb_z80.py`.
What you really need to implement:

  - A function that decides if a line of log is valid or not, and fetches
    information from it.
  - Fill a dictionary named `CPU_CONF` that contains:
    * `parse_line`: the function that parses lines of log.
    * `addr_width`: the width of the address space.
    * `interrupts`: address of the beginning of all the interrupts.
    * `{int,call,jump,jr,ret}_opcodes`: the opcodes for all these instructions,
      conditional or not.
    * `{int,call,jump,jr,ret}_opcodes_size`: the size of respective
      instructions.

Additionally, you can add a `disassembler`, check the one in GameBoy z80 CPU :)

Other informations
------------------

* Example of result: [1](http://kushou.eu/images/pub/bracoujl/)
* If you see several paths after a call, it probably means the function called
  modifies its return address (for example if it's on the stack).

### Name Votes

Any name containing 'bracoujl' letters (all of them, only once) can be used.
Shout me an email to vote.

 - bracoujl: 100 votes

PS: Those are totally not rigged
