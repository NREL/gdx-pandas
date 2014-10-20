
from nose.tools import nottest
import subprocess as subp

import gdxpds.test
import gdxpds.tools

import os
import shutil

def base_dir():
    return os.path.dirname(__file__)

def run_dir():
    return os.path.join(base_dir(), 'output')
    
def setup_module():
    if os.path.exists(run_dir()):
        shutil.rmtree(run_dir())
    os.mkdir(run_dir())
    
def tesrdown_module():
    if gdxpds.test.clean_up:
        shutil.rmtree(run_dir())
        
def test_gdx_roundtrip():
    # load gdx, make map of symbols and number of records
    gdx_file = os.path.join(base_dir(),'CONVqn.gdx')
    loader = gdxpds.tools.GdxLoader(gdx_file)
    num_records = {}
    total_records = 0
    for symbol_name in loader.gdx:
        num_records[symbol_name] = loader.gdx.get_info(symbol_name)['records']
        total_records += num_records[symbol_name]
    assert total_records > 0
    
    # call command-line interface to transform gdx to csv
    out_dir = os.path.join(run_dir(), 'gdx_roundtrip')
    cmds = ['python', os.path.join(gdxpds.test.bin_prefix,'gdx_to_csv.py'),
            '-i', gdx_file,
            '-o', out_dir]
    subp.call(cmds)            
    
    # call command-line interface to transform csv to gdx
    txt_file = os.path.join(out_dir, 'csvs.txt')
    f = open(txt_file, 'w')
    for p, dirs, files in os.walk(out_dir):
        for file in files:
            if os.path.splitext(file)[1] == '.csv':
                f.write("{}\n".format(os.path.join(p,file)))
        break
    f.close()
    roundtripped_gdx = os.path.join(out_dir, 'output.gdx')
    cmds = ['python', os.path.join(gdxpds.test.bin_prefix,'csv_to_gdx.py'),
            '-i', txt_file,
            '-o', roundtripped_gdx]
    subp.call(cmds)
    
    # load gdx and check symbols and records against original map
    loader = gdxpds.tools.GdxLoader(roundtripped_gdx)
    for symbol_name, records in num_records:
        if records > 0:
            assert symbol_name in loader.gdx
            assert loader.gdx.get_info(symbol_name)['records'] == records
    
def test_csv_roundtrip():
    # load csvs into pandas and make map of filenames to number of rows
    csvs = [os.path.join(base_dir(), 'installed_capacity.csv'),
            os.path.join(base_dir(), 'annual_generation.csv')]
    n = len(csvs)
    num_records = {}
    total_records = 0
    for csv in csvs:
        df = pds.DataFrame.from_csv(csv, index_col = None)
        num_records[os.path.splitext(os.path.basename(csv))[0]] = len(df.index)
        total_records += len(df.index)
    assert total_records > 0
    
    # call command-line interface to transform csv to gdx
    out_dir = os.path.join(run_dir(), 'csv_roundtrip')
    gdx_file = os.path.join(out_dir, 'intermediate.gdx')
    cmds = ['python', os.path.join(gdxpds.test.bin_prefix,'csv_to_gdx.py'),
            '-i', csvs[0], csvs[1],
            '-o', gdx_file]
    subp.call(cmds)
    
    # call command-line interface to transform gdx to csv
    cmds = ['python', os.path.join(gdxpds.test.bin_prefix,'gdx_to_csv.py'),
            '-i', gdx_file,
            '-o', out_dir]
    subp.call(cmds)
    
    # load csvs into pandas and check filenames and number of rows against original map
    for csv_name, records in num_records:
        csv_file = os.path.join(out_dir, csv_name + '.csv')
        assert os.path.isfile(csv_file)
        df = pds.DataFrame.from_csv(csv_file, index_col = None)
        assert len(df.index) == records

    cnt = 0
    for p, dirs, files in os.walk(out_dir):
        for file in files:
            if os.path.splitext(file)[1] == '.csv':
                cnt += 1
        break
    assert cnt == n
    