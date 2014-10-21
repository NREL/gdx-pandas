gdx-pandas
==========

Python package to translate between gdx (GAMS data) and pandas.

## Usage

[Install](#install) first.

To work in memory between GDX and pandas DataFrames, note that the two primary points 
of reference are GDX files on disk and python dicts of {symbol_name: pandas.DataFrame}. 
(Alternatively for GDX files, you can directly access the intermediate gdxdict.gdxdict 
objects in memory.)

Then, to convert from GDX to DataFrames:

```python
import gdxpds

gdx_file = 'C:\path_to_my_gdx\data.gdx'
dataframes = gdxpds.to_dataframes(gdx_file)
for symbol_name, df in dataframes.items():
    print("Doing work with {}.".format(symbol_name))
```

And within the loop, df is a pandas.DataFrame with unhelpful column names (#1) except 
for 'value'.

And vice-versa:

```python
import gdxpds

# assume we already have a dataframes object in memory

gdx_file = 'C:\path_to_my_output_gdx\data_to_send_to_gams.gdx'
gdx = gdxpds(dataframes, gdx_file)
```

Note that providing a gdx_file is optional, and the returned gdx is an object of type [gdxdict.gdxdict](https://github.com/geoffleyland/py-gdx/blob/master/gdxdict.py).


The package also includes command line utilities for converting between GDX and CSV, see

```bash
python gdx_to_csv.py --help
python csv_to_gdx.py --help
```

## Install

### Preliminaries

- Python 2.7
- pandas (In general you will want the SciPy stack. Anaconda comes with it, or see [my notes for Windows](http://elainethale.wordpress.com/programming-notes/python-environment-set-up/).)
- nose
- GAMS Python bindings
    - See GAMS/win64/XX.X/apifiles/readme.txt
    - See GAMS/win64/XX.X/apifiles/Python/api/setup.py, in particular, run
        
        ```
        python setup.py install
        ```
        
- geoffleyland/py-gdx

    ```
    pip install git+https://github.com/geoffleyland/py-gdx.git@master
    ```

### Get the Latest Package

```
pip install git+ssh://git@github.nrel.gov/ehale/gdx-pandas.git@master
```

or 

```
pip install git+ssh://git@github.nrel.gov/ehale/gdx-pandas.git@v0.1.0
```

Versions are listed at https://github.nrel.gov/ehale/gdx-pandas/releases.

Unfortunately on Windows, while this command nominally works (after running it, `pip list` will show cpest as installed), it [exits with errors](http://stackoverflow.com/q/23938896/1470262).

## Uninstall

```
pip uninstall gdxpds
```
