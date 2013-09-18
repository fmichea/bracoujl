#! /usr/bin/env python

# Author: Franck Michea < franck.michea@gmail.com >
# License: New BSD License (See LICENSE)

import argparse
import os
import subprocess
import sys

import bracoujl.graph as bg

import bracoujl.writers.dotwriter as bwd
import bracoujl.writers.svgwriter as bws

def main():
    parser = argparse.ArgumentParser(description='Some debugging tool.')
    parser.add_argument('-o', '--output-dir', action='store', required=False,
                        metavar='dir', help='output directory')
#    parser.add_argument('-s', '--serialize', action='store_true', required=False,
#                        help='create a serialized version of the graphs.')

    group = parser.add_argument_group('actions')
    group.add_argument('--dot', action='store_true', help='generate dot files')
    group.add_argument('--svg', action='store_true', help='generate svg files')
    group.add_argument('--cmp', action='store_true', help='compare two graphs')

    parser.add_argument('log', action='store', nargs='+',
                        help='log file correctly formatted')
    args = parser.parse_args(sys.argv[1:])

    if not (args.dot or args.svg or args.cmp):
        parser.error('Must precise at least --dot or --svg or --cmp.')

    output_dir = None
    if args.dot or args.svg:
        if not args.output_dir:
            parser.error('This option requires --output-dir')
        output_dir = os.path.abspath(args.output_dir)
        if not os.path.exists(output_dir):
            msg = 'I didn\'t find directory/symbolic link named `{path}` where '
            msg += 'to generate the graphs.'
            sys.exit(msg.format(path=output_dir))

    graphs, grapher = dict(), bg.Graph()
    for log in args.log:
#        functions = None
#        if args.serialize:
#            functions = grapher.unserialize(log)
#        if functions is None:
        functions = grapher.generate_graph(log)
#        if args.serialize:
#            grapher.serialize(log, functions)

        print('Found {} functions in {}:'.format(len(functions), log))
        for function in functions:
            print(' - {}'.format(function.name()))
        graphs[log] = functions

    dw, sw = bwd.DotWriter(output_dir), bws.SVGWriter(output_dir)
    for log in args.log:
        for function in graphs[log]:
            if args.svg:
                sw.generate(function)
            elif args.dot:
                dw.generate(function)

if __name__ == '__main__':
    main()
