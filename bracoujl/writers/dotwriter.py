# dotwriter.py - Writes the graph in dot format.
# Author: Franck Michea < franck.michea@gmail.com >
# License: New BSD License (See LICENSE)

import sys

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

    def generate_subgraph(self, subgraph):
        self.f.write('\tsubgraph {subgraph_name} {{\n'.format(
            subgraph_name = subgraph.name(),
        ))
        addrs = sorted(subgraph.blocks.keys())
        for addr in addrs:
            block = subgraph.blocks[addr]
            self.f.write('\t\t{block_name} [ label = "{code}\\l" ];\n'.format(
                block_name = block.node_name(),
                code = str(block).replace('\n', '\\l').replace('\t', ' ' * 4)
            ))
        self.f.write('\n')
        for link in list(subgraph.links):
            self.f.write('\t\t{}\n'.format(self.generate_link(link)))
        self.f.write('\t}\n')

    def generate_link(self, link):
        return '{block1} -> {block2} [ {options} ];'.format(
            block1 = link._from.node_name(),
            block2 = link.to.node_name(),
            options = 'color = {color}, tailport = s, headport = n'.format(
                color = link.type,
            )
        )

    def generate(self, graph):
        for subgraph in graph.graphs:
            self.generate_subgraph(subgraph)
        for name, interrupt in graph.interrupts.items():
            self.generate_subgraph(interrupt)
        for link in graph.graph_links:
            self.f.write('\t{}\n'.format(self.generate_link(link)))
