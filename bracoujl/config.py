# config.py - Some data needed in some places.
# Author: Franck Michea < franck.michea@gmail.com >
# License: New BSD License (See LICENSE)

import re

CALL_OPCODES = [0xC4, 0xCC, 0xCD, 0xD4, 0xDC]
RST_OPCODES = [0xC7, 0xD7, 0xE7, 0xF7, 0xCF, 0xDF, 0xEF, 0xFF]
JUMP_OPCODES = [0xC2, 0xC3, 0xCA, 0xD2, 0xDA, 0x18, 0x28, 0x38, 0x20, 0x30]

OPCODE = re.compile('.*Opcode : ([0-9A-Fa-f]{2}), PC : ([A-Fa-f0-9]{4})$')
DISASS = re.compile('\[([0-9a-fA-F]+)\] Disass : (.+)$')
INTERRUPT = re.compile('.*Interrupt : ([A-Fa-f0-9]+)$')

BEGIN_ADDR = 0x10000
END_ADDR = 0x10001
