import os

import gdxpds.gdx
from gdxpds.test import base_dir

def test_read():
    filename = 'all_generator_properties_input.gdx'
    gdx_file = os.path.join(base_dir,filename)
    with gdxpds.gdx.GdxFile() as f:
        f.read(gdx_file)
        for symbol in f:
            symbol.load()
