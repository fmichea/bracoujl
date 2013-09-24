import argparse
import sys
import time
import bracoujl.processor.gb_z80 as proc

dis = proc.CPU_CONF['disassembler']()

def disassemble(lines, keep_logs=False):
    res = []
    for line in lines:
        op, gline = proc.CPU_CONF['parse_line'](line), ''
        if keep_logs:
            gline += line + (' | DIS: ' if op is not None else '')
        else:
            gline += '{:04X}'.format(op['pc']) + ' - '
        if op is not None:
            gline += dis.disassemble(op)
        res.append(gline)
    res.append('-' * 20)
    return '\n'.join(res)

uniq = set()
def display_lines(lines, **kwds):
    tlines = disassemble(lines, **kwds)
    if tlines not in uniq:
        uniq.add(tlines)
        print(tlines)
    return []

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Little disassembly helper.')
    parser.add_argument('-N', action='store', default=-1,
                        help='number of uniq blocks displayed')
    parser.add_argument('-k', '--keep-logs', action='store_true', default=False,
                        help='keep log lines')
    args = parser.parse_args(sys.argv[1:])

    lines, count = [], 0
    for line in sys.stdin:
        if line == '--\n':
            lines = display_lines(lines, keep_logs=args.keep_logs)
            if args.N == count:
                sys.exit(0)
            count += 1
        lines.append(line[:-1])

    if lines:
        display_lines(lines, keep_logs=args.keep_logs)
