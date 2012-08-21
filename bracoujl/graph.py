# graph.py - Some structures to build graphs.
# Author: Franck Michea < franck.michea@gmail.com >
# License: New BSD License (See LICENSE)

import os
import pickle
import sys

import bracoujl.config


def _readlines(f):
    line = f.readline()
    while line:
        yield line[:-1]
        line = f.readline()

def _enum(**enums):
    return type('Enum', (), enums)

LinkType = _enum(NORMAL='black', CALL='blue', MEMORY_CHANGE='red')
GraphState = _enum(NORMAL_GRAPH=0, INTERRUPT=1)

class SerializedGraph(object):
    '''Loads and writes a serialized representation of a graph in a file.'''

    def __init__(self, serialize, filename):
        self.filename = '.%s.graph' % filename
        self.origin = filename
        self.serialize = serialize

    def read(self):
        if not self.serialize or not os.path.isfile(self.filename):
            return None
        if os.stat(self.filename).st_mtime < os.stat(self.origin).st_mtime:
            return None
        f = open(self.filename, 'rb')
        res = pickle.load(f)
        f.close()
        return res

    def write(self, graph):
        if not self.serialize:
            return
        f = open(self.filename, 'wb')
        pickle.dump(graph, f)
        f.close()


class Link(object):
    def __init__(self, _from, to):
        self._from, self.to, self.type = _from, to, LinkType.NORMAL

    def __hash__(self):
        return hash('{:04X} -> {:04X}'.format(
            self._from.addr, self.to.addr
        ))

    def __eq__(self, other):
        return (self._from == other._from and self.to == other.to)


class Instruction(object):
    '''
    An instruction consists of an address (addr), an opcode, and optionnally a
    disassembly.
        - addr: Address of the instruction.
        - opcode: Opcode of the instruction.
        - disassembly (opt.): Disassembly of the instruction.
    '''

    def __init__(self, addr, opcode, disassembly=''):
        self.addr, self.opcode, self.disassembly  = addr, opcode, disassembly

    def __str__(self):
        return '\t{addr:04X} - {opcode:02X} - {disassembly}'.format(
            addr = (self.addr & 0xFFFF), opcode = self.opcode,
            disassembly = self.disassembly,
        )

    def __eq__(self, other):
        return (self.addr == other.addr and self.opcode == other.opcode)


class Block(object):
    '''
    A block represents a couple of instructions executed in a row without
    breaking the workflow. It possibly ends with a CALL or a JUMP. Here are its
    attributes explained:
        - addr: First address of the block.
        - is_sub: Block is the beginning of a sub function (was called).
        - instructions: List of all the instructions in the block.
    '''
    def __init__(self, subgraph, addr, opcode):
        self.addr, self.froms, self.tos = addr, set(), set()
        self.subgraph, self.is_sub = subgraph, False
        self.instructions = [Instruction(addr, opcode)]

    def __str__(self):
        res = '{name}:\n'.format(name = self.name())
        res += '\n'.join(map(lambda a: str(a), self.instructions))
        return res

    def __eq__(self, other):
        return (self.tos == other.tos and
                self.instructions == other.instructions)

    def node_name(self):
        return '{gname}_node_{addr:04X}'.format(
            gname = self.subgraph.name(), addr = self.addr,
        )

    def name(self):
        return self.node_name().replace('node', 'sub' if self.is_sub else 'loc')

    def add_disassembly(self, disassembly):
        self.instructions[-1].disassembly = disassembly

    def accepts_child(self):
        if len(self.tos) != 1 or self.instructions[-1].opcode in [0xc9, 0xd9]:
            return False
        if self.instructions[-1].opcode in bracoujl.config.CALL_OPCODES:
            return False
        if self.instructions[-1].opcode in bracoujl.config.JUMP_OPCODES:
            return False
        return True

    def is_motherless(self):
        return len(self.froms) == 1

    def merge(self, block):
        self.instructions.extend(block.instructions)
        self.tos = set()
        for new_to in list(block.tos):
            self.subgraph.blocks[new_to].froms.remove(block.addr)
            self.link_to(new_to)
        del self.subgraph.blocks[block.addr]

    def link_to(self, addr):
        # Only used to keep track of access points.
        self.tos.add(addr)
        self.subgraph.blocks[addr].froms.add(self.addr)

        # Creating real link between nodes.
        tmp = Link(self, self.subgraph.blocks[addr])
        if (self.instructions[-1].opcode in bracoujl.config.CALL_OPCODES and
            len(self.tos) == 1):
            tmp.type = LinkType.CALL
        if tmp not in self.subgraph.links:
            self.subgraph.links.add(tmp)

    def sumary(self):
        def addrs_printer(addrs):
            return ', '.join(map(lambda a: '{:04X}'.format(a), addrs))
        print('From: {addrs}\n'.format(addrs = addrs_printer(self.froms)))
        print(str(self))
        print('To: {addrs}\n'.format(addrs = addrs_printer(self.tos)))


class SubGraph(object):
    '''
    This structure represents a graph, from only one memory viewpoint. If
    memory changes during execution, another subgraph will be created by the
    main class Graph bellow. It contains several datas:
        - blocks: The nodes representing a block of code (Block class before).
        - links: Representing all the links between every block.
        - id: Used to differenciate every subgraph name.
    '''

    def __init__(self, id):
        '''Initialize data needed in a subgraph.'''
        self.blocks, self.links, self.id = dict(), set(), id
        self.is_interrupt = False

    def name(self):
        '''Returns the name of the subgraph, using its id.'''
        if not self.is_interrupt:
            return 'subgraph{id}'.format(id = self.id)
        else:
            return 'int{id}'.format(id = self.id)

    def add_block(self, block):
        self.blocks[block.addr] = block

    def opcode(self, addr):
        return self.blocks[addr].instructions[-1].opcode

    def merge_blocks(self):
        '''
        This method merges every block of the subgraph after generation. When
        generating the complete graph, a block only consists of one
        instruction.
        '''
        addrs = sorted(self.blocks.keys())
        for addr in addrs:
            try:
                mother = self.blocks[addr]
                while mother.accepts_child():
                    kid = self.blocks[list(mother.tos)[0]]
                    if kid.is_motherless():
                        mother.merge(kid)
                    else:
                        break
            except KeyError: pass
        links, res = sorted(list(self.links)), []
        for it in xrange(len(links)):
            link = links[it]
            if link._from.addr not in self.blocks or link.to.addr not in self.blocks:
                continue
            if link.type == LinkType.CALL:
                self.blocks[link.to.addr].is_sub = True
            res.append(link)
        self.links = set(res)


class Graph(object):
    def __init__(self):
        self.graphs, self.graph_links, self.workflow = [], [], []
        self.graphs.append(SubGraph(0))
        self.interrupts, self.current_interrupt = dict(), []
        self.current_state = GraphState.NORMAL_GRAPH
        self.last_addr, self.backtrace = bracoujl.config.BEGIN_ADDR, []

    def current_graph(self):
        if self.current_state == GraphState.NORMAL_GRAPH:
            return self.graphs[-1]
        else: # Can be anything between 1 and +oo
            return self.interrupts[self.current_interrupt[-1]]

    def next_graph(self, addr, opcode):
        if self.backtrace != []:
            sys.exit('''There is at least one call between two memory states.
Collliding addr is {addr:04X} with opcode {opcode:02X} (was {was:02X})'''.format(
                addr = addr, opcode = opcode,
                was = self.graphs[-1].opcode(addr),
            ))
        print 'Detected a change in memory at address {addr:04X}.'.format(
            addr = addr,
        )
        graph = SubGraph(len(self.graphs))
        graph.add_block(Block(graph, addr, opcode))
        self.graphs.append(graph)
        self.graph_links.append(Link(
            self.graphs[-2].blocks[self.last_addr],
            graph.blocks[addr]
        ))
        self.graph_links[-1].type = LinkType.MEMORY_CHANGE

    def interrupt_launched(self, int_name):
        # Loads INT mode and creates graph for interrupt.
        self.current_state += GraphState.INTERRUPT
        self.current_interrupt.append(int_name)
        if int_name not in self.interrupts.keys():
            self.interrupts[int_name] = bracoujl.graph.SubGraph(int_name)
            self.interrupts[int_name].is_interrupt = True

        # Adds a node in workflow graph.
        self.workflow.append(self.last_addr)

        # Breaks links between graphs.
        self.backtrace.append((self.last_addr, False))
        self.last_addr = None

    def _matches_regex(self, regex, line):
        self.matches = regex.match(line)
        return (self.matches is not None)

    def generate(self, filename):
        fd, graph = open(filename), None
        self._create_begin_block()
        for line in _readlines(fd):
            # Opcode line with addr first and opcode second.
            if self._matches_regex(bracoujl.config.OPCODE, line):
                graph = self.current_graph()
                addr = int(self.matches.group(2), 16)
                opcode = int(self.matches.group(1), 16)

                # Current block is created.
                try:
                    if graph.opcode(addr) != opcode:
                        self.next_graph(addr, opcode)
                except KeyError: # First time we encounter this address.
                    graph.add_block(Block(graph, addr, opcode))

                # Linkings nodes.
                if self.last_addr is not None:
                    graph.blocks[self.last_addr].link_to(addr)
                self.last_addr = addr

                # Special cases.
                if graph.opcode(addr) in bracoujl.config.CALL_OPCODES:
                    self.backtrace.append((addr, True))
                elif graph.opcode(addr) in [0xC9, 0xD9]:
                    try:
                        last_addr, call = self.backtrace.pop()
                        if self.current_state != GraphState.NORMAL_GRAPH:
                            # FIXME: print 'Exiting an interrupt!'
                            #self._create_end_block()
                            if not call:
                                self.current_state -= GraphState.INTERRUPT
                                self.current_interrupt.pop()
                        self.last_addr = last_addr
                    except:
                        pass

            # Interrupt line sets the start of the execution of an interrupt...
            if self._matches_regex(bracoujl.config.INTERRUPT, line):
                self.interrupt_launched(int(self.matches.group(1), 16))
                self._create_begin_block()

            # Disass line contains the disass of the code.
            if self._matches_regex(bracoujl.config.DISASS, line):
                addr = int(self.matches.group(1), 16)
                disassembly = self.matches.group(2)
                try:
                    graph.blocks[addr].add_disassembly(disassembly)
                except KeyError:
                    print('Unknow disass at {addr:04X} (can be ret)'.format(
                        addr = addr
                    ))
                    print line
        self._create_end_block()
        for subgraph in self.graphs:
            subgraph.merge_blocks()
        for name, interrupts in self.interrupts.items():
            interrupts.merge_blocks()
        fd.close()

    def _create_begin_block(self):
        graph = self.current_graph()
        block = Block(graph, bracoujl.config.BEGIN_ADDR, 0)
        block.add_disassembly('BEGIN')
        block.is_sub = True
        graph.add_block(block)
        self.last_addr = block.addr

    def _create_end_block(self):
        graph = self.current_graph()
        block = Block(graph, bracoujl.config.END_ADDR, 0)
        block.add_disassembly('END')
        block.froms.add(0)
        block.tos.add(0)
        block.is_sub = True
        graph.add_block(block)
        graph.blocks[self.last_addr].link_to(block.addr)
