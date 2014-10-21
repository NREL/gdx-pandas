import gdxdict

import os
import subprocess as subp
import re

class GamsDirFinder(object):
    """
    Class for finding and accessing the system's GAMS directory. 
    
    The find function is currently based on 'which gams' for POSIX systems, and on
    the default install location, 'C:\GAMS', for Windows systems. 
    
    You can always specify the GAMS directory directly, and this class will attempt 
    to clean up your input. (Even on Windows, the GAMS path must use '/' rather than 
    '\'.)
    """
    def __init__(self, gams_dir = None):
        self.gams_dir = gams_dir
        
    @property
    def gams_dir(self):
        """The GAMS directory on this system."""
        if self._gams_dir is None:
            raise RuntimeError("Unable to locate your GAMS directory.")
        return self._gams_dir
        
    @gams_dir.setter
    def gams_dir(self, value):
        self._gams_dir = None
        if isinstance(value,str):
            self._gams_dir = self._clean_gams_dir(value)
        if self._gams_dir is None:
            self._gams_dir = self._find_gams()
            
    def _clean_gams_dir(self,value):
        assert(isinstance(value,str))
        ret = os.path.realpath(value)
        if not os.path.exists(ret):
            return None
        ret = re.sub('\\\\','/',ret)
        return ret
        
    def _find_gams(self):
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
            ret = self._clean_gams_dir(ret)
            
        return ret
        
class NeedsGamsDir(object):
    def __init__(self, gams_dir = None):
        self.gams_dir = gams_dir
        
    @property
    def gams_dir(self):
        return self._gams_dir
        
    @gams_dir.setter
    def gams_dir(self, value):
        self._gams_dir = GamsDirFinder(value).gams_dir    

class GdxLoader(NeedsGamsDir):
    def __init__(self, gdx_file, gams_dir = None):
        self.gdx_file = gdx_file
        super(GdxLoader, self).__init__(gams_dir)
        
    @property 
    def gdx_file(self):
        return self._gdx_file

    @gdx_file.setter
    def gdx_file(self, value):
        if not os.path.exists(value):
            raise RuntimeError("The GDX file '{}' does not exist.".format(value))
        self._gdx_file = value
        self._gdx = None
        
    @property
    def gdx(self):
        if self._gdx is None:
            self._gdx = gdxdict.gdxdict()
            self._gdx.read(self.gdx_file, self.gams_dir)
        return self._gdx
        
class GdxWriter(NeedsGamsDir):
    def __init__(self, gdx, path, gams_dir = None):
        self.gdx = gdx
        self.path = path
        super(GdxWriter, self).__init__(gams_dir)
        
    @property
    def gdx(self):
        return self._gdx
        
    @gdx.setter
    def gdx(self, value):
        if not isinstance(value, gdxdict.gdxdict):
            raise RuntimeError("Expected GDX file loaded as a gdxdict.gdxdict.")
        self._gdx = value
        
    @property
    def path(self):
        return self._path
        
    @path.setter
    def path(self, value):
        if not os.path.exists(os.path.dirname(value)):
            raise RuntimeError("Parent directory of '{}' does not exist. Please create before trying to save a gdx file there.".format(value))
        if os.path.exists(value) and os.path.isdir(value):
            raise RuntimeError("Cannot save a GDX file to '{}', as it is a directory.".format(value))
        self._path = value
        
    def save(self):
        if os.path.isfile(self.path):
            os.remove(self.path)
        self.gdx.write(self.path, self.gams_dir)
