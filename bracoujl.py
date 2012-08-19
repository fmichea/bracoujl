#! /usr/bin/env python

# Author: Franck Michea < franck.michea@gmail.com >
# License: New BSD License (See LICENSE)

import argparse
import os
import pickle
import re
import sys



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
