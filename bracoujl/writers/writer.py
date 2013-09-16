# writer.py - Abstraction layer for writers.
# Author: Franck Michea < franck.michea@gmail.com >
# License: New BSD License (See LICENSE)

import os

from contextlib import contextmanager

class Writer:
    def __init__(self, output_dir):
        self._output_dir = output_dir or '.'

    @contextmanager
    def _output_file(self, ext, function, output_file=None):
        if output_file:
            yield output_file
        else:
            f = open(self.output_filename(ext, function), 'w')
            try:
                yield f
            finally:
                f.close()

    def output_filename(self, function, output_filename=None):
        if output_filename is not None:
            return output_filename
        filename = function.uniq_name() + '.' + self.EXT
        output_filename = os.path.join(self._output_dir, filename)
        return output_filename
