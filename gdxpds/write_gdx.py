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
import gdxpds.gdxdict as gdxdictimport loggingimport numpy as np
import pandas as pds
logger = logging.getLogger(__name__)
import gdxpds.tools

class Translator(object):
    def __init__(self, dataframes):
        self.dataframes = dataframes
    
    @property
    def dataframes(self):
        return self.__dataframes
        
    @dataframes.setter
    def dataframes(self, value):
        if not isinstance(value, dict):
            raise RuntimeError("Expecting dict of name, pandas.DataFrame pairs.")
        for symbol_name, df in value.items():
            if not isinstance(symbol_name, str):
                raise RuntimeError("Expecting dict of name, pandas.DataFrame pairs.")
            if not isinstance(df, pds.DataFrame):
                raise RuntimeError("Expecting dict of name, pandas.DataFrame pairs.")
        self.__dataframes = value
        self.__gdx = None
    
    @property
    def gdx(self):
        if self.__gdx is None:
            self.__gdx = gdxdict.gdxdict()
            for symbol_name, df in self.dataframes.items():
                self.__add_symbol_to_gdx(symbol_name, df)
        return self.__gdx
        
    def save_gdx(self, path, gams_dir = None):
        gdxpds.tools.GdxWriter(self.gdx, path, gams_dir).save()
        
    def __add_symbol_to_gdx(self, symbol_name, df):
        symbol_info = {}        if not df.columns[-1].lower().strip() == 'value':            raise RuntimeError("The last column must be labeled 'value' (case insensitive).")        is_set = True if isinstance(df.loc[0,df.columns[-1]], (bool, np.bool_)) else False
        symbol_info['name'] = symbol_name        symbol_info['typename'] = 'Set' if is_set else 'Parameter'
        symbol_info['dims'] = len(df.columns) - 1
        symbol_info['records'] = len(df.index)
        symbol_info['domain'] = []
        for col in df.columns:
            if not col.lower().strip() == 'value':
                symbol_info['domain'].append({'key': '*'})
                # If we register the domain names, it seems that gdxdict expects us
                # to explicitly create a Set symbol for each domain. (Something that
                # can be done as an enhancement.)
                # symbol_info['domain'].append({'key': col})
        self.__gdx.add_symbol(symbol_info)
        top_dim = self.__gdx[symbol_name]
        
        def add_data(dim, data):
            """
            Appends data, the row of a csv file, to dim, the data structure holding
            a gdx symbol.
            
            Parameters:
                - dim (gdxdict.gdxdim): top-level container for symbol data
                - data (pds.Series): row of csv data, with index being the dimension
                  name or 'value', and the corresponding value being the dimension's 
                  set element or the parameter value, respectively.
            """
            cur_dim = dim
            prev_value = None
            # each item in the series, except for the 'value', takes us farther into
            # a tree of gdxdict.gdxdim objects. each level of the tree represents a
            # dimension of the data. each actual value is at a leaf of the tree.
            for i, value in data.iteritems():
                assert cur_dim is not None
                if prev_value is None:
                    # initialize
                    if 'name' not in cur_dim.info:
                        cur_dim.info['name'] = i
                    else:
                        assert cur_dim.info['name'] == i
                    prev_value = value
                elif isinstance(i,basestring) and (i.lower().strip() == 'value'):
                    # finalize, that is
                    # register the value at the current level
                    assert prev_value not in cur_dim
                    cur_dim[prev_value] = value
                    # this should be the last item in the series
                    cur_dim = None
                else:
                    # in the middle of the Series,
                    # create or descend into the next level of the tree
                    new_dim = None
                    if prev_value in cur_dim:
                        # next level is already there, just grab it
                        new_dim = cur_dim[prev_value]
                        assert new_dim.info['name'] == i
                    else:
                        # make a new level of the tree by creating a node for prev_value
                        # that points down to the next dimension
                        new_dim = gdxdict.gdxdim(self.__gdx)
                        new_dim.info['name'] = i
                        cur_dim[prev_value] = new_dim
                    # prev_value will be used as a label, so make sure it is a string
                    prev_value = str(value)
                    cur_dim = new_dim
    
        # add each row to the gdx symbol
        for i, row in df.iterrows():
            add_data(top_dim, row)

def to_gdx(dataframes, path = None, gams_dir = None):
    """
    Parameters:
      - dataframes (map of pandas.DataFrame): symbol name to pandas.DataFrame 
        dict to be compiled into a single gdx file. Each DataFrame is assumed to 
        represent a single set or parameter. The last column must be the parameter's         value, or the set's listing of True/False, and must be labeled as (case         insensitive) 'value'. 
      - path (optional string): if provided, the gdx file will be written
        to this path
        
    Returns a gdxdict.gdxdict, which is defined in [py-gdx](https://github.com/geoffleyland/py-gdx).
    """
    translator = Translator(dataframes)
    if path is not None:
        translator.save_gdx(path, gams_dir)
    return translator.gdx
    