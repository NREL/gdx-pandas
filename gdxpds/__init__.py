# [LICENSE]
# Copyright (c) 2018, Alliance for Sustainable Energy.
# All rights reserved.
# 
# Redistribution and use in source and binary forms, 
# with or without modification, are permitted provided 
# that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above 
# copyright notice, this list of conditions and the 
# following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the 
# above copyright notice, this list of conditions and the 
# following disclaimer in the documentation and/or other 
# materials provided with the distribution.
# 
# 3. Neither the name of the copyright holder nor the 
# names of its contributors may be used to endorse or 
# promote products derived from this software without 
# specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND 
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, 
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF 
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR 
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, 
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, 
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) 
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE 
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# [/LICENSE]

__author__ = "Elaine T. Hale"
__email__ = "elaine.hale@nrel.gov"

from ._version import __version__

import logging
import sys

logger = logging.getLogger(__name__)

from gdxpds.tools import Error
from gdxpds.special import load_specials

def load_gdxcc(gams_dir=None):
    """
    Method to initialize GAMS, especially to load required libraries that can 
    sometimes conflict with other packages.

    Parameters
    ----------
    gams_dir : None or str
        if not None, directory containing the GAMS executable
    """
    if 'pandas' in sys.modules:
        logger.warning("Especially on Linux, gdxpds should be imported before " + \
                       "pandas to avoid a library conflict. Also make sure your " + \
                       "GAMS directory is listed in LD_LIBRARY_PATH.")
    import gdxcc
    from gdxpds.tools import GamsDirFinder
    finder = GamsDirFinder(gams_dir=gams_dir)
    H = gdxcc.new_gdxHandle_tp()
    rc = gdxcc.gdxCreateD(H,finder.gams_dir,gdxcc.GMS_SSSIZE)
    gdxcc.gdxFree(H)
    load_specials()
    return

try:
    load_gdxcc()
except:
    from gdxpds.tools import GamsDirFinder
    gams_dir = None
    try:
        gams_dir = GamsDirFinder().gams_dir
    except: pass
    logger.warning("Unable to load gdxcc with default GAMS directory '{}'. ".format(gams_dir) + \
                   "You may need to explicitly call gdxpds.load_gdxcc(gams_dir) " + \
                   "before importing pandas to avoid a library conflict.")


from gdxpds.read_gdx import to_dataframes, list_symbols, to_dataframe
from gdxpds.write_gdx import to_gdx
