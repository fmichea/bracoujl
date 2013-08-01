# svgwriter.py - Dumps functions as several svg files.
# Author: Franck Michea < franck.michea@gmail.com >
# License: New BSD License (See LICENSE)

import os
import subprocess
import sys

class SVGWriter(object):
    def __init__(self):
        self.tmp_dir = subprocess.check_output('mktemp -d', shell=True)
