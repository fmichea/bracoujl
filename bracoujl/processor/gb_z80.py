# gb_z80.py - GameBoy z80 Disassembler + configuration.

import struct
import re

from functools import partial as P

class GBZ80Disassembler:
    def __init__(self):
        def _disassemble_cb(op):
            return self._cb_ops[op // 8] + self._cb_regs[op % 8]
        def r(reg): return '%{reg}'.format(reg=reg)
        def inc_reg(reg):
            a = 'inc {reg}'.format(reg=reg)
            return lambda _: a
        def dec_reg(reg):
            a = 'dec {reg}'.format(reg=reg)
            return lambda _: a
        def push_reg(reg):
            a = 'push {reg}'.format(reg=reg)
            return lambda _: a
        def pop_reg(reg):
            a = 'pop {reg}'.format(reg=reg)
            return lambda _: a
        def ld_a_mreg(reg):
            a = 'ld %a, ({})'.format(reg)
            return lambda _: a
        def ld_mreg_a(reg):
            a = 'ld ({}), %a'.format(reg)
            return lambda _: a
        def call_flag_a16(flag, inst):
            addr = struct.unpack('<H', inst['mem'])[0]
            return 'call {}, $0x{:04X}'.format(flag, addr)
        def jmp_flag_a16(flag, inst):
            addr = struct.unpack('<H', inst['mem'])[0]
            return 'jmp {}, $0x{:04X}'.format(flag, addr)
        def jr_flag_r8(flag, inst):
            addr = struct.unpack('b', inst['mem'][:1])[0]
            return 'jr {}, $0x{:02X} ; (${:d})'.format(flag, addr & 0xff, addr)
        def ret_flag(flag):
            a = 'ret {}'.format(flag)
            return lambda _: a
        def ld_reg_reg(reg1, reg2):
            a = 'ld {reg1}, {reg2}'.format(reg1=reg1, reg2=reg2)
            return lambda _: a
        def op_a_reg(op, reg):
            a = '{} %a, {}'.format(op, reg)
            return lambda _: a
        def rst_nn(nn):
            a = 'rst {:02X}h'.format(nn)
            return lambda _: a
        def jmp_a16(inst):
            addr = struct.unpack('<H', inst['mem'])[0]
            return 'jmp $0x{:04X}'.format(addr)
        def ld_mc_a(_):
            return 'ld ($0xFFF0 + %c), %a'
        def ld_a_mc(_):
            return 'ld %a, ($0xFFF0 + %c)'
        def cb(inst):
            op = inst['mem'][0]
            return 'cb $0x{:02X} ; {}'.format(op, _disassemble_cb(op))
        def call_a16(inst):
            addr = struct.unpack('<H', inst['mem'])[0]
            return 'call $0x{:04X}'.format(addr)
        def jr_r8(inst):
            addr = struct.unpack('b', inst['mem'][:1])[0]
            return 'jr $0x{:02X} ; (${:d})'.format(addr & 0xff, addr)
        def ld_ma16_sp(inst):
            addr = struct.unpack('<H', inst['mem'])[0]
            return 'ld ($0x{:04X}), %sp'.format(addr)
        def ld_reg_d8(reg, inst):
            val = struct.unpack('B', inst['mem'][:1])[0]
            return 'ld {}, $0x{:02X}'.format(reg, val)
        def ld_reg_d16(reg, inst):
            val = struct.unpack('<H', inst['mem'])[0]
            return 'ld {}, $0x{:04X}'.format(reg, val)
        def add_hl_reg(reg):
            a = 'add %hl, {}'.format(reg)
            return lambda _: a
        def ld_ma16_a(inst):
            addr = struct.unpack('<H', inst['mem'])[0]
            return 'ld ($0x{:04X}), %a'.format(addr)
        def ld_a_ma16(inst):
            addr = struct.unpack('<H', inst['mem'])[0]
            return 'ld %a, ($0x{:04X})'.format(addr)
        def ldh_a_ma8(inst):
            addr = inst['mem'][0]
            return 'ldh %a, ($0x{:04X})'.format(0xFF00 + addr)
        def ldh_ma8_a(inst):
            addr = inst['mem'][0]
            return 'ldh ($0x{:04X}), %a'.format(0xFF00 + addr)
        def op_a_d8(op, inst):
            d8 = inst['mem'][0]
            return '{} %a, $0x{}'.format(op, d8)
        def add_sp_r8(inst):
            r8 = struct.unpack('b', inst['mem'][:1])[0]
            return 'add %sp, $0x{:02X} ; (${:d})'.format(r8 & 0xff, r8)
        def ld_hl_sppr8(inst):
            a = struct.unpack('b', inst['mem'][1:])[0]
            return 'ld %hl, %sp + $0x{:02X} ; (${:d})'.format(a & 0xff, a)
        def ld_sp_hl(_):
            return 'ld %sp, %hl'
        def jmp_mhl(_):
            return 'jmp (%hl)'

        self._opcodes = dict()

        # PREFIX CB
        self._cb_ops = []
        self._cb_regs = [r(a) for a in ['b', 'c', 'd', 'e', 'h', 'l']] + ['(%hl)', r('a')]
        for o in ['rlc', 'rrc', 'rl', 'rr', 'sla', 'sra', 'swap', 'srl']:
            self._cb_ops.append(o + ' ')
        for o in ["bit", "res", "set"]:
            for i in range(8):
                self._cb_ops.append(o + ' $' + str(i) + ', ')
        self._opcodes[0xCB] = cb

        # LD (a16), SP
        self._opcodes[0x08] = ld_ma16_sp

        # LDH (a8), A / LDH A, (a8)
        self._opcodes[0xE0] = ldh_ma8_a
        self._opcodes[0xF0] = ldh_a_ma8

        # LD (a16), A / LD A, (a16)
        self._opcodes[0xEA] = ld_ma16_a
        self._opcodes[0xFA] = ld_a_ma16

        # LD SP, HL / LD HL, SP + r8
        self._opcodes[0xF9] = ld_sp_hl
        self._opcodes[0xF8] = ld_hl_sppr8

        # ADD SP, r8
        self._opcodes[0xE8] = add_sp_r8

        # JP (HL)
        self._opcodes[0xE9] = jmp_mhl

        for i, reg in enumerate(['bc', 'de', 'hl']):
            # INC
            self._opcodes[0x10 * i + 0x3] = inc_reg(r(reg))
            self._opcodes[0x10 * i + 0x4] = inc_reg(r(reg[0]))
            self._opcodes[0x10 * i + 0xC] = inc_reg(r(reg[1]))
            # DEC
            self._opcodes[0x10 * i + 0x5] = dec_reg(r(reg[0]))
            self._opcodes[0x10 * i + 0xB] = dec_reg(r(reg))
            self._opcodes[0x10 * i + 0xD] = dec_reg(r(reg[1]))
        # INC
        self._opcodes[0x33] = inc_reg('%sp')
        self._opcodes[0x34] = inc_reg('(%hl)')
        self._opcodes[0x3C] = inc_reg(r('a'))
        # DEC
        self._opcodes[0x35] = dec_reg('(%hl)')
        self._opcodes[0x3B] = dec_reg('%sp')
        self._opcodes[0x3D] = dec_reg(r('a'))

        # PUSH/POP
        for i, reg in enumerate(['bc', 'de', 'hl', 'af']):
            self._opcodes[0xC0 + 0x10 * i + 0x1] = pop_reg(r(reg))
            self._opcodes[0xC0 + 0x10 * i + 0x5] = push_reg(r(reg))

        # ADD/ADC/SUB/SBC/AND/XOR/OR/CP
        for i1, op in enumerate(['add', 'adc', 'sub', 'sbc', 'and', 'xor', 'or', 'cp']):
            for i2, reg in enumerate([r(a) for a in 'bcdehl'] + ['(%hl)', r('a')]):
                self._opcodes[0x80 + 0x8 * i1 + i2] = op_a_reg(op, reg)
            self._opcodes[0xC6 + 0x8 * i1] = P(op_a_d8, op)

        # LD REG, d16
        for i, reg in enumerate(['bc', 'de', 'hl', 'sp']):
            self._opcodes[0x10 * i + 0x1] = P(ld_reg_d16, r(reg))

        # ADD HL, REG
        for i, reg in enumerate(['bc', 'de', 'hl', 'sp']):
            self._opcodes[0x09 + 0x10 * i] = add_hl_reg(r(reg))

        # LD REG, REG / LD REG, d8
        for i1, reg1 in enumerate([r(a) for a in 'bcdehl'] + ['(%hl)', r('a')]):
            for i2, reg2 in enumerate([r(a) for a in 'bcdehl'] + ['(%hl)', r('a')]):
                self._opcodes[0x40 + 0x8 * i1 + i2] = ld_reg_reg(reg1, reg2)
            self._opcodes[0x06 + 0x08 * i1] = P(ld_reg_d8, reg1)

        # LD A, (REG)
        for i, reg in enumerate(['bc', 'de', 'hl+', 'hl-']):
            self._opcodes[0x10 * i + 0x2] = ld_mreg_a(r(reg))
            self._opcodes[0x10 * i + 0xA] = ld_a_mreg(r(reg))

        # LD A, (C) / LD (C), A
        self._opcodes[0xE2] = ld_mc_a
        self._opcodes[0xF2] = ld_a_mc

        # RST
        for i in range(0x00, 0x40, 0x8):
            self._opcodes[0xC7 + i] = rst_nn(i)

        # CALL, JMP, JR
        self._opcodes[0x18] = jr_r8
        self._opcodes[0xC3] = jmp_a16
        self._opcodes[0xCD] = call_a16
        for i, flag in enumerate(['nzf', 'zf', 'ncy', 'cy']):
            self._opcodes[0xC0 + 0x8 * i] = ret_flag(flag)
            self._opcodes[0x20 + 0x8 * i] = P(jr_flag_r8, flag)
            self._opcodes[0xC2 + 0x8 * i] = P(jmp_flag_a16, flag)
            self._opcodes[0xC2 + 0x8 * i + 0x2] = P(call_flag_a16, flag)

        # Simple ops
        for addr, op in [(0x00, 'nop'), (0x10, 'stop'), (0xFB, 'ei'),
                         (0xF3, 'di'), (0x76, 'halt'), (0xC9, 'ret'),
                         (0xD9, 'reti')]:
            self._opcodes[addr] = P(lambda x, _: x, op)
        for i, op in enumerate(['rlca', 'rrca', 'rla', 'rra', 'daa', 'cpl', 'scf', 'ccf']):
            self._opcodes[0x07 + 0x08 * i] = P(lambda x, _: x, op)

    def disassemble(self, inst):
        try:
            return self._opcodes[inst['opcode'][0]](inst)
        except KeyError:
            return '[unknown: {!r}]'.format(inst['opcode'])
        except Exception as e:
            return '[error: {!r} -> {}]'.format(inst['opcode'], str(e))

_RGX = '.*'
_RGX += 'PC: (?P<pc>[0-9A-Fa-f]{4}) \\| '
_RGX += 'OPCODE: (?P<opcode>[0-9A-Fa-f]{2}) \\| '
_RGX += 'MEM: (?P<mem>[0-9A-Fa-f]{4})$'
_LOG_LINE = re.compile(_RGX)

def _parse_line(line):
    m = _LOG_LINE.match(line)
    if m:
        opcode = bytes.fromhex(m.group('opcode'))
        pc = int(m.group('pc'), 16)
        mem = bytes.fromhex(m.group('mem'))
        return {'pc': pc, 'opcode': opcode, 'mem': mem}
    return None

def chrlst(lst): return [struct.pack('B', c) for c in lst]

CPU_CONF = {
    'parse_line': _parse_line,
    'addr_width': 16,
    'opcode_size': 3,
    'interrupts': range(0x0, 0x60 + 1, 0x8),

    'int_opcodes': chrlst(range(0xc7, 0x100, 0x8)),
    'int_opcodes_size': 1,

    'call_opcodes': chrlst([0xc4, 0xcc, 0xcd, 0xd4, 0xdc]),
    'call_opcodes_size': 3,

    'jump_opcodes': chrlst([0xc2, 0xc3, 0xca, 0xd2, 0xda, 0xe9]),
    'jump_opcodes_size': 3,

    'jr_opcodes': chrlst([0x18, 0x20, 0x28, 0x30, 0x38]),
    'jr_opcodes_size': 2,

    'ret_opcodes': chrlst([0xc9, 0xd9, 0xc0, 0xc8, 0xd0, 0xd8]),
    'ret_opcodes_size': 1,

    'disassembler': GBZ80Disassembler,
}
