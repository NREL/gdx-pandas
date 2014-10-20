import gdxdict
import pandas as pds

import gdxpds.tools

class Translator:
    def __init__(self, dataframes):
        self.dataframes = dataframes
    
    @property
    def dataframes(self):
        return self._dataframes
        
    @dataframes.setter
    def dataframes(self, value):
        if not isinstance(value, dict):
            RuntimeError("Expecting dict of name, pandas.DataFrame pairs.")
        for symbol_name, df in value:
            if not isinstance(symbol_name, str):
                RuntimeError("Expecting dict of name, pandas.DataFrame pairs.")
            if not isinstance(df, pds.DataFrame):
                RuntimeError("Expecting dict of name, pandas.DataFrame pairs.")
        self._dataframes = value
        self._gdx = None
    
    @property
    def gdx(self):
        if self._gdx is None:
            self._gdx = gdxdict.gdxdict()
            for symbol_name, df in self.dataframes:
                self._add_symbol_to_gdx(symbol_name, df)
        return self._gdx
        
    def save_gdx(self, path, gams_dir = None):
        gdxpds.tools.GdxWriter(self.gdx, path, gams_dir).save()
        
    def _add_symbol_to_gdx(symbol_name, df):
        symbol_info = {}
        symbol_info['name'] = symbol_name
        symbol_info['typename'] = 'Parameter'
        symbol_info['dims'] = len(df.columns) - 1
        symbol_info['records'] = len(df.index)
        symbol_info['domain'] = []
        for col in df.columns:
            if not col == 'value':
                symbol_info['domain'].append({'key': '*'})
                # If we register the domain names, it seems that gdxdict expects us
                # to explicitly create a Set symbol for each domain. (Something that
                # can be done as an enhancement.)
                # symbol_info['domain'].append({'key': col})
        self._gdx.add_symbol(symbol_info)
        top_dim = self._gdx[symbol_name]
        
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
                elif i == 'value':
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
                        new_dim = gdxdict.gdxdim(cur_dim)
                        new_dim.info['name'] = i
                        cur_dim[prev_value] = new_dim
                    prev_value = value
                    cur_dim = new_dim
    
        # add each row to the gdx symbol
        for i, row in df.iterrows():
            add_data(top_dim, row)

def to_gdx(dataframes, path = None, gams_dir = None):
    """
    Parameters:
      - dataframes (map of pandas.DataFrame): symbol name to pandas.DataFrame 
        dict to be compiled into a single gdx file
      - path (optional string): if provided, the gdx file will be written
        to this path
        
    Returns a gdxdict.gdxdict, which is defined in [py-gdx](https://github.com/geoffleyland/py-gdx).
    """
    translator = Translator(dataframes)
    if path is not None:
        translator.save_gdx(path, gams_dir)
    return translator.gdx
    