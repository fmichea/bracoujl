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

_ADDR_WIDTH = proc.CPU_CONF.get('addr_width', 32)
_ADDR_SIZE = m.ceil(m.log2(_ADDR_WIDTH))
_ADDR_FRMT = '0{}X'.format(_ADDR_SIZE)

_DISASSEMBLER = proc.CPU_CONF.get('disassembler', type(None))()

# These two will not be displayed.
_BEGIN_ADDR = 1 << _ADDR_WIDTH
_END_ADDR   = 1 << _ADDR_WIDTH + 1

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
        self.tlf, self.within = False, []
        self.uniq, self.uniq_id = True, 0

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
            name += '_{uniq_id}'.format(uniq_id=self.uniq_id)
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
        for spec_opc in ['ret', 'call', 'jump', 'jr']:
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
            link = Link(self, to.to)
            # Link again.
            n = to.unlink_all()
            link.do_link(n)
            # Copy link property.
            link.link_type = to.link_type

    def __eq__(self, other):
        # This will also check addresses and the like. Don't forget to change
        # this if it is not the case anymore.
        return self.insts == other.insts

    def __hash__(self):
        return hash(self.uniq_name())


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

        def ret_miss(link):
            msg = 'Could not pop call place from the which we come'
            msg += ' from.'
            link.link_type = LinkType.RET_MISS
            #print(msg, file=sys.stderr, flush=True)

        def cutfunction(blocks, function):
            todos, done = [function], []
            while todos:
                todo = todos.pop()

                if todo in done:
                    continue
                done.append(todo)

                # When the block was already removed from the list, we
                # just ignore but conitnue to follow links to add the
                # "within" information.
                try:
                    blocks[todo['pc']].remove(todo)
                except ValueError:
                    pass

                # Add the knownledge that this block is within the
                # current function.
                todo.within.append(function.uniq_name())

                # We remove it and continue on its blocks
                todos.extend([to.to for to in todo.tos])

        blocks, last_block, backtrace = dict(), None, list()

        ########################################################################
        ##### STEP 1: Fetch the graph from the log file.                   #####
        ########################################################################

        # Create a special block for the begining of the logs.
        last_block = SpecialBlock({'pc': _BEGIN_ADDR}, 'BEGIN')
        last_block.block_type = BlockType.SUB
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
                        block.uniq_id = len(blocks[block['pc']])
                        blocks[block['pc']][0].uniq = False
                        block.uniq = False
                    blocks[block['pc']].append(block)

                # Now we need to link this block and the last block.
                link = find_link(last_block, block)

                # Now we need to treat special cases.
                offset = block['pc'] - last_block['pc']

                if (last_block['opcode'] in proc.CPU_CONF['ret_opcodes'] and
                    offset != proc.CPU_CONF['ret_opcodes_size']):
                    # We a ret, and triggered it. A ret trigger happens when
                    # we don't fall-through. In that case, we traceback to the
                    # place where we were called.
                    try:
                        backblock, size = backtrace[-1]
                        if ((size == 0 or block['pc'] == backblock['pc'] + size) or
                            block['pc'] in proc.CPU_CONF['interrupts']):
                            last_block = backblock
                            link = find_link(last_block, block)
                            backtrace.pop()
                        else:
                            ret_miss(link)
                    except IndexError:
                        ret_miss(link)
                else:
                    for spec_op in ['call', 'jump', 'jr']:
                        spec_op += '_opcodes'
                        if last_block['opcode'] in proc.CPU_CONF[spec_op]:
                            # Links are colorized depending on the detection of
                            # if they are taken or not. First we need to know
                            # wether we know the triggering link or not.
                            if offset == proc.CPU_CONF[spec_op + '_size']:
                                link.link_type = LinkType.NOT_TAKEN
                            else:
                                if not last_block.tlf:
                                    # Offset is not the size of the opcode
                                    # *and* this is the first time it happens,
                                    # we are on the triggering link.
                                    if spec_op == 'call_opcodes':
                                        block.block_type = BlockType.SUB
                                        link.link_type = LinkType.CALL_TAKEN
                                    else:
                                        link.link_type = LinkType.TAKEN
                                    last_block.tlf = True
                                if spec_op == 'call_opcodes':
                                    size = proc.CPU_CONF['call_opcodes_size']
                                    backtrace.append((last_block, size))

                if block['pc'] in proc.CPU_CONF['interrupts']:
                    # If the block is the beginning of an interrupt, we don't
                    # need the link, but we do need to keep the triggering
                    # block in the backtrace.
                    block.block_type, size = BlockType.INT, 0
                    if last_block['opcode'] in proc.CPU_CONF['int_opcodes']:
                        size = proc.CPU_CONF['int_opcodes_size']
                    backtrace.append((last_block, size))
                    link = None

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
                    call_block.uniq = False
                    link = Link(from_.from_, call_block)
                    link.link_type = LinkType.CALL_TAKEN
                    for _ in range(cnt):
                        link.do_link()
                    from_.unlink_all()

                # Keep the beginning of the sub in a list.
                functions.append(subblock)

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

        ########################################################################
        ##### STEP 4: Now we can decide which functions we will need to    #####
        #####         generate.                                            #####
        ########################################################################
        result = {'functions': dict(), 'inner-functions': dict()}

        innerfunctions = []
        for subblock in functions:
            # We have two possibilities: the beginning of the sub is not only
            # called, so we keep it for later concidering it to be within
            # another function. Else, we just cut out the current sub function
            # from the blocks.
            if len(subblock.froms) != 0:
                innerfunctions.append(subblock)
            else:
                result['functions'][subblock.uniq_name()] = subblock
                cutfunction(blocks, subblock)

        # Finally, for each "inner function" that were not reached from any
        # standard function, we cut it out and generate it anyway, it must mean
        # it is "within itself", example:
        #
        # sub_0216:
        #    0216 - ldh %a, ($0xFF44)
        #    0218 - cp %a, $0x145
        #    021A - jr cy, $0xFA ; ($-6)
        #    021C - ret
        for inner in innerfunctions:
            if inner.within == []:
                result['functions'][inner.uniq_name()] = inner
                cutfunction(blocks, inner)
            else:
                result['inner-functions'][inner.uniq_name()] = inner

        ########################################################################
        ##### STEP 5: SANITY CHECK: if there are still blocks in the main  #####
        #####         dictionary, we probably failed something.            #####
        ########################################################################
        remaining = sum([blocks[pc] for pc in keys], [])
        if remaining:
            msg = 'WARNING: Sanity check failed, there are remaining blocks '
            msg += 'in the internal dictionary: '
            msg += ', '.join([b.uniq_name() for b in remaining])
            print(msg)

        # We did it! We now have a complete list of sub-functions and interrupts
        # we can return, awesome!
        return result


def compare(funcs1, funcs2):
    funcs, count = set(funcs1.keys()) | set(funcs2.keys()), 0
    print('Comparison of two graphs:')
    for funcname in funcs:
        #print('FUNC', funcname)
        errors = []
        try: func1 = funcs1[funcname]
        except KeyError:
            errors.append('Function {} is not defined in first graph.'.format(funcname))
            continue
        try: func2 = funcs2[funcname]
        except KeyError:
            errors.append('Function {} is not defined in second graph.'.format(funcname))
            continue
        blocks, visited = [(func1, func2)], set()
        while blocks:
            block1, block2 = blocks.pop()
            if (block1, block2) in visited:
                continue
            visited.add((block1, block2))
            if block1 is not None and block2 is not None:
                #print('[1] Doing', block1.uniq_name(), block2.uniq_name())
                # Block in both functions!
                if block1 != block2:
                    errors.append('Block {} is different in functions {}.'.format(
                        block1.uniq_name(), func1.uniq_name()
                    ))
                    count += 1
                tos1 = dict((l.to.uniq_name(), l.to) for l in block1.tos)
                tos2 = dict((l.to.uniq_name(), l.to) for l in block2.tos)
                #print('tos1:', tos1)
                #print('tos2:', tos2)
                for b in list(set(tos1.keys()) - set(tos2.keys())):
                    m = 'Block {} is only reached from first function from '
                    m += 'block {}'
                    errors.append(m.format(b, block1.uniq_name()))
                    blocks.insert(0, (tos1[b], None))
                    count += 1
                for b in list(set(tos2.keys()) - set(tos1.keys())):
                    m = 'Block {} is only reached from second function from '
                    m += 'block {}'
                    errors.append(m.format(b, block2.uniq_name()))
                    blocks.insert(0, (None, tos2[b]))
                    count += 1
                for b in list(set(tos1.keys()) & set(tos2.keys())):
                    blocks.insert(0, (tos1[b], tos2[b]))
            elif block2 is None:
                #print('[2] Doing', block1.uniq_name())
                # Only in first function.
                # XXX: Do something?
                pass
            else:
                # Only in second function.
                # XXX: Do something?
                #print('[3] Doing', block2.uniq_name())
                pass
        if errors:
            print('Begin comparison of function: {}'.format(funcname))
            for error in errors:
                print(error)
            print('-' * 40)
    print('Total error count:', count)
