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

import gdxcc
import numpy as np
import pandas as pds

import gdxpds.gdx
from gdxpds.test import base_dir, run_dir
from gdxpds.test.test_session import manage_rundir
from gdxpds.test.test_conversions import roundtrip_one_gdx

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
        df = pds.DataFrame([['sv' + str(i+1), f.special_values[i]] for i in range(gdxcc.GMS_SVIDX_MAX-2)],
                           columns=['sv','Value'])
        logger.info("Special values are:\n{}".format(df))

        # save this directly as a GdxSymbol
        filename = os.path.join(outdir,'direct_write_special_values.gdx')
        ret = gdxcc.gdxOpenWrite(f.H,filename,"gdxpds")
        if not ret:
            raise gdxpds.gdx.GdxError(f.H,"Could not open {} for writing. Consider cloning this file (.clone()) before trying to write".format(repr(filename)))
        # set special values
        ret = gdxcc.gdxSetSpecialValues(f.H,f.special_values)
        if ret == 0:
            raise gdxpds.gdx.GdxError(f.H,"Unable to set special values")
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
            assert gdxpds.gdx.gdx_val_equal(gdx_file.np_to_gdx_svs[i],gdx_file.special_values[i],gdx_file)

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
            assert gdxpds.gdx.is_np_sv(val)
            data[-1].append(val)
            sym = gdx['CapacityValue']
            assert sym.data_type == gdxpds.gdx.GamsDataType.Variable
            val = sym.dataframe.iloc[0,value_column_index(sym,gdxpds.gdx.GamsValueType.Upper)]
            assert gdxpds.gdx.is_np_sv(val)
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
        assert gdx[-1].dataframe[gdx[-1].dataframe.columns[-1]].dtype == bool
        gdx.append(gdxpds.gdx.GdxSymbol('my_other_set',gdxpds.gdx.GamsDataType.Set,dims=['u']))
        data = pds.DataFrame([['u' + str(i)] for i in range(1,11)],columns=['u'])
        data['Value'] = True
        gdx[-1].dataframe = gdx[-1].dataframe.append(data)
        assert gdx[-1].dataframe[gdx[-1].dataframe.columns[-1]].dtype == bool        
        gdx.write(os.path.join(outdir,'my_sets.gdx'))
    with gdxpds.gdx.GdxFile(lazy_load=False) as gdx:
        gdx.read(os.path.join(outdir,'my_sets.gdx'))
        for sym in gdx:
            assert sym.num_dims == 1
            assert sym.dims[0] == 'u'
            assert sym.data_type == gdxpds.gdx.GamsDataType.Set
            assert sym.num_records == 10
            assert sym.dataframe[sym.dataframe.columns[-1]].dtype == bool
