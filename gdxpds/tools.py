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

import logging
import os
import subprocess as subp
import re
from six import PY2, string_types, text_type

logger = logging.getLogger(__name__)


class Error(Exception): 
    """
    Base class for all Exceptions raised by this package.
    """

class GamsDirFinder(object):
    """
    Class for finding and accessing the system's GAMS directory. 
    
    The find function is currently based on 'which gams' for POSIX systems, and on
    the default install location, 'C:\GAMS', for Windows systems. 
    
    You can always specify the GAMS directory directly, and this class will attempt 
    to clean up your input. (Even on Windows, the GAMS path must use '/' rather than 
    '\'.)
    """
    gams_dir_cache = None

    def __init__(self,gams_dir=None):
        self.gams_dir = gams_dir
        
    @property
    def gams_dir(self):
        """The GAMS directory on this system."""
        if self.__gams_dir is None:
            raise RuntimeError("Unable to locate your GAMS directory.")
        return self.__gams_dir
        
    @gams_dir.setter
    def gams_dir(self, value):
        self.__gams_dir = None
        if isinstance(value,string_types):
            self.__gams_dir = self.__clean_gams_dir(value)
        if self.__gams_dir is None:
            self.__gams_dir = self.__find_gams()
            
    def __clean_gams_dir(self,value):
        assert(isinstance(value,string_types))
        ret = os.path.realpath(value)
        if not os.path.exists(ret):
            return None
        ret = re.sub('\\\\','/',ret)
        if PY2 and isinstance(ret, text_type):
            ret = ret.encode('ascii','replace')
        return ret
        
    def __find_gams(self):
        """
        For Windows, looks for the GAMS directory based on the default install location
        (C:\GAMS). 
        
        For all others, uses 'which gams'.
        
        Returns the found gams_dir, or None.
        """
        ret = None
        
        if os.name == 'nt':
            # windows systems
            cur_dir = 'C:\GAMS'
            if os.path.exists(cur_dir):
                # level 1 - prefer win64 to win32
                for p, dirs, files in os.walk(cur_dir):
                    if 'win64' in dirs:
                        cur_dir = os.path.join(cur_dir, 'win64')
                    elif len(dirs) > 0:
                        cur_dir = os.path.join(cur_dir, dirs[0])
                    else:
                        return ret
                    break
            if os.path.exists(cur_dir):
                # level 2 - prefer biggest number (most recent version)
                for p, dirs, files in os.walk(cur_dir):
                    if len(dirs) > 1:
                        try:
                            versions = [float(x) for x in dirs]
                            ret = os.path.join(cur_dir, "{}".format(max(versions)))
                        except:
                            ret = os.path.join(cur_dir, dirs[0])
                    elif len(dirs) > 0:
                        ret = os.path.join(cur_dir, dirs[0])
                    break
        else:
            # posix systems
            try:
                ret = os.path.dirname(subp.check_output(['which', 'gams'])).decode()
            except:
                ret = None
                
        if ret is not None:
            ret = self.__clean_gams_dir(ret)
            GamsDirFinder.gams_dir_cache = ret

        if ret is None:
            logger.debug("Did not find GAMS directory. Using cached value {}.".format(self.gams_dir_cache))
            ret = GamsDirFinder.gams_dir_cache
            
        return ret
        
class NeedsGamsDir(object):
    def __init__(self,gams_dir=None):
        self.gams_dir = gams_dir
        
    @property
    def gams_dir(self):
        return self.__gams_dir
        
    @gams_dir.setter
    def gams_dir(self, value):
        self.__gams_dir = GamsDirFinder(value).gams_dir    

