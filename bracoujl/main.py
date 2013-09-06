#! /usr/bin/env python

# Author: Franck Michea < franck.michea@gmail.com >
# License: New BSD License (See LICENSE)

import argparse
import os
import sys

import bracoujl.graph as bg
import bracoujl.writers.dotwriter as bwd
#import bracoujl.writers.asciiwriter

def main():
    parser = argparse.ArgumentParser(description='Some debugging tool.')
    parser.add_argument('-o', '--output-dir', action='store', required=True,
                        metavar='dir', help='output directory')
    parser.add_argument('log', action='store', nargs='+',
                        help='log file correctly formatted')
    args = parser.parse_args(sys.argv[1:])

    output_dir = os.path.abspath(args.output_dir)
    if not os.path.exists(output_dir):
        msg = 'I didn\'t find directory/symbolic link named `{path}` where '
        msg += 'to generate the graphs.'
        sys.exit(msg.format(path=output_dir))

    for log in args.log:
        functions = bg.Graph().generate_graph(log)
        print('Found {} functions:'.format(len(functions)))

        dw = bwd.DotWriter()
        for function in functions:
            print(' - {}'.format(function.name()))
            if function.name() in ['sub_0216', 'int_0010']:
                with open(os.path.join(output_dir, function.uniq_name() + '.dot'), 'w') as f:
                    dw.generate_graph(f, function)

if __name__ == '__main__':
    main()
