import logging
import os

import pytest

import gdxpds.gdx
from gdxpds import to_dataframes
from gdxpds.test import base_dir

logger = logging.getLogger(__name__)

def test_read():
    filename = 'all_generator_properties_input.gdx'
    gdx_file = os.path.join(base_dir,filename)
    with gdxpds.gdx.GdxFile() as f:
        f.read(gdx_file)
        for symbol in f:
            symbol.load()

def test_read_none():
    with pytest.raises(gdxpds.gdx.GdxError) as excinfo:
        to_dataframes(None)
    assert "Could not open None" in str(excinfo.value)

def test_read_path():
    filename = 'all_generator_properties_input.gdx'
    from pathlib import Path
    gdx_file = Path(base_dir) / filename
    to_dataframes(gdx_file)

def test_unload():
    filename = 'all_generator_properties_input.gdx'
    gdx_file = os.path.join(base_dir,filename)
    with gdxpds.gdx.GdxFile() as f:
        f.read(gdx_file)
        assert not f['startupfuel'].loaded
        assert f['startupfuel'].dataframe.empty

        f['startupfuel'].load()
        assert f['startupfuel'].loaded
        assert not f['startupfuel'].dataframe.empty
        assert 'CC' in f['startupfuel'].dataframe['*'].tolist()

        f['startupfuel'].unload()
        assert not f['startupfuel'].loaded
        assert f['startupfuel'].dataframe.empty
        
        f['startupfuel'].load()
        assert f['startupfuel'].loaded
        assert not f['startupfuel'].dataframe.empty
        assert 'CC' in f['startupfuel'].dataframe['*'].tolist()
