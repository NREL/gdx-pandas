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


import pandas as pds

import gdxpds.test
import gdxpds.tools

import os
import shutil
import subprocess as subp

def base_dir():
    return os.path.dirname(__file__)

def run_dir():
    return os.path.join(base_dir(), 'output')
    
def setup_module():
    if os.path.exists(run_dir()):
        shutil.rmtree(run_dir())
    os.mkdir(run_dir())
    
def teardown_module():
    if gdxpds.test.clean_up:
        shutil.rmtree(run_dir())
        
def test_gdx_roundtrip():
    # load gdx, make map of symbols and number of records
    gdx_file = os.path.join(base_dir(),'CONVqn.gdx')
    loader = gdxpds.tools.GdxLoader(gdx_file)
    num_records = {}
    total_records = 0
    for symbol_name in loader.gdx:
        num_records[symbol_name] = loader.gdx.getinfo(symbol_name)['records']
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
    for symbol_name, records in num_records.items():
        if records > 0:
            assert symbol_name in loader.gdx
            assert loader.gdx.getinfo(symbol_name)['records'] == records
    
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
    os.mkdir(out_dir)
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
    for csv_name, records in num_records.items():
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
    