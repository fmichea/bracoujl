# asciiwriter.py - Writes the disassembly of the program in console.
# Author: Franck Michea < franck.michea@gmail.com >
# License: New BSD License (See LICENSE)

class AsciiWriter(object):
    def __init__(self, output_file = None):
        if output_file is None:
            self.f = sys.stdout
        else:
            self.f = open(output_file, 'w')

    def __del__(self):
        self.f.close()

    def generate(self, graph):
        addrs = sorted(graph.nodes.keys())
        for addr in addrs:
            self.f.write(str(graph.nodes[addr]))
            self.f.write('\n')
