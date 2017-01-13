'''

[LICENSE]

Copyright (c) 2015, Alliance for Sustainable Energy.
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
import copy
import gc
import logging

import pandas as pds

import gdxpds.gdxdict as gdxdict
import gdxpds.tools

logger = logging.getLogger(__name__)

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
        logger.debug("Starting loading process. " + gdxpds.memory_use_str())
        
        # recursive helper function
        def collect_data(data, entry, dim):
            has_limits = False
            if isinstance(dim, float):
                data.append([dim])
                return has_limits
            assert isinstance(dim, gdxdict.gdxdim), 'dim is unexpected type {}'.format(type(dim))
            # cannot use dim.items.items() here, because skips the lazy_load feature
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
            
        logger.debug("Located {} symbol names. ".format(len(symbol_names)) + 
            gdxpds.memory_use_str())
            
        for symbol_name in symbol_names:
            symbol_info = self.gdx.getinfo(symbol_name)
            if symbol_info['records'] > 0:
                logger.debug('Processing symbol {} with {} records. '.format(symbol_name, symbol_info['records']) + 
                    gdxpds.memory_use_str())
                data = []; entry = []
                has_limits = collect_data(data,entry,self.gdx[symbol_name])
                cols = [d['key'] for d in symbol_info["domain"]]
                cols.append('value')
                if has_limits:
                    cols = cols + gdxdict.level_names
                self.__dataframes[symbol_name] = pds.DataFrame(data = data, columns = cols)
                if len(self.__dataframes[symbol_name].index) != symbol_info['records']:
                    logger.error("Dataframe containing {} contains {} records when expected {}".format(
                        symbol_name, len(self.__dataframes[symbol_name].index), symbol_info['records']))
                logger.debug('Complete. ' + gdxpds.memory_use_str())

def to_dataframes(gdx_file, gams_dir = None):
    """
    Primary interface for converting a GAMS GDX file to pandas DataFrames.
    
    Parameters:
      - gdx_file (string): path to a GDX file
      - gams_dir (string): optional path to GAMS directory
      
    Returns a dict of Pandas DataFrames, one item for each symbol in the GDX 
    file, keyed with the symbol name.
    """
    dfs = Translator(gdx_file, gams_dir).dataframes
    result = copy.deepcopy(dfs)
    gc.collect()
    return result
    
def list_symbols(gdx_file, gams_dir = None):
    """
    Returns the list of symbols available in gdx_file.
    
    Parameters:
      - gdx_file (string): path to a GDX file
      - gams_dir (string): optional path to GAMS directory      
    """
    symbols = Translator(gdx_file, gams_dir, lazy_load = True).symbols
    result = copy.deepcopy(symbols)
    gc.collect()
    return symbols
    
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
    df = copy.deepcopy(Translator(gdx_file, gams_dir, lazy_load = True).dataframe(symbol_name))
    result = copy.deepcopy(df)
    gc.collect()
    return result
    