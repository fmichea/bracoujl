# gb_z80.py - GameBoy z80 Disassembler + configuration.

import struct

class GBZ80Disassembler:
    def __init__(self):
        def _disassemble_cb(op):
            return 'TODO'
        def r(reg): return '%{reg}'.format(reg=reg)
        def inc_reg(reg):
            return 'inc {reg}'.format(reg=reg)
        def dec_reg(reg):
            return 'dec {reg}'.format(reg=reg)
        def push_reg(reg):
            return 'push {reg}'.format(reg=reg)
        def pop_reg(reg):
            return 'pop {reg}'.format(reg=reg)
        def ld_a_mreg(reg):
            return 'ld %a, ({})'.format(reg)
        def ld_mreg_a(reg):
            return 'ld ({}), %a'
        def call_flag_a16(flag, inst):
            addr = struct.unpack('<H', inst['mem'])
            return 'call {}, $0x{:04X}'.format(flag, addr)
        def jmp_flag_a16(flag, inst):
            addr = struct.unpack('<H', inst['mem'])
            return 'jmp {}, $0x{:04X}'.format(flag, addr)
        def jr_flag_r8(flag, inst):
            addr = struct.unpack('b', inst['mem'][:1])
            return 'jr {}, $0x{:02X} ; (${:d})'.format(flag, addr & 0xff, addr)
        def ret_flag(flag):
            return 'ret {}'
        def ld_reg_reg(reg1, reg2):
            return 'ld {reg1}, {reg2}'.format(reg1=reg1, reg2=reg2)
        def op_a_reg(op, reg):
            return '{} %a, {}'
        def rst_nn(nn):
            return 'rst {02X}h'.format(nn)
        def jmp_a16(inst):
            addr = struct.unpack('<H', inst['mem'])
            return 'jmp $0x{:04X}'.format(addr)
        def ld_mc_a():
            return 'ld ($0xFFF0 + %c), %a'
        def ld_a_mc():
            return 'ld %a, ($0xFFF0 + %c)'
        def cb(inst):
            op = inst['mem'][0]
            return 'cb $0x{:02X} ; {}'.format(op, _disassemble_cb(op))
        def call_a16(inst):
            addr = struct.unpack('<H', inst['mem'])
            return 'call $0x{:04X}'.format(addr)
        def jr_r8(inst):
            addr = struct.unpack('b', inst['mem'][:1])
            return 'jr $0x{:02X} ; (${:d})'.format(addr & 0xff, addr)
        def ld_ma16_sp(inst):
            addr = struct.unpack('<H', inst['mem'])
            return 'ld ($0x{:04X}), %sp'.format(addr)
        def ld_reg_d8(reg, inst):
            val = struct.unpack('b', inst['mem'][:1])
            return 'ld {}, $0x{:02X}'.format(reg, val)
        def ld_reg_d16(reg, inst):
            val = struct.unpack('<H', inst['mem'])
            return 'ld {}, $0x{:04X}'.format(reg, val)
        def add_hl_reg():
            return 'add %hl, {}'.format(reg)
        def ld_ma16_a(inst):
            addr = struct.unpack('<H', inst['mem'])
            return 'ld ($0x{:04X}), %a'.format(addr)
        def ld_a_ma16(inst):
            addr = struct.unpack('<H', inst['mem'])
            return 'ld %a, ($0x{:04X})'.format(addr)
        def ldh_a_ma8(inst):
            addr = inst['mem'][0]
            return 'ldh %a, ($0x{:04X})'.format(0xFF00 + addr)
        def ldh_ma8_a(inst):
            addr = inst['mem'][0]
            return 'ldh ($0x{:04X}), %a'.format(0xFF00 + addr)
#        return '{} %hl'
        def op_a_d8(op, inst):
            d8 = inst['mem'][0]
            return '{} %a, $0x{}'.format(op, d8)
        def add_sp_r8(inst):
            r8 = struct.unpack('b', inst['mem'][:1])
            return 'add %sp, $0x{:02X} ; (${:d})'.format(r8 & 0xff, r8)
        def ld_hl_sppr8(inst):
            a = struct.unpack('b', inst['mem'][1:])
            return 'ld %hl, %sp + $0x{:02X} ; (${:d})'.format(a & 0xff, a)
        def ld_sp_hl():
            return 'ld %sp, %hl'
        def jmp_mhl():
            return 'jmp (%hl)'

        self._opcodes = dict()

        # PREFIX CB
        self._opcodes[0xCB] = lambda inst: cb(inst)

        # LD (a16), SP
        self._opcodes[0x08] = lambda inst: ld_ma16_sp(inst)

        # LDH (a8), A / LDH A, (a8)
        self._opcodes[0xE0] = lambda inst: ldh_ma8_a(inst)
        self._opcodes[0xF0] = lambda inst: ldh_a_ma8(inst)

        # LD (a16), A / LD A, (a16)
        self._opcodes[0xEA] = lambda inst: ld_ma16_a(inst)
        self._opcodes[0xFA] = lambda inst: ld_a_ma16(inst)

        # LD SP, HL / LD HL, SP + r8
        self._opcodes[0xF9] = lambda _: ld_sp_hl()
        self._opcodes[0xF8] = lambda inst: ld_hl_sppr8(inst)

        # ADD SP, r8
        self._opcodes[0xE8] = lambda inst: add_sp_r8(inst)

        # JP (HL)
        self._opcodes[0xE9] = lambda _: jmp_mhl()

        for i, reg in enumerate(['bc', 'de', 'hl']):
            # INC
            self._opcodes[0x10 * i + 0x3] = lambda _: inc_reg(r(reg))
            self._opcodes[0x10 * i + 0x4] = lambda _: inc_reg(r(reg[0]))
            self._opcodes[0x10 * i + 0xC] = lambda _: inc_reg(r(reg[1]))
            # DEC
            self._opcodes[0x10 * i + 0x5] = lambda _: dec_reg(r(reg[0]))
            self._opcodes[0x10 * i + 0xB] = lambda _: dec_reg(r(reg))
            self._opcodes[0x10 * i + 0xD] = lambda _: dec_reg(r(reg[1]))
        # INC
        self._opcodes[0x33] = lambda _: inc_reg('%sp')
        self._opcodes[0x34] = lambda _: inc_reg('(%hl)')
        self._opcodes[0x3C] = lambda _: inc_reg(r('a'))
        # DEC
        self._opcodes[0x35] = lambda _: dec_reg('(%hl)')
        self._opcodes[0x3B] = lambda _: dec_reg('%sp')
        self._opcodes[0x3D] = lambda _: dec_reg(r('a'))

        # PUSH/POP
        for i, reg in enumerate(['bc', 'de', 'hl', 'af']):
            self._opcodes[0xC0 + 0x10 * i + 0x1] = lambda _: pop_reg(r(reg))
            self._opcodes[0xC0 + 0x10 * i + 0x5] = lambda _: push_reg(r(reg))

        # ADD/ADC/SUB/SBC/AND/XOR/OR/CP
        for i1, op in enumerate(['add', 'adc', 'sub', 'sbc', 'and', 'xor', 'or', 'cp']):
            for i2, reg in enumerate([r(a) for a in 'bcdehl'] + ['(%hl)', r('a')]):
                self._opcodes[0x80 + 0x8 * i1 + i2] = lambda _: op_a_reg(op, reg)
            self._opcodes[0xC6 + 0x8 * i1] = lambda inst: op_a_d8(op, inst)

        # LD REG, d16
        for i, reg in enumerate(['bc', 'de', 'hl', 'sp']):
            self._opcodes[0x10 * i + 0x1] = lambda inst: ld_reg_d16(r(reg), inst)

        # ADD HL, REG
        for i, reg in enumerate(['bc', 'de', 'hl', 'sp']):
            self._opcodes[0x09 + 0x10 * i] = lambda _: add_hl_reg(r(reg))

        # LD REG, REG / LD REG, d8
        for i1, reg1 in enumerate([r(a) for a in 'bcdehl'] + ['(%hl)', r('a')]):
            for i2, reg2 in enumerate([r(a) for a in 'bcdehl'] + ['(%hl)', r('a')]):
                self._opcodes[0x40 + 0x8 * i1 + i2] = lambda _: ld_reg_reg(reg1, reg2)
            self._opcodes[0x06 + 0x08 * i1] = lambda inst: ld_reg_d8(reg, inst)

        # LD A, (REG)
        for i, reg in enumerate(['bc', 'de', 'hl+', 'hl-']):
            self._opcodes[0x10 * i + 0x2] = lambda _: ld_mreg_a(r(reg))
            self._opcodes[0x10 * i + 0xA] = lambda _: ld_a_mreg(r(reg))

        # LD A, (C) / LD (C), A
        self._opcodes[0xE2] = lambda _: ld_mc_a()
        self._opcodes[0xF2] = lambda _: ld_a_mc()

        # RST
        for i in range(0x00, 0x40, 0x8):
            self._opcodes[0xC7 + i] = lambda _: rst_nn(i)

        # CALL, JMP, JR
        self._opcodes[0x18] = lambda inst: jr_r8(inst)
        self._opcodes[0xC3] = lambda inst: jmp_a16(inst)
        self._opcodes[0xCD] = lambda inst: call_a16(inst)
        for i, flag in enumerate(['nzf', 'zf', 'ncy', 'cy']):
            self._opcodes[0xC0 + 0x8 * i] = lambda _: ret_flag(flag)
            self._opcodes[0x20 + 0x8 * i] = lambda inst: jr_flag_r8(flag, inst)
            self._opcodes[0xC2 + 0x8 * i] = lambda inst: jmp_flag_a16(flag, inst)
            self._opcodes[0xC2 + 0x8 * i + 0x2] = lambda inst: call_flag_a16(flag, inst)

        # Simple ops
        for addr, op in [(0x00, 'nop'), (0x10, 'stop'), (0xFB, 'ei'),
                         (0xF3, 'di'), (0x76, 'halt'), (0xC9, 'ret'),
                         (0xD9, 'reti')]:
            self._opcodes[addr] = lambda _: op
        for i, op in enumerate(['rlca', 'rrca', 'rla', 'rra', 'daa', 'cpl', 'scf', 'ccf']):
            self._opcodes[0x07 + 0x08 * i] = lambda _: op

    def disassemble(self, inst):
        try:
            return self._opcodes[inst['opcode'][0]](inst)
        except KeyError:
            return '[unknown: {!r}]'.format(inst['opcode'])

_RGX = '.*'
_RGX += 'PC: (?<pc>[A-Fa-f0-9]{4}) | '
_RGX += 'OPCODE: (?<opcode>[0-9A-Fa-f]{2}) | '
_RGX += 'MEM: (?<mem>[0-9A-Fa-f]{4})$'
_LOG_LINE = re.compile(_RGX)

def _parse_line(line):
    m = _LOG_LINE.match(line)
    if m:
        opcode = bytes.fromhex(m.group('opcode'))
        pc = int(m.group('pc'), 16)
        mem = bytes.fromhex(m.group('mem'))
        return {'pc': pc, 'opcode': opcode, 'mem': mem}
    return None

CPU_CONF = {
    'parse_line': _parse_line,
    'addr_width': 16,
    'opcode_size': 3,
    'interrupts': range(0x0, 0x60 + 1, 0x8),
    'call_opcodes': [0xc4, 0xcc, 0xcd, 0xd4, 0xdc],
    'call_opcodes_size': 3,
    'jump_opcodes': [0xc2, 0xc3, 0xca, 0xd2, 0xda, 0xe9] + \    # JMP
                    [0x18, 0x20, 0x28, 0x30, 0x38],             # JR
    'jump_opcodes_size': 3,
    'ret_opcodes': [0xc9, 0xd9, 0xC0, 0xc8, 0xd0, 0xd8],
    'ret_opcodes_size': 1,
    'disassembler': GBZ80Disassembler,
}
