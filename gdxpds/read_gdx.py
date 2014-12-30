import gdxpds.gdxdict as gdxdict
import pandas as pds

import gdxpds.tools

class Translator(object):
    def __init__(self, gdx_file, gams_dir = None, lazy_load = False):
        self.__gdx_loader = gdxpds.tools.GdxLoader(gdx_file, gams_dir, lazy_load)
        self.__dataframes = None
        
    @property
    def gams_dir(self):
        return self.__gdx_loader.gams_dir
        
    @gams_dir.setter
    def gams_dir(self, value):
        self.__gdx_loader.gams_dir = value
        
    @property 
    def gdx_file(self):
        return self.__gdx_loader.gdx_file
        
    @gdx_file.setter
    def gdx_file(self, value):
        self.__gdx_loader.gdx_file = value
        self.__dataframes = None
        
    @property
    def gdx(self):
        return self.__gdx_loader.gdx
        
    @property
    def dataframes(self):
        if self.__dataframes is None:
            self.__translate()
        return self.__dataframes
        
    @property
    def symbols(self):
        return [symbol_name for symbol_name in self.gdx]
        
    def dataframe(self, symbol_name):
        if not symbol_name in self.symbols:
            raise RuntimeError("No symbol named '{}' in '{}'.".format(symbol_name, self.gdx_file))
        if (self.__dataframes is None) or (not symbol_name in self.__dataframes):
            self.__translate(symbol_name)
        return { symbol_name: self.__dataframes[symbol_name] }
                
    def __translate(self, symbol_name = None):    
        # recursive helper function
        def collect_data(data, entry, dim):
            assert isinstance(dim, gdxdict.gdxdim)
            # cannot use dim.items.items() here, because skips the lazy_load feature
            has_limits = False
            for key in dim:
                key_name = self.gdx.universal[key.lower()]['name']
                value = dim[key]
                if isinstance(value,gdxdict.gdxdim):
                    has_limits = collect_data(data,entry + [key_name],value)
                else:
                    row = entry + [key_name, value]
                    if 'limits' in dim.getinfo(key_name):
                        for limit_name, limit_value in dim.getinfo(key_name)['limits'].items():
                            row += [limit_value]
                        has_limits = True
                    data.append(row)
            return has_limits
        
        # main body   
        if self.__dataframes is None:
            self.__dataframes = {}

        symbol_names = None
        if symbol_name is None:
            symbol_names = self.symbols
        else:
            symbol_names = [symbol_name]
            
        for symbol_name in symbol_names:
            symbol_info = self.gdx.getinfo(symbol_name)
            if symbol_info['records'] > 0:
                data = []; entry = []
                has_limits = collect_data(data,entry,self.gdx[symbol_name])
                cols = [d['key'] for d in symbol_info["domain"]]
                cols.append('value')
                if has_limits:
                    cols = cols + gdxdict.level_names
                self.__dataframes[symbol_name] = pds.DataFrame(data = data, columns = cols)

def to_dataframes(gdx_file, gams_dir = None):
    """
    Primary interface for converting a GAMS GDX file to pandas DataFrames.
    
    Parameters:
      - gdx_file (string): path to a GDX file
      - gams_dir (string): optional path to GAMS directory
      
    Returns a dict of Pandas DataFrames, one item for each symbol in the GDX 
    file, keyed with the symbol name.
    """
    return Translator(gdx_file, gams_dir).dataframes
    
def list_symbols(gdx_file, gams_dir = None):
    """
    Returns the list of symbols available in gdx_file.
    
    Parameters:
      - gdx_file (string): path to a GDX file
      - gams_dir (string): optional path to GAMS directory      
    """
    return Translator(gdx_file, gams_dir, lazy_load = True).symbols
    
def to_dataframe(gdx_file, symbol_name, gams_dir = None):
    """
    Interface for getting the { symbol_name: pandas.DataFrame } dict for a 
    single symbol.
    
    Parameters:
      - gdx_file (string): path to a GDX file
      - symbol_name (string): symbol whose pandas.DataFrame is being requested
      - gams_dir (string): optional path to GAMS directory    
      
    Returns a dict with a single entry, where the key is symbol_name and the
    value is the corresponding pandas.DataFrame.
    """
    return Translator(gdx_file, gams_dir, lazy_load = True).dataframe(symbol_name)
    