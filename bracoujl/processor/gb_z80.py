# gb_z80.py - GameBoy z80 Disassembler + configuration.

import struct

class GBZ80Disassembler:
    def __init__(self):
        def _disassemble_cb(opcode):
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
        def call_flag_a16(flag, opcode):
            addr = struct.unpack('<H', opcode[1:])
            return 'call {}, $0x{:04X}'.format(flag, addr)
        def jmp_flag_a16(flag, opcode):
            addr = struct.unpack('<H', opcode[1:])
            return 'jmp {}, $0x{:04X}'.format(flag, addr)
        def jr_flag_r8(flag, opcode):
            addr = struct.unpack('<b', opcode[1:])
            return 'jr {}, $0x{:02X} ; (${:d})'.format(flag, addr & 0xff, addr)
        def ret_flag(flag):
            return 'ret {}'
        def ld_reg_reg(reg1, reg2):
            return 'ld {reg1}, {reg2}'.format(reg1=reg1, reg2=reg2)
        def op_a_reg(op, reg):
            return '{} %a, {}'
        def rst_nn(nn):
            return 'rst {02X}h'.format(nn)
        def jmp_a16(opcode):
            addr = struct.unpack('<H', opcode[1:])
            return 'jmp $0x{:04X}'.format(addr)
        def ld_mc_a():
            return 'ld ($0xFFF0 + %c), %a'
        def ld_a_mc():
            return 'ld %a, ($0xFFF0 + %c)'
        def cp(opcode):
            return 'cb $0x{:02X} ; TODO'
        def call_a16(opcode):
            addr = struct.unpack('<H', opcode[1:])
            return 'call $0x{:04X}'.format(addr)
        def jr_r8(opcode):
            addr = struct.unpack('b', opcode[1])
            return 'jr $0x{:02X} ; (${:d})'.format(addr & 0xff, addr)
        def ld_ma16_sp(opc):
            addr = struct.unpack('<H', opc[1:])
            return 'ld ($0x{:04X}), %sp'.format(addr)
        def ld_reg_d8(reg, opcode):
            val = struct.unpack('b', opcode[1:])
            return 'ld {}, $0x{:02X}'.format(reg, val)
        def ld_reg_d16(reg, opcode):
            val = struct.unpack('<H', opcode[1:])
            return 'ld {}, $0x{:04X}'.format(reg, val)
        def add_hl_reg():
            return 'add %hl, {}'.format(reg)
        def ld_ma16_a(opcode):
            addr = struct.unpack('<H', opcode[1:])
            return 'ld ($0x{:04X}), %a'.format(addr)
        def ld_a_ma16(opcode):
            addr = struct.unpack('<H', opcode[1:])
            return 'ld %a, ($0x{:04X})'.format(addr)
        def ldh_a_ma8(opcode):
            addr = struct.unpack('B', opcode[1:])
            return 'ldh %a, ($0x{:04X})'.format(0xFF00 + addr)
        def ldh_ma8_a(opcode):
            addr = struct.unpack('B', opcode[1:])
            return 'ldh ($0x{:04X}), %a'.format(0xFF00 + addr)
#        return '{} %hl'
        def op_a_d8(op, opcode):
            d8 = struct.unpack('B', opcode[1:])
            return '{} %a, $0x{}'.format(op, d8)
        def add_sp_r8(opcode):
            r8 = struct.unpack('b', opcode[1:])
            return 'add %sp, $0x{:02X} ; (${:d})'.format(r8 & 0xff, r8)
        def ld_hl_sppr8(opcode):
            a = struct.unpack('b', opcode[1:])
            return 'ld %hl, %sp + $0x{:02X} ; (${:d})'.format(a & 0xff, a)
        def ld_sp_hl():
            return 'ld %sp, %hl'
        def jmp_mhl():
            return 'jmp (%hl)'

        self._opcodes = dict()

        # PREFIX CB
        self._opcodes[0xCB] = lambda _, mem: cb(mem)

        # LD (a16), SP
        self._opcodes[0x08] = lambda _, mem: ld_ma16_sp(mem)

        # LDH (a8), A / LDH A, (a8)
        self._opcodes[0xE0] = lambda _, mem: ldh_ma8_a(mem)
        self._opcodes[0xF0] = lambda _, mem: ldh_a_ma8(mem)

        # LD (a16), A / LD A, (a16)
        self._opcodes[0xEA] = lambda _, mem: ld_ma16_a(mem)
        self._opcodes[0xFA] = lambda _, mem: ld_a_ma16(mem)

        # LD SP, HL / LD HL, SP + r8
        self._opcodes[0xF9] = lambda _, __: ld_sp_hl()
        self._opcodes[0xF8] = lambda _, mem: ld_hl_sppr8(mem)

        # ADD SP, r8
        self._opcodes[0xE8] = lambda _, mem: add_sp_r8(mem)

        # JP (HL)
        self._opcodes[0xE9] = lambda _: jmp_mhl()

        for i, reg in enumerate(['bc', 'de', 'hl']):
            # INC
            self._opcodes[0x10 * i + 0x3] = lambda _, __: inc_reg(r(reg))
            self._opcodes[0x10 * i + 0x4] = lambda _, __: inc_reg(r(reg[0]))
            self._opcodes[0x10 * i + 0xC] = lambda _, __: inc_reg(r(reg[1]))
            # DEC
            self._opcodes[0x10 * i + 0x5] = lambda _, __: dec_reg(r(reg[0]))
            self._opcodes[0x10 * i + 0xB] = lambda _, __: dec_reg(r(reg))
            self._opcodes[0x10 * i + 0xD] = lambda _, __: dec_reg(r(reg[1]))
        # INC
        self._opcodes[0x33] = lambda _, __: inc_reg('%sp')
        self._opcodes[0x34] = lambda _, __: inc_reg('(%hl)')
        self._opcodes[0x3C] = lambda _, __: inc_reg(r('a'))
        # DEC
        self._opcodes[0x35] = lambda _, __: dec_reg('(%hl)')
        self._opcodes[0x3B] = lambda _, __: dec_reg('%sp')
        self._opcodes[0x3D] = lambda _, __: dec_reg(r('a'))

        # PUSH/POP
        for i, reg in enumerate(['bc', 'de', 'hl', 'af']):
            self._opcodes[0xC0 + 0x10 * i + 0x1] = lambda _, __: pop_reg(r(reg))
            self._opcodes[0xC0 + 0x10 * i + 0x5] = lambda _, __: push_reg(r(reg))

        # ADD/ADC/SUB/SBC/AND/XOR/OR/CP
        for i1, op in enumerate(['add', 'adc', 'sub', 'sbc', 'and', 'xor', 'or', 'cp']):
            for i2, reg in enumerate([r(a) for a in 'bcdehl'] + ['(%hl)', r('a')]):
                self._opcodes[0x80 + 0x8 * i1 + i2] = lambda _, __: op_a_reg(op, reg)
            self._opcodes[0xC6 + 0x8 * i1] = lambda _, mem: op_a_d8(op, mem)

        # LD REG, d16
        for i, reg in enumerate(['bc', 'de', 'hl', 'sp']):
            self._opcodes[0x10 * i + 0x1] = lambda _, mem: ld_reg_d16(r(reg), mem)

        # ADD HL, REG
        for i, reg in enumerate(['bc', 'de', 'hl', 'sp']):
            self._opcodes[0x09 + 0x10 * i] = lambda _, __: add_hl_reg(r(reg))

        # LD REG, REG / LD REG, d8
        for i1, reg1 in enumerate([r(a) for a in 'bcdehl'] + ['(%hl)', r('a')]):
            for i2, reg2 in enumerate([r(a) for a in 'bcdehl'] + ['(%hl)', r('a')]):
                self._opcodes[0x40 + 0x8 * i1 + i2] = lambda _, __: ld_reg_reg(reg1, reg2)
            self._opcodes[0x06 + 0x08 * i1] = lambda _, mem: ld_reg_d8(reg, mem)

        # LD A, (REG)
        for i, reg in enumerate(['bc', 'de', 'hl+', 'hl-']):
            self._opcodes[0x10 * i + 0x2] = lambda _, __: ld_mreg_a(r(reg))
            self._opcodes[0x10 * i + 0xA] = lambda _, __: ld_a_mreg(r(reg))

        # LD A, (C) / LD (C), A
        self._opcodes[0xE2] = lambda _, __: ld_mc_a
        self._opcodes[0xF2] = lambda _, __: ld_a_mc

        # RST
        for i in range(0x00, 0x40, 0x8):
            self._opcodes[0xC7 + i] = lambda _, __: rst_nn(i)

        # CALL, JMP, JR
        self._opcodes[0x18] = lambda _, mem: jr_r8(mem)
        self._opcodes[0xC3] = lambda _, mem: jmp_a16(mem)
        self._opcodes[0xCD] = lambda _, mem: call_a16(mem)
        for i, flag in enumerate(['nzf', 'zf', 'ncy', 'cy']):
            self._opcodes[0xC0 + 0x8 * i] = lambda _, __: ret_flag(flag)
            self._opcodes[0x20 + 0x8 * i] = lambda _, mem: jr_flag_r8(flag, mem)
            self._opcodes[0xC2 + 0x8 * i] = lambda _, mem: jmp_flag_a16(flag, mem)
            self._opcodes[0xC2 + 0x8 * i + 0x2] = lambda _, mem: call_flag_a16(flag, mem)

        # Simple ops
        for addr, op in [(0x00, 'nop'), (0x10, 'stop'), (0xFB, 'ei'),
                         (0xF3, 'di'), (0x76, 'halt'), (0xC9, 'ret'),
                         (0xD9, 'reti')]:
            self._opcodes[addr] = lambda _, __: op
        for i, op in enumerate(['rlca', 'rrca', 'rla', 'rra', 'daa', 'cpl', 'scf', 'ccf']):
            self._opcodes[0x07 + 0x08 * i] = lambda _, __: op

    def disassemble(self, opcode, mem):
        try:
            return self._opcodes[opcode[0]](opcode, mem)
        except KeyError:
            return '[unknown: {!r}]'.format(opcode)

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
        return {'opcode': opcode, 'pc': pc}
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
