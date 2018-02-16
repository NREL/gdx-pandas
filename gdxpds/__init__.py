'''
[LICENSE]

Copyright (c) 2017, Alliance for Sustainable Energy.
All rights reserved.

Redistribution and use in source and binary forms, 
with or without modification, are permitted provided 
that the following conditions are met:

1. Redistributions of source code must retain the above 
copyright notice, this list of conditions and the 
following disclaimer.

2. Redistributions in binary form must reproduce the 
above copyright notice, this list of conditions and the 
following disclaimer in the documentation and/or other 
materials provided with the distribution.

3. Neither the name of the copyright holder nor the 
names of its contributors may be used to endorse or 
promote products derived from this software without 
specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND 
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, 
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF 
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR 
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, 
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, 
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) 
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE 
OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

[/LICENSE]



'''


__version__ = '1.0.3'

import logging
import os
import sys

logger = logging.getLogger(__name__)

from gdxpds.tools import Error

def load_gdxcc(gams_dir=None):
    if 'pandas' in sys.modules:
        logger.warn("Especially on Linux, gdxpds should be imported before " + \
                    "pandas to avoid a library conflict. Also make sure your " + \
                    "GAMS directory is listed in LD_LIBRARY_PATH.")
    import gdxcc
    from gdxpds.tools import GamsDirFinder
    finder = GamsDirFinder(gams_dir=gams_dir)
    H = gdxcc.new_gdxHandle_tp()
    rc = gdxcc.gdxCreateD(H,finder.gams_dir,gdxcc.GMS_SSSIZE)
    gdxcc.gdxFree(H)
    return

try:
    load_gdxcc()
except:
    from gdxpds.tools import GamsDirFinder
    gams_dir = None
    try:
        gams_dir = GamsDirFinder().gams_dir
    except: pass
    logger.warn("Unable to load gdxcc with default GAMS directory '{}'. ".format(gams_dir) + \
                "You may need to explicitly call gdxpds.load_gdxcc(gams_dir) " + \
                "before importing pandas to avoid a library conflict.")


from gdxpds.read_gdx import to_dataframes
from gdxpds.read_gdx import list_symbols
from gdxpds.read_gdx import to_dataframe
from gdxpds.write_gdx import to_gdx

HAVE_PSUTIL = False
try:
    import psutil
    HAVE_PSUTIL = True
except ImportError:
    logger.info("Optional package psutil not found. pip install psutil if " + \
                "you would like to monitor memory usage.")

def memory_use_str(pid=None):
    if HAVE_PSUTIL:
        pid = os.getpid() if pid is None else pid
        rss = psutil.Process(pid).memory_info().rss
        return "Process {} using {:.2f} GB of memory.".format(pid, float(rss) / (1024.0**3))
    return "Feature unavailable."
