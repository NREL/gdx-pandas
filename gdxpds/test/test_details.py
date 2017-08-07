import os
import subprocess as subp

import pandas as pds

import gdxpds.gdx
from gdxpds.test import base_dir, run_dir
from gdxpds.test.test_session import manage_rundir
from gdxpds.test.test_conversions import roundtrip_one_gdx

def value_column_index(sym,gams_value_type):
    for i, val in enumerate(sym.value_cols):
        if val[1] == gams_value_type.value:
            break
    return len(sym.dims) + i

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
            assert val in gdx.special_values
            data[-1].append(val)
            sym = gdx['CapacityValue']
            assert sym.data_type == gdxpds.gdx.GamsDataType.Variable
            val = sym.dataframe.iloc[0,value_column_index(sym,gdxpds.gdx.GamsValueType.Upper)]
            assert val in gdx.special_values
            data[-1].append(val)
    data = list(zip(*data))
    for pt in data:
        for i in range(1,len(pt)):
            assert pt[i] == pt[0]

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
