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

from ctypes import c_bool
import copy
import logging
import os
import subprocess as subp

import gdxpds.gdx
import gdxpds.special
from gdxpds.test import base_dir, run_dir
from gdxpds.test.test_session import manage_rundir
from gdxpds.test.test_conversions import roundtrip_one_gdx

import gdxcc
import numpy as np
import pandas as pds
import pytest

logger = logging.getLogger(__name__)

def value_column_index(sym,gams_value_type):
    for i, val in enumerate(sym.value_cols):
        if val[1] == gams_value_type.value:
            break
    return len(sym.dims) + i

def test_roundtrip_just_special_values(manage_rundir):
    outdir = os.path.join(run_dir,'special_values')
    if not os.path.exists(outdir):
        os.mkdir(outdir)
    # create gdx file containing all special values
    with gdxpds.gdx.GdxFile() as f:
        df = pds.DataFrame([['sv' + str(i+1), gdxpds.special.SPECIAL_VALUES[i]] for i in range(gdxcc.GMS_SVIDX_MAX-2)],
                           columns=['sv','Value'])
        logger.info("Special values are:\n{}".format(df))

        # save this directly as a GdxSymbol
        filename = os.path.join(outdir,'direct_write_special_values.gdx')
        ret = gdxcc.gdxOpenWrite(f.H,filename,"gdxpds")
        if not ret:
            raise gdxpds.gdx.GdxError(f.H,"Could not open {} for writing. Consider cloning this file (.clone()) before trying to write".format(repr(filename)))
        # write the universal set
        f.universal_set.write()
        if not gdxcc.gdxDataWriteStrStart(f.H,
                                          'special_values',
                                          '',
                                          1,
                                          gdxpds.gdx.GamsDataType.Parameter.value,
                                          0):
            raise gdxpds.gdx.GdxError(f.H,"Could not start writing data for symbol special_values")
        # set domain information
        if not gdxcc.gdxSymbolSetDomainX(f.H,1,[df.columns[0]]):
            raise gdxpds.gdx.GdxError(f.H,"Could not set domain information for special_values.")
        values = gdxcc.doubleArray(gdxcc.GMS_VAL_MAX)
        for row in df.itertuples(index=False,name=None):
            dims = [str(x) for x in row[:1]]
            vals = row[1:]
            for col_name, col_ind in gdxpds.gdx.GAMS_VALUE_COLS_MAP[gdxpds.gdx.GamsDataType.Parameter]:
                values[col_ind] = float(vals[col_ind])
            gdxcc.gdxDataWriteStr(f.H,dims,values)
        gdxcc.gdxDataWriteDone(f.H)
        gdxcc.gdxClose(f.H)

    # general test for expected values
    def check_special_values(gdx_file):
        df = gdx_file['special_values'].dataframe
        for i, val in enumerate(df['Value'].values):
            assert gdxpds.special.pd_val_equal(val, gdxpds.special.NUMPY_SPECIAL_VALUES[i])

    # now roundtrip it gdx-only
    with gdxpds.gdx.GdxFile(lazy_load=False) as f:
        f.read(filename)
        check_special_values(f)
        with f.clone() as g:
            rt_filename = os.path.join(outdir,'roundtripped.gdx')
            g.write(rt_filename)
    with gdxpds.gdx.GdxFile(lazy_load=False) as g:
        g.read(filename)
        check_special_values(g)

    # now roundtrip it through csv
    roundtripped_gdx = roundtrip_one_gdx(filename,'roundtrip_just_special_values')
    with gdxpds.gdx.GdxFile(lazy_load=False) as h:
        h.read(roundtripped_gdx)
        check_special_values(h)
    

def test_roundtrip_special_values(manage_rundir):
    filename = 'OptimalCSPConfig_Out.gdx'
    original_gdx = os.path.join(base_dir,filename)
    roundtripped_gdx = roundtrip_one_gdx(filename,'roundtrip_special_values')
    data = []
    for gdx_file in [original_gdx, roundtripped_gdx]:
        with gdxpds.gdx.GdxFile(lazy_load=False) as gdx:
            data.append([])
            gdx.read(gdx_file)
            sym = gdx['calculate_capacity_value']
            assert sym.data_type == gdxpds.gdx.GamsDataType.Equation
            val = sym.dataframe.iloc[0,value_column_index(sym,gdxpds.gdx.GamsValueType.Marginal)]
            assert gdxpds.special.is_np_sv(val)
            data[-1].append(val)
            sym = gdx['CapacityValue']
            assert sym.data_type == gdxpds.gdx.GamsDataType.Variable
            val = sym.dataframe.iloc[0,value_column_index(sym,gdxpds.gdx.GamsValueType.Upper)]
            assert gdxpds.special.is_np_sv(val)
            data[-1].append(val)
    data = list(zip(*data))
    for pt in data:
        for i in range(1,len(pt)):
            assert (pt[i] == pt[0]) or (np.isnan(pt[i]) and np.isnan(pt[0]))

def test_from_scratch_sets(manage_rundir):
    outdir = os.path.join(run_dir,'from_scratch_sets')
    if not os.path.exists(outdir):
        os.mkdir(outdir)
    with gdxpds.gdx.GdxFile() as gdx:
        gdx.append(gdxpds.gdx.GdxSymbol('my_set',gdxpds.gdx.GamsDataType.Set,dims=['u']))
        data = pds.DataFrame([['u' + str(i)] for i in range(1,11)])
        data['Value'] = True
        gdx[-1].dataframe = data
        assert isinstance(gdx[-1].dataframe[gdx[-1].dataframe.columns[-1]].values[0], c_bool)
        gdx.append(gdxpds.gdx.GdxSymbol('my_other_set',gdxpds.gdx.GamsDataType.Set,dims=['u']))
        data = pds.DataFrame([['u' + str(i)] for i in range(1,11)],columns=['u'])
        data['Value'] = True
        gdx[-1].dataframe = gdx[-1].dataframe.append(data)        
        gdx.write(os.path.join(outdir,'my_sets.gdx'))
    with gdxpds.gdx.GdxFile(lazy_load=False) as gdx:
        gdx.read(os.path.join(outdir,'my_sets.gdx'))
        for sym in gdx:
            assert sym.num_dims == 1
            assert sym.dims[0] == 'u'
            assert sym.data_type == gdxpds.gdx.GamsDataType.Set
            assert sym.num_records == 10
            assert isinstance(sym.dataframe[sym.dataframe.columns[-1]].values[0],c_bool)

def test_special_integrity():
    """
    Check that the special values line up
    """
    assert all(sv in gdxpds.special.GDX_TO_NP_SVS for sv in gdxpds.special.SPECIAL_VALUES)
    assert all(sv in gdxpds.special.NP_TO_GDX_SVS for sv in gdxpds.special.NUMPY_SPECIAL_VALUES)

    for val in gdxpds.special.SPECIAL_VALUES:
        assert gdxpds.special.NP_TO_GDX_SVS[gdxpds.special.GDX_TO_NP_SVS[val]] == val

    for val in gdxpds.special.NUMPY_SPECIAL_VALUES:
        # Can't use "==", as None != NaN
        assert gdxpds.special.pd_val_equal(gdxpds.special.GDX_TO_NP_SVS[gdxpds.special.NP_TO_GDX_SVS[val]], val)

def test_numpy_eps():
    assert(gdxpds.special.is_np_eps(np.finfo(float).eps))
    assert(not gdxpds.special.is_np_eps(float(0.0)))
    assert(not gdxpds.special.is_np_eps(2.0 * np.finfo(float).eps))

def test_unnamed_dimensions(manage_rundir):
    outdir = os.path.join(run_dir,'unnamed_dimensions')
    if not os.path.exists(outdir):
        os.mkdir(outdir)
    # create a gdx file with all symbol types and 4 dimensions named '*'
    cols = ['*'] * 4
    some_entries = pds.DataFrame([['tech_1','year_2','low','h1'],
                                  ['tech_1','year_2','low','h2'],
                                  ['tech_1','year_2','low','h3'],
                                  ['tech_1','year_2','low','h4']],
                                 columns = cols)
    with gdxpds.gdx.GdxFile() as gdx:
        # Set
        gdx.append(gdxpds.gdx.GdxSymbol('star_set',gdxpds.gdx.GamsDataType.Set,dims=4))
        gdx[-1].dataframe[cols] = some_entries
        # Parmeter
        a_param = copy.deepcopy(some_entries)
        a_param['Value'] = [1.0,2.0,3.0,4.0]
        gdx.append(gdxpds.gdx.GdxSymbol('star_param',gdxpds.gdx.GamsDataType.Parameter,dims=4))
        gdx[-1].dataframe = a_param
        # Test changing the parameter data
        a_param.iloc[:,0] = 'tech_2'
        gdx[-1].dataframe = pds.concat([gdx[-1].dataframe,a_param])
        # Variable
        gdx.append(gdxpds.gdx.GdxSymbol('star_var',gdxpds.gdx.GamsDataType.Variable,dims=4,
                   variable_type=gdxpds.gdx.GamsVariableType.Positive))
        a_var = copy.deepcopy(some_entries)
        for value_col_name in gdx[-1].value_col_names:
            a_var[value_col_name] = gdx[-1].get_value_col_default(value_col_name)
        gdx[-1].dataframe = a_var
        # Equation
        gdx.append(gdxpds.gdx.GdxSymbol('star_eqn',gdxpds.gdx.GamsDataType.Equation,dims=4,
                   equation_type=gdxpds.gdx.GamsEquationType.GreaterThan))
        an_eqn = copy.deepcopy(some_entries)
        for value_col_name in gdx[-1].value_col_names:
            an_eqn[value_col_name] = gdx[-1].get_value_col_default(value_col_name)
        gdx[-1].dataframe = an_eqn
        gdx.write(os.path.join(outdir,'star_symbols.gdx'))
    with gdxpds.gdx.GdxFile(lazy_load=False) as gdx:
        gdx.read(os.path.join(outdir,'star_symbols.gdx'))
        assert gdx['star_set'].num_dims == 4
        assert gdx['star_set'].data_type == gdxpds.gdx.GamsDataType.Set
        assert gdx['star_set'].variable_type is None
        assert gdx['star_set'].equation_type is None
        assert gdx['star_param'].num_dims == 4
        assert gdx['star_param'].data_type == gdxpds.gdx.GamsDataType.Parameter
        assert gdx['star_param'].variable_type is None
        assert gdx['star_param'].equation_type is None
        assert gdx['star_var'].num_dims == 4
        assert gdx['star_var'].data_type == gdxpds.gdx.GamsDataType.Variable
        assert gdx['star_var'].variable_type == gdxpds.gdx.GamsVariableType.Positive
        assert gdx['star_var'].equation_type is None
        assert gdx['star_eqn'].num_dims == 4
        assert gdx['star_eqn'].data_type == gdxpds.gdx.GamsDataType.Equation
        assert gdx['star_eqn'].variable_type is None
        assert gdx['star_eqn'].equation_type == gdxpds.gdx.GamsEquationType.GreaterThan

def test_setting_dataframes(manage_rundir):
    outdir = os.path.join(run_dir,'setting_dataframes')
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    with gdxpds.gdx.GdxFile() as gdx:
        # reading is tested elsewhere. here go through the different ways to
        # set a dataframe. 
        
        # start with WAYS THAT WORK:
        # 0 dims
        #     full dataframe
        gdx.append(gdxpds.gdx.GdxSymbol('sym_1',gdxpds.gdx.GamsDataType.Parameter))
        gdx[-1].dataframe = pds.DataFrame([[2.0]])
        assert list(gdx[-1].dataframe.columns) == ['Value']
        #     edit initialized dataframe - Parameter
        gdx.append(gdxpds.gdx.GdxSymbol('sym_2',gdxpds.gdx.GamsDataType.Parameter))
        n = len(gdx[-1].dataframe.columns)
        gdx[-1].dataframe['Value'] = [5.0] # list is required to specify number of rows to make
        assert n == len(gdx[-1].dataframe.columns)
        #     list of lists
        gdx.append(gdxpds.gdx.GdxSymbol('sym_3',gdxpds.gdx.GamsDataType.Variable))
        values = [3.0]
        for value_col_name in gdx[-1].value_col_names:
            if value_col_name == 'Level':
                continue
            values.append(gdx[-1].get_value_col_default(value_col_name))
        gdx[-1].dataframe = [values]
        #     reset with empty list
        gdx.append(gdxpds.gdx.GdxSymbol('sym_4',gdxpds.gdx.GamsDataType.Parameter))
        gdx[-1].dataframe = pds.DataFrame([[1.0]])
        gdx[-1].dataframe = []
        assert gdx[-1].num_records == 0

        # > 0 dims - GdxSymbol initialized with dims=0
        #     full dataframe
        gdx.append(gdxpds.gdx.GdxSymbol('sym_5',gdxpds.gdx.GamsDataType.Parameter))
        gdx[-1].dataframe = pds.DataFrame([['u1','CC',8727.2],
                                           ['u2','CC',7500.2],
                                           ['u3','CT',9258.0]], 
                                          columns=['u','q','val'])
        assert gdx[-1].num_dims == 2
        assert gdx[-1].num_records == 3
        #     full list of lists
        gdx.append(gdxpds.gdx.GdxSymbol('sym_6',gdxpds.gdx.GamsDataType.Parameter))
        gdx[-1].dataframe = [['u1','CC',8727.2],
                             ['u2','CC',7500.2],
                             ['u3','CT',9258.0],
                             ['u4','Coal',10100.0]]
        assert gdx[-1].num_dims == 2
        assert gdx[-1].num_records == 4
        #     reset with empty list
        gdx.append(gdxpds.gdx.GdxSymbol('sym_7',gdxpds.gdx.GamsDataType.Parameter))
        gdx[-1].dataframe = gdx[-2].dataframe.copy()
        gdx[-1].dataframe = []
        assert gdx[-1].num_dims == 2
        assert gdx[-1].num_records == 0

        # > 0 dims - GdxSymbol initialized with dims=n
        #     dataframe of dims
        gdx.append(gdxpds.gdx.GdxSymbol('sym_8',gdxpds.gdx.GamsDataType.Variable,
            dims=3,variable_type=gdxpds.gdx.GamsVariableType.Positive))
        gdx[-1].dataframe = pds.DataFrame([['u0','BES','c2'],
                                           ['u0','BES','c1'],
                                           ['u1','BES','c2']])
        assert gdx[-1].num_dims == 3;
        assert gdx[-1].dims == ['*','*','*']
        assert len(gdx[-1].dataframe.columns) > 3
        gdx[-1].dataframe[gdxpds.gdx.GamsValueType.Level.name] = 1.0
        gdx[-1].dataframe[gdxpds.gdx.GamsValueType.Upper.name] = 10.0
        #     full dataframe
        gdx.append(gdxpds.gdx.GdxSymbol('sym_9',gdxpds.gdx.GamsDataType.Parameter,
            dims=3))
        gdx[-1].dataframe = pds.DataFrame([['u0','BES','c2',2.0],
                                           ['u0','BES','c1',1.0],
                                           ['u1','BES','c2',2.0]],
                                          columns=['u','q','c','storage_duration_h'])
        assert list(gdx[-1].dataframe.columns) == ['u','q','c','Value']
        #     list of lists containing dims only
        gdx.append(gdxpds.gdx.GdxSymbol('sym_10',gdxpds.gdx.GamsDataType.Equation,
            dims=4,equation_type=gdxpds.gdx.GamsEquationType.LessThan))
        gdx[-1].dataframe = [['u0','PHES','c0','1'],
                             ['u0','PHES','c0','2'],
                             ['u0','PHES','c0','3'],
                             ['u0','PHES','c0','4'],
                             ['u0','PHES','c0','5']]
        gdx[-1].dataframe['Level'] = -15.0
        assert list(gdx[-1].dataframe.columns[:gdx[-1].num_dims]) == ['*'] * 4
        #     full list of lists
        gdx.append(gdxpds.gdx.GdxSymbol('sym_11',gdxpds.gdx.GamsDataType.Set,
            dims=2))
        gdx[-1].dataframe = [['PV','c0',True],
                             ['CSP','c0',False],
                             ['CSP','c1',False],
                             ['Wind','c0',True]]
        assert gdx[-1].num_dims == 2
        #     reset with empty list
        gdx.append(gdxpds.gdx.GdxSymbol('sym_12',gdxpds.gdx.GamsDataType.Set,
            dims=2))
        gdx[-1].dataframe = gdx[-1].dataframe.copy()
        gdx[-1].dataframe = []
        assert gdx[-1].num_dims == 2
        assert gdx[-1].dims == ['*'] * 2
        assert gdx[-1].num_records == 0

        # > 0 dims - GdxSymbol initialized with dims=[list of actual dims]
        #     dataframe of dims
        gdx.append(gdxpds.gdx.GdxSymbol('sym_13',gdxpds.gdx.GamsDataType.Variable,
            dims=['u','q','c'],variable_type=gdxpds.gdx.GamsVariableType.Positive))
        gdx[-1].dataframe = pds.DataFrame([['u0','BES','c2'],
                                           ['u0','BES','c1'],
                                           ['u1','BES','c2']])
        assert gdx[-1].num_dims == 3;
        assert gdx[-1].dims == ['u','q','c']
        assert len(gdx[-1].dataframe.columns) > 3
        gdx[-1].dataframe[gdxpds.gdx.GamsValueType.Level.name] = 1.0
        gdx[-1].dataframe[gdxpds.gdx.GamsValueType.Upper.name] = 10.0
        #     full dataframe
        gdx.append(gdxpds.gdx.GdxSymbol('sym_14',gdxpds.gdx.GamsDataType.Parameter,
            dims=['u','q','c']))
        gdx[-1].dataframe = pds.DataFrame([['u0','BES','c2',2.0],
                                           ['u0','BES','c1',1.0],
                                           ['u1','BES','c2',2.0]],
                                          columns=['u','q','c','storage_duration_h'])
        assert list(gdx[-1].dataframe.columns) == ['u','q','c','Value']
        #     list of lists containing dims only
        gdx.append(gdxpds.gdx.GdxSymbol('sym_15',gdxpds.gdx.GamsDataType.Equation,
            dims=['u','q','c','t'],equation_type=gdxpds.gdx.GamsEquationType.LessThan))
        gdx[-1].dataframe = [['u0','PHES','c0','1'],
                             ['u0','PHES','c0','2'],
                             ['u0','PHES','c0','3'],
                             ['u0','PHES','c0','4'],
                             ['u0','PHES','c0','5']]
        gdx[-1].dataframe['Level'] = -15.0
        assert list(gdx[-1].dataframe.columns[:gdx[-1].num_dims]) == ['u','q','c','t']
        #     full list of lists
        gdx.append(gdxpds.gdx.GdxSymbol('sym_16',gdxpds.gdx.GamsDataType.Set,
            dims=['q','c']))
        gdx[-1].dataframe = [['PV','c0',True],
                             ['CSP','c0',False],
                             ['CSP','c1',False],
                             ['Wind','c0',True]]
        assert gdx[-1].num_dims == 2
        #     reset with empty list
        gdx.append(gdxpds.gdx.GdxSymbol('sym_17',gdxpds.gdx.GamsDataType.Set,
            dims=['q','c']))
        gdx[-1].dataframe = gdx['sym_11'].dataframe.copy()
        gdx[-1].dataframe = []
        assert gdx[-1].num_dims == 2
        assert list(gdx[-1].dataframe.columns[:gdx[-1].num_dims]) == ['*'] * 2
        assert gdx[-1].num_records == 0

        # And then document that some ways DO NOT WORK:
        # dims=0
        #     set value, then try to set different number of dimensions
        gdx.append(gdxpds.gdx.GdxSymbol('sym_18',gdxpds.gdx.GamsDataType.Parameter,
            dims=0))
        gdx[-1].dataframe = [[3]]
        with pytest.raises(Exception) as e_info:
            gdx[-1].dims = 3
        # dims > 0
        #     explicitly set dims to something else
        gdx.append(gdxpds.gdx.GdxSymbol('sym_19',gdxpds.gdx.GamsDataType.Parameter,
                   dims=['g','t']))
        with pytest.raises(Exception) as e_info:
            gdx[-1].dims = ['g','t','d']
        #     dataframe of different number of dims
        gdx.append(gdxpds.gdx.GdxSymbol('sym_20',gdxpds.gdx.GamsDataType.Variable,
            dims=['d','t']))
        gdx[-1].dataframe = [['d1','1'],
                             ['d1','2'],
                             ['d1','3']]
        tmp = gdx[-1].dataframe.copy()
        cols = list(tmp.columns)
        tmp['q'] = 'PV'
        tmp = tmp[['q'] + cols]
        with pytest.raises(Exception) as e_info:
            gdx[-1].dataframe = tmp
        #     full dataframe of different number of dims
        gdx.append(gdxpds.gdx.GdxSymbol('sym_21',gdxpds.gdx.GamsDataType.Parameter,
            dims=6))
        assert gdx[-1].dims == ['*'] * 6
        with pytest.raises(Exception) as e_info:
            gdx[-1].dataframe = pds.DataFrame([['1',6.0],
                                              ['2',7.0],
                                              ['3',-12.0]])
        #     list of lists of varying widths
        gdx.append(gdxpds.gdx.GdxSymbol('sym_22',gdxpds.gdx.GamsDataType.Parameter,
            dims=3))
        with pytest.raises(Exception) as e_info:
            gdx[-1].dataframe = [[1]]
        with pytest.raises(Exception) as e_info:
            gdx[-1].dataframe = [['1',2.5],
                                 ['2',-30.0]]
        # TODO: Write test where parameter value ends up as set dimension--does
        # an exception get thrown upon writing to GDX?
        with pytest.raises(Exception) as e_info:
            gdx[-1].dataframe = [['u1','PV','c0','1',2.5],
                                 ['u1','PV','c0','2',-30.0]]

        gdx.write(os.path.join(outdir,'dataframe_set_tests.gdx'))
    with gdxpds.gdx.GdxFile(lazy_load=False) as gdx:
        gdx.read(os.path.join(outdir,'dataframe_set_tests.gdx'))
        assert gdx['sym_1'].num_records == 1
        assert gdx['sym_2'].num_records == 1
        assert gdx['sym_3'].num_records == 1
        assert gdx['sym_4'].num_records == 1 # GAMS defaults empty 0-dim parameter to 0
        assert gdx['sym_4'].dataframe['Value'].values[0] == 0.0
        assert gdx['sym_5'].dims == ['u','q']
        assert gdx['sym_5'].num_records == 3
        assert gdx['sym_5'].dataframe['Value'].values[1] == 7500.2
        assert gdx['sym_6'].num_records == 4
        assert gdx['sym_7'].num_records == 0
        assert gdx['sym_8'].dims == ['*'] * 3
        assert gdx['sym_8'].dataframe[gdxpds.gdx.GamsValueType.Upper.name].values[0] == 10.0
        assert gdx['sym_9'].num_records == 3
        assert gdx['sym_10'].num_dims == 4
        assert gdx['sym_11'].num_dims == 2
        assert gdx['sym_11'].num_records == 4 
        # ETH@20181007 - Tried to test for some values being c_bool(False) in sym_11, but
        # c_bool(True) != c_bool(True), so that makes it hard to test such things.
        # Also, c_bool(False) appears to be interpreted as True in GDX. Ick and yikes.
        assert gdx['sym_12'].num_dims == 2
        assert gdx['sym_12'].num_records == 0
        assert gdx['sym_13'].dims == ['u','q','c']
        assert gdx['sym_13'].dataframe[gdxpds.gdx.GamsValueType.Upper.name].values[0] == 10.0
        assert gdx['sym_14'].num_records == 3
        assert gdx['sym_15'].num_dims == 4
        assert gdx['sym_16'].num_dims == 2
        assert gdx['sym_16'].num_records == 4 
        assert gdx['sym_17'].num_dims == 2
        assert gdx['sym_17'].num_records == 0
