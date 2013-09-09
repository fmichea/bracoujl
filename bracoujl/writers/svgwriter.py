# svgwriter.py - Dumps functions as several svg files.
# Author: Franck Michea < franck.michea@gmail.com >
# License: New BSD License (See LICENSE)

import os
import subprocess
import sys

import bracoujl.writers.writer as w
import bracoujl.writers.dotwriter as wdot

class SVGWriter(w.Writer):
    EXT = 'svg'

    def __init__(self, output_dir):
        rc = subprocess.call(['which', 'dot'])
        if rc != 0:
            sys.exit('error: dot was not found in your $PATH.')
        self._dw = wdot.DotWriter(output_dir)
        super().__init__(output_dir)

    def generate(self, function, output_filename=None):
        self._dw.generate(function)
        out = self.output_filename(function, output_filename)
        in_ = self._dw.output_filename(function)
        subprocess.call(['dot', '-Tsvg', in_, '-o', out])
