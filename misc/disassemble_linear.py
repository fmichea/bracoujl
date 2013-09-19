import sys
import time
import bracoujl.processor.gb_z80 as proc

dis = proc.CPU_CONF['disassembler']()

def disassemble(lines):
    res = ''
    for line in lines:
        op = proc.CPU_CONF['parse_line'](line)
        if op is None:
            continue
        res += '{:04X}'.format(op['pc']) + ' - ' + dis.disassemble(op) + '\n'
    res += '-' * 30
    return res

try:
    N = int(sys.argv[1])
except (ValueError, IndexError):
    N = -1

uniq, lines, count = set(), [], 0
for line in sys.stdin:
    if line == '--\n':
        tlines = disassemble(lines)
        if tlines not in uniq:
            uniq.add(tlines)
            print(tlines)
        lines = []
        if N == count:
            sys.exit(0)
        count += 1
    lines.append(line[:-1])
