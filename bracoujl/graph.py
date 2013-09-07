# graph.py - Some structures to build graphs.
# Author: Franck Michea < franck.michea@gmail.com >
# License: New BSD License (See LICENSE)

import binascii
import os
import pickle
import sys

import math as m

from collections import Counter

# Change this if you want to use your processor.
# XXX: Nothing smart for now. Useful?
import bracoujl.processor.gb_z80 as proc

_ADDR_SIZE = m.ceil(m.log2(proc.CPU_CONF.get('addr_width', 32)))
_ADDR_FRMT = '0{}X'.format(_ADDR_SIZE)

_DISASSEMBLER = proc.CPU_CONF.get('disassembler', type(None))()

# These two will not be displayed.
_BEGIN_ADDR = 0x10000
_END_ADDR   = 0x10001

def _enum(**enums):
    return type('Enum', (), enums)

LinkType    = _enum(NORMAL='black', TAKEN='green', CALL_TAKEN='blue', NOT_TAKEN='red', RET_MISS='brown')
BlockType   = _enum(INT='int', LOC='loc', SUB='sub')
GraphState  = _enum(NORMAL_GRAPH=0, INTERRUPT=1)

class Link:
    '''
    This class represents a link between two blocks.

    :param from_: The block from which the link begins.
    :param to: The block to which the link goes.
    :param link_type: The type of the link.
    '''

    def __init__(self, from_, to):
        self.from_, self.to, self.link_type = from_, to, LinkType.NORMAL
        self._repr = '[{:x}] {:{addr_frmt}} -> {:{addr_frmt}} [{:x}]'.format(
            id(self.from_),
            self.from_['pc'],
            self.to['pc'],
            id(self.to),
            addr_frmt=_ADDR_FRMT,
        )

    def do_link(self, n=1):
        self.from_.tos[self] += n
        self.to.froms[self] += n

    def do_unlink(self):
        self.from_.tos[self] -= 1
        if not self.from_.tos[self]:
            del self.from_.tos[self]
        self.to.froms[self] -= 1
        if not self.to.froms[self]:
            del self.to.froms[self]

    def unlink_all(self):
        count = self.from_.tos[self]
        del self.from_.tos[self]
        del self.to.froms[self]
        return count

    def __repr__(self):
        return self._repr

    def __eq__(self, other):
        return self._repr == other._repr

    def __hash__(self):
        return hash(self._repr)


class Instruction:
    '''
    An instruction consists of an address, an opcode.

    :param inst: The instruction parsed by the cpu configuration.
    '''

    def __init__(self, inst):
        self._inst = inst

    def __str__(self):
        res = '    {addr:{addr_frmt}}: {opcode}'.format(
            addr = self['pc'],
            opcode = binascii.hexlify(self['opcode']).decode('utf-8'),
            addr_frmt=_ADDR_FRMT,
        )
        if _DISASSEMBLER is not None:
            res += ' - {disassembly}'.format(
                disassembly=_DISASSEMBLER.disassemble(self._inst)
            )
        return res

    def __getitem__(self, item):
        return self._inst[item]

    def __eq__(self, other):
        f = lambda obj: (obj['pc'], obj['opcode'], obj['mem'])
        return f(self) == f(other)


class Block:
    '''
    A block represents a couple of instructions executed in a row without any
    branchement in it. It possibly ends with a CALL, a JUMP or a RET.

    Links are stored in two attributes, `froms` and `tos`. There is a
    additional attribute that holds the information necessary to know if a
    branchement trigerred.
    '''

    def __init__(self, inst, inst_class=Instruction):
        self.insts, self.block_type = [inst_class(inst)], BlockType.LOC
        self.froms, self.tos = Counter(), Counter()
        self.tlf, self.uniq = False, True

    def __str__(self):
        res = '{name}:\n'.format(name=self.name())
        res += '\n'.join(str(it) for it in self.insts)
        return res

    def __getitem__(self, item):
        '''
        Until there is multiple instructions in a block, the __getitem__
        functions coresponds to the uniq instruction in it. The property always
        works for 'pc' property.
        '''
        return self.insts[0][item]

    def name(self):
        return '{block_type}_{pc:{addr_frmt}}'.format(
            pc=self['pc'], block_type=self.block_type, addr_frmt=_ADDR_FRMT,
        )

    def uniq_name(self):
        name = self.name()
        if not self.uniq:
            name += '_' + hex(id(self))[2:]
        return name

    def accepts_merge_top(self):
        '''
        This function determines if the current block can be merged with the
        preceding block. This is *True* if if we can't reach this block from
        multiple other blocks.
        '''
        return len(self.froms) == 1

    def accepts_merge_bottom(self):
        '''
        This function determines if the current block accepts merge at its
        bottom. It is possible if we are not on the end of a block, meaning
        that we don't go to multiple blocks, or that we are not part of the
        special opcodes (call, jump, ret).
        '''
        if len(self.tos) != 1:
            return False
        for spec_opc in ['ret', 'call', 'jump']:
            if self.insts[-1]['opcode'] in proc.CPU_CONF[spec_opc + '_opcodes']:
                return False
        return True

    def merge(self, other):
        '''
        This function will take a block bellow the current block (*self*) and
        merge them. They must be directly following themselves to avoid
        breaking the graph.
        '''
        self.insts.extend(other.insts)
        self.tos = Counter()
        for to in list(other.tos):
            Link(self, to.to).do_link()
            to.unlink_all()

    def __eq__(self, other):
        # This will also check addresses and the like. Don't forget to change
        # this if it is not the case anymore.
        return self.insts == other.insts


class SpecialBlock(Block):
    def __init__(self, inst, label, mergeable=True):
        blockself = self
        class SpecialInstruction(Instruction):
            def __str__(self):
                res = ''
                if blockself._mergeable:
                    res += '    {padding} '.format(padding=''.ljust(_ADDR_SIZE))
                res += '{label}'.format(label=label)
                return res
            def __getitem__(self, item):
                if item in ['pc', 'opcode', 'mem']:
                    if item in self._inst:
                        return super().__getitem__(item)
                    return None
                return super().__getitem__(item)
        super().__init__(inst, inst_class=SpecialInstruction)
        self._mergeable = mergeable

    def __str__(self):
        s = super().__str__().splitlines()
        if len(s) == 2:
            return s[-1]
        return '\n'.join(s)

    def name(self):
        return super().name() + 'S'

    def accepts_merge_top(self):
        return self._mergeable and super().accepts_merge_top()

    def accepts_merge_bottom(self):
        return self._mergeable and super().accepts_merge_bottom()


class Graph:
    def generate_graph(self, filename):
        def find_link(last_block, block):
            link = Link(last_block, block)
            for ll in last_block.tos:
                if ll == link:
                    link = ll
                    break
            return link

        blocks, last_block, backtrace = dict(), None, list()

        ########################################################################
        ##### STEP 1: Fetch the graph from the log file.                   #####
        ########################################################################

        # Create a special block for the begining of the logs.
        last_block = SpecialBlock({'pc': _BEGIN_ADDR}, 'BEGIN')
        blocks[_BEGIN_ADDR] = [last_block]

        with open(filename) as fd:
            for line in fd:
                inst = proc.CPU_CONF['parse_line'](line)

                # If line is not recognized, just skip it.
                if inst is None:
                    continue

                # Create the list of blocks for the current PC in the blocks
                # dictionary.
                if inst['pc'] not in blocks:
                    blocks[inst['pc']] = []

                # Check if we already know the current instruction for the
                # current program counter. If we do, we keep the current block
                # and add a link.
                block_found = False
                for block in blocks[inst['pc']]:
                    if block['opcode'] == inst['opcode']:
                        block_found = True
                        break
                if not block_found:
                    block = Block(inst)
                    if 0 < len(blocks[block['pc']]):
                        # No loop needed, if we set the first one and each one
                        # from the second, we will set them all.
                        blocks[block['pc']][0].uniq = False
                        block.uniq = False
                    blocks[block['pc']].append(block)

                # Now we need to link this block and the last block.
                link = find_link(last_block, block)

                # Now we need to treat special cases.
                offset = last_block['pc'] - block['pc']
                if block['pc'] in proc.CPU_CONF['interrupts']:
                    # If the block is the beginning of an interrupt, we don't
                    # need the link, but we do need to keep the triggering
                    # block in the backtrace.
                    block.block_type = BlockType.INT
                    backtrace.append(last_block)
                    link = None
                elif (last_block['opcode'] in proc.CPU_CONF['ret_opcodes'] and
                      offset != proc.CPU_CONF['ret_opcodes_size']):
                    # We a ret, and triggered it. A ret trigger happens when
                    # we don't fall-through. In that case, we traceback to the
                    # place where we were called.
                    try:
                        last_block = backtrace.pop()
                        link = find_link(last_block, block)
                    except IndexError:
                        msg = 'Could not pop call place from the which we come'
                        msg += ' from.'
                        link.link_type = LinkType.RET_MISS
                        #print(msg, file=sys.stderr, flush=True)
                else:
                    for spec_op in ['call', 'jump']:
                        spec_op += '_opcodes'
                        if last_block['opcode'] in proc.CPU_CONF[spec_op]:
                            # Links are colorized depending on the detection of
                            # if they are taken or not. First we need to know
                            # wether we know the triggering link or not.
                            if offset == proc.CPU_CONF[spec_op + '_size']:
                                link.link_type = LinkType.NOT_TAKEN
                            elif not last_block.tlf:
                                # Offset is not the size of the opcode *and*
                                # this is the first time it happens, we are on
                                # the triggering link.
                                if spec_op == 'call_opcodes':
                                    block.block_type = BlockType.SUB
                                    link.link_type = LinkType.CALL_TAKEN
                                    backtrace.append(last_block)
                                else:
                                    link.link_type = LinkType.TAKEN
                                last_block.tlf = True

                # We finally really link the Link if it still exists and was not
                # known, and add the block to the list of blocks.
                if link is not None:
                    link.do_link()

                # To be used in the next step.
                last_block = block

        # Finally we add a end block, to know were the logs end.
        end_block = SpecialBlock({'pc': _END_ADDR}, 'END')
        Link(last_block, end_block).do_link()
        blocks[_END_ADDR] = [end_block]

        ########################################################################
        ##### STEP 2: We now split all calls and only put little boxes,    #####
        #####         unmergeable, that will only contain the name of the  #####
        #####         functions.                                           #####
        ########################################################################
        functions, keys = [], list(sorted(blocks.keys()))
        for pc in keys:
            for subblock in blocks[pc]:
                # If we did interrupts correctly, we don't have any link that
                # comes to it, we just need to put it in the function list.
                if subblock.block_type == BlockType.INT:
                    functions.append(subblock)

                # We only care about subs from here.
                if subblock.block_type != BlockType.SUB:
                    continue

                # For each link, if it's a call link (it is marked "taken"),
                # then we remove this link and place a little box instead, to
                # be able to split the functions' graphs in multiple files.
                items = list(subblock.froms.items())
                for from_, cnt in items:
                    if from_.link_type != LinkType.CALL_TAKEN:
                        continue
                    call_str = 'Call to {}.'.format(subblock.name())
                    call_block = SpecialBlock({'pc': subblock['pc']}, call_str,
                                              mergeable=False)
                    link = Link(from_.from_, call_block)
                    link.link_type = LinkType.CALL_TAKEN
                    for _ in range(cnt):
                        link.do_link()
                    from_.unlink_all()

                # Finally, if this function is not part of another function, we
                # can cut it from and put it in a separate file later, so we
                # keep it in a list of functions.
                if len(subblock.froms) == 0:
                    functions.append(subblock)
                else:
                    print('Function {} is within another function.'.format(
                        subblock.name()
                    ))

        ########################################################################
        ##### STEP 3: Now we will merge all the blocks that can be merged  #####
        #####         to remove useless links and make it ready.           #####
        ########################################################################
        keys = list(sorted(blocks.keys()))
        for pc in keys:
            for subblock in blocks[pc]:
                while True:
                    # If this block cannot be merged on its bottom, we ignore it.
                    if not subblock.accepts_merge_bottom():
                        break

                    # We now know that we have only one link, we fetch it and check
                    # wether it accepts top merges.
                    to = list(subblock.tos.items())[0][0].to
                    if not to.accepts_merge_top():
                        break

                    # We know are sure we can merge this block, so we proceed and
                    # remove it from our block list.
                    blocks[to['pc']].remove(to)
                    subblock.merge(to)

        # We did it! We now have a complete list of sub-functions and interrupts
        # we can return, awesome!
        return functions
