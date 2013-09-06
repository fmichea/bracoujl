# dotwriter.py - Writes the graph in dot format.
# Author: Franck Michea < franck.michea@gmail.com >
# License: New BSD License (See LICENSE)

import sys

class DotWriter:
    def generate_graph(self, output_file, function):
        output_file.write('digraph {name} {{\n'.format(name=function.uniq_name()))
        output_file.write('\tsplines = true;\n')
        output_file.write('\tnode [ shape = box, fontname = "Deja Vu Sans Mono" ];\n\n')

        blocks, blocks_done = [function], []
        while blocks:
            block = blocks.pop()
            if block in blocks_done:
                continue
            output_file.write('\t\t{block_name} [ label = "{code}\\l" ];\n'.format(
                block_name = block.uniq_name(),
                code = str(block).replace('\n', '\\l').replace('\t', ' ' * 4)
            ))

            for link in block.tos.keys():
                output_file.write('\t\t{}\n'.format(self._generate_link(link)))
                blocks.append(link.to)
            output_file.write('\n')
            blocks_done.append(block)

        output_file.write('}\n')

    def _generate_link(self, link):
        return '{block1} -> {block2} [ {options} ];'.format(
            block1 = link.from_.uniq_name(),
            block2 = link.to.uniq_name(),
            options = 'color = {color}, tailport = s, headport = n'.format(
                color = link.link_type,
            )
        )
