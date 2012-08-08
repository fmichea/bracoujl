#! /usr/bin/env python

# Author: Franck Michea < franck.michea@gmail.com >
# License: New BSD License (See LICENSE)

import argparse
import os
import pickle
import re
import sys

CALL_OPCODES = [0xC4, 0xCC, 0xCD, 0xD4, 0xDC]
RST_OPCODES = [0xC7, 0xD7, 0xE7, 0xF7, 0xCF, 0xDF, 0xEF, 0xFF]
JUMP_OPCODES = [0xC2, 0xC3, 0xCA, 0xD2, 0xDA, 0x18, 0x28, 0x38, 0x20, 0x30]
OPCODE_LINE = re.compile('\[([A-Za-z0-9]+)\] Opcode : ([0-9A-Za-z]{2}), PC : ([A-Za-z0-9]{4})')
DISSAS_LINE = re.compile('\[([A-Za-z0-9]{4})] ([^O:]+)')





class SerializedGraph(object):
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


class LinkType:
    NORMAL          = 0
    CALL            = 1
    CHANGE_MEMORY   = 2


class Link(object):
    def __init__(self, from_, to_):
        self.from_ = from_
        self.to_ = to_
        self.type_ = LinkType.NORMAL

    def __hash__(self):
        return hash('%04X -> %04X' % (self.from_, self.to_))

    def __eq__(self, other):
        return self.from_ == other.from_ and self.to_ == other.to_

    def set_type(self, type_):
        self.type_ = type_

    def color(self):
        if self.type_ == LinkType.CALL:
            return 'blue'
        elif self.type == LinkType.CHANGE_MEMORY:
            return 'red'
        return 'black'


class Block(object):
    def __init__(self, graph, addr, opcode):
        self.addr, self.addrs = addr, [addr]
        self.opcodes, self.disassembly = [opcode], ['']
        self.from_, self.to = set(), set()
        self.is_sub = False
        self.graph = graph

    def __str__(self):
        res = '%s:\n' % self.name()
        res += ''.join(map(
            lambda (addr, opcode, disassembly): '%04X  -  %02X  %s    \n' % (
                    addr, opcode, '' if disassembly == '' else ('-  %s' % disassembly)
            ), zip(self.addrs, self.opcodes, self.disassembly)
        ))
        return res

    def __eq__(self, other):
        return (self.to == other.to and self.opcodes == other.opcodes)

    def accepts_child(self):
        if len(self.to) != 1 or self.opcodes[-1] in [0xc9, 0xd9]:
            return False
        if self.opcodes[-1] in CALL_OPCODES:
            return False
        if self.opcodes[-1] in JUMP_OPCODES:
            return False
        return True

    def is_motherless(self):
        return len(self.from_) == 1

    def merge(self, block):
        self.opcodes.extend(block.opcodes)
        self.addrs.extend(block.addrs)
        self.disassembly.extend(block.disassembly)
        self.to = set()
        for new_to in list(block.to):
            self.graph.nodes[new_to].from_.remove(block.addr)
            self.link_to(new_to)
        del self.graph.nodes[block.addr]

    def link_to(self, addr):
        # Only used to keep track of access points.
        self.to.add(addr)
        self.graph.nodes[addr].from_.add(self.addr)

        # Creating real link between nodes.
        tmp = Link(self.addr, addr)
        if self.opcodes[-1] in CALL_OPCODES and len(self.to) == 1:
            tmp.set_type(LinkType.CALL)
        self.graph.links.add(tmp)

    def name(self):
        return ('sub' if self.is_sub else 'loc') + '_%04X' % self.addr

    def sumary(self):
        print 'From: %s\n' % ', '.join(
            map(lambda a: '%04X' % a, sorted(self.from_))
        )
        print self
        print 'To: %s' % ', '.join(
            map(lambda a: '%04X' % a, sorted(self.to))
        )


class Graph(object):
    def __init__(self):
        self.nodes = dict()
        self.links = set()

        # First node is a BEGIN node.
        self.nodes[0x10000] = Block(self, 0x10000, 0)
        self.nodes[0x10000].disassembly = ['BEGIN']
        self.nodes[0x10000].is_sub = True

        # Last node is a END node.
        self.nodes[0x10001] = Block(self, 0x10001, 0)
        self.nodes[0x10001].disassembly = ['END']
        self.nodes[0x10001].from_.add(0)
        self.nodes[0x10001].to.add(0)
        self.nodes[0x10001].is_sub = True

    def generate(self, filename):
        self.create_graph(filename)
        self.merge_blocks()
        self.clear_links()

    def create_graph(self, filename):
        f = open(filename)
        backtrace, last_addr = [], 0x10000
        line = f.readline()
        while line:
            match, line = OPCODE_LINE.match(line), line[:-1]
            if match is not None:
                addr, opcode = int(match.group(3), 16), int(match.group(2), 16)
                try:
                    if self.nodes[addr].opcodes[-1] != opcode:
                        msg = 'Found different opcodes for the same address...'
                        msg += '\nAddr = %04X - opcodes: %02X - %02X' % (
                            addr, self.nodes[addr].opcodes[-1], opcode
                        )
                        break
                except KeyError: # First time we encounter this address.
                    self.nodes[addr] = Block(self, addr, opcode)
                if last_addr is not None:
                    self.nodes[last_addr].link_to(addr)
                last_addr = addr
                if self.nodes[addr].opcodes[-1] in CALL_OPCODES:
                    backtrace.append(addr)
                elif self.nodes[addr].opcodes[-1] in RST_OPCODES:
                    backtrace.append(addr)
                    last_addr = None
                elif self.nodes[addr].opcodes[-1] in [0xC9, 0xD9]:
                    try: last_addr = backtrace.pop()
                    except: pass

            if line.startswith('Launching'): # Interrupt.
                backtrace.append(addr)
                last_addr = None

            match = DISSAS_LINE.match(line)
            if match is not None:
                addr, disass = int(match.group(1), 16), match.group(2)
                try:
                    self.nodes[addr].disassembly = [disass]
                except KeyError:
                    print ('Unknow disass at %x (can be ret)' % addr)
            line = f.readline()
        self.nodes[last_addr].link_to(0x10001)

    def merge_blocks(self):
        addrs = sorted(self.nodes.keys())
        for addr in addrs:
            try:
                mother = self.nodes[addr]
                while mother.accepts_child():
                    kid = self.nodes[list(mother.to)[0]]
                    if kid.is_motherless():
                        mother.merge(kid)
                    else:
                        break
            except KeyError: pass

    def clear_links(self):
        links, res = sorted(list(self.links)), []
        for it in xrange(len(links)):
            link = links[it]
            if link.from_ not in self.nodes or link.to_ not in self.nodes:
                continue
            if link.type_ == LinkType.CALL:
                self.nodes[link.to_].is_sub = True
            res.append(link)
        self.links = set(res)

def compare_graphs(graph1, graph2):
    addr_checked, stack, blocks_diff = [], [0x10000], 0
    while stack:
        addr, block1, block2 = stack.pop(), None, None
        if addr in addr_checked:
            continue
        addr_checked.append(addr)
        try: block1 = graph1.nodes[addr]
        except KeyError: pass
        try: block2 = graph2.nodes[addr]
        except KeyError: pass
        if block1 is None or block2 is None:
            print 'One of the graphs doesn\'t contain %04X addr.' % addr
            if block1 is not None:
                print 'In graph 1:'
                block1.sumary()
                stack.extend(list(block1.to))
            if block2 is not None:
                print 'In graph 2:'
                block2.sumary()
                stack.extend(list(block2.to))
            print '=' * 40
            blocks_diff += 1
            continue
        if not (block1 == block2):
            block1.sumary()
            print '- ' * 20
            block2.sumary()
            print '=' * 40
            blocks_diff += 1
        stack.extend(list(block1.to | block2.to))
    print 'Found %d differences.' % blocks_diff

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Some debugging tool.')
    parser.add_argument('-i', '--input', action='append', required=True,
                        metavar='filename', help='Input file (logs from nebula).')
    parser.add_argument('-o', '--output', action='store', required=False,
                        metavar='filename', help='Output file (default: prints on stdout).')
    parser.add_argument('-d', '--dotify', action='store_true', default=False,
                        help='Translates graph to dot.')
    parser.add_argument('-a', '--ascii', action='store_true', default=False,
                        help='Prints program in ascii.')
    parser.add_argument('-c', '--compare', action='store_true', default=False,
                        help='Compares two graphs (needs two inputs).')
    parser.add_argument('-s', '--serialize', action='store_true', default=False,
                        help='Serialize graph and use it if serialized.')
    args = parser.parse_args(sys.argv[1:])

    graphs = []
    for it in xrange(len(args.input)):
        input_filename = args.input[it]
        if not os.path.isfile(input_filename):
            sys.exit('File `%s` was not found...' % input_filename)
        ser = SerializedGraph(args.serialize, input_filename)
        graph = ser.read()
        if graph is None:
            graph = Graph()
            graph.generate(input_filename)
            ser.write(graph)
        graphs.append(graph)

    if args.dotify or args.ascii:
        output_filename = args.output if args.output else None
        if args.dotify: DotWriter(output_filename).generate(graphs[0])
        else: AsciiWriter(output_filename).generate(graphs[0])
    elif args.compare:
        if len(graphs) < 2:
            sys.exit('Need two graphs to compare them.')
        compare_graphs(graphs[0], graphs[1])

    sys.exit(0)
