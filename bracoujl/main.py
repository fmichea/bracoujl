#! /usr/bin/env python

# Author: Franck Michea < franck.michea@gmail.com >
# License: New BSD License (See LICENSE)

import argparse
import os
import sys

import bracoujl.graph
import bracoujl.writers.dotwriter
import bracoujl.writers.asciiwriter

def main():
    parser = argparse.ArgumentParser(description='Some debugging tool.')
    parser.add_argument('-o', '--output', action='store', required=True,
                        metavar='dir', help='output directory')
    parser.add_argument('log', action='append', nargs='+',
                        help='log file correctly formatted')
    args = parser.parse_args(sys.argv[1:])


if __name__ == '__main__':
    main()
