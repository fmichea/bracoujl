# dotwriter.py - Writes the graph in dot format.
# Author: Franck Michea < franck.michea@gmail.com >
# License: New BSD License (See LICENSE)

class DotWriter(object):
    def __init__(self, output_file = None):
        if output_file is None:
            self.f = sys.stdout
        else:
            self.f = open(output_file, 'w')

        self.f.write('digraph bracoujl {\n')
        self.f.write('\tsplines = true;\n')
        self.f.write('\tnode [ shape = box, fontname = "Deja Vu Sans Mono" ];\n\n')

    def __del__(self):
        self.f.write('}\n')
        self.f.close()

    def generate(self, graph):
        addrs = sorted(graph.nodes.keys())
        for addr in addrs:
            block = graph.nodes[addr]
            self.f.write('\tnode_{addr:04X} [ label = "{code}" ];\n'.format(
                addr = block.addr,
                code = str(block).replace('\n', '\\l')
            ))
        self.f.write('\n')
        for link in list(graph.links):
            self.f.write("""\tnode_{addr1:04X} -> node_{addr2:04X} [ color = {color}, tailport = s, headport = n ];\n""".format(
                addr1 = link.from_,
                addr2 = link.to_,
                color = link.color()
            ))
