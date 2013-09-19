# dotwriter.py - Writes the graph in dot format.
# Author: Franck Michea < franck.michea@gmail.com >
# License: New BSD License (See LICENSE)

import sys

import bracoujl.writers.writer as w

class DotWriter(w.Writer):
    EXT = 'dot'

    def generate(self, function, output_file=None):
        with self._output_file(function, output_file) as of:
            of.write('digraph {name} {{\n'.format(name=function.uniq_name()))
            of.write('\tsplines = true;\n')
            of.write('\tnode [ shape = box, fontname = "Deja Vu Sans Mono" ];\n\n')

            blocks, blocks_done = [function], []
            while blocks:
                block = blocks.pop()
                if block in blocks_done:
                    continue
                of.write('\t\t{block_name} [ label = "{code}\\l" ];\n'.format(
                    block_name = block.uniq_name(),
                    code = str(block).replace('\n', '\\l').replace('\t', ' ' * 4)
                ))

                for link in block.tos.keys():
                    of.write('\t\t{}\n'.format(self._generate_link(link)))
                    blocks.append(link.to)
                of.write('\n')
                blocks_done.append(block)

            of.write('}\n')

    def _generate_link(self, link):
        opts = 'color = {color}, tailport = s, headport = n, label = "{l}"'.format(
            color = link.link_type, l=link.from_.tos[link],
        )
        return '{block1} -> {block2} [ {options} ];'.format(
            block1 = link.from_.uniq_name(),
            block2 = link.to.uniq_name(),
            options = opts,
        )
