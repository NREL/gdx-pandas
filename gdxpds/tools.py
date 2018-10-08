'''
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

    The find function first looks for the 'GAMS_DIR' environment variable. If 
    that is unsuccessful, it next uses 'which gams' for POSIX systems, and the 
    default install location, 'C:\GAMS', for Windows systems. In the latter case
    it prefers the largest version number.
    
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
        """
        Cleans up the path string.
        """
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
        For all systems, the first place we examine is the GAMS_DIR environment
        variable.

        For Windows, the next step is to look for the GAMS directory based on 
        the default install location (C:\GAMS). 
        
        For all others, the next step is 'which gams'.
        
        Returns
        -------
        str or None
            If not None, the return value is the found gams_dir
        """
        # check for environment variable
        ret = os.environ.get('GAMS_DIR')
        
        if ret is None:
            if os.name == 'nt':
                # windows systems
                # search in default installation location
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
    """
    Mix-in class that asserts that a GAMS directory is needed and provides the
    methods required to find and access it.

    Attributes
    ----------
    gams_dir : str
        The GAMS directory whose value has either been directly set or has been 
        found using the GamsDirFinder class.
    """
    def __init__(self,gams_dir=None):
        self.gams_dir = gams_dir
        
    @property
    def gams_dir(self):
        return self.__gams_dir
        
    @gams_dir.setter
    def gams_dir(self, value):
        self.__gams_dir = GamsDirFinder(value).gams_dir    

