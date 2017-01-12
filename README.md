gdx-pandas
==========

Python package to translate between gdx (GAMS data) and pandas. 

[Install](#install) | [Use](#use) | [Uninstall](#uninstall)

## Use

To work in memory between GDX and pandas DataFrames, note that the two primary points 
of reference are GDX files on disk and python dicts of {symbol_name: pandas.DataFrame}, 
where each pandas.DataFrame contains data for a single parameter whose value is in
the last column, and that column is labeled 'value' (case insensitive). Alternatively 
for GDX files, you can directly access the intermediate gdxdict.gdxdict objects in memory.

Then, to convert from GDX to DataFrames:

```python
import gdxpds

gdx_file = 'C:\path_to_my_gdx\data.gdx'
dataframes = gdxpds.to_dataframes(gdx_file)
for symbol_name, df in dataframes.items():
    print("Doing work with {}.".format(symbol_name))
```

And within the loop, df is a pandas.DataFrame with unhelpful column names except 
for 'value'.

And vice-versa:

```python
import gdxpds

# assume we have a DataFrame df with last column 'value'
data_ready_for_GAMS = { 'symbol_name': df }

gdx_file = 'C:\path_to_my_output_gdx\data_to_send_to_gams.gdx'
gdx = gdxpds.to_gdx(data_ready_for_GAMS, gdx_file)
```

Note that providing a gdx_file is optional, and the returned gdx is an object of type gdxpds.gdxdict.gdxdict.

Additional functions include:

- `gdxpds.list_symbols`
- `gdxpds.to_dataframe`

The package also includes command line utilities for converting between GDX and CSV, see

```bash
python C:\your_python_path\Scripts\gdx_to_csv.py --help
python C:\your_python_path\Scripts\csv_to_gdx.py --help
```

(Ideally, after installing gdxpds you should be able to simply call `python gdx_to_csv.py`, but for some reason python does not use either PATH or PYTHONPATH when looking for scripts, see [stackoverflow question](http://stackoverflow.com/q/26497032/1470262).)

## Install

### Preliminaries

- Python 2.7
- pandas (In general you will want the SciPy stack. Anaconda comes with it, or see [my notes for Windows](http://elainethale.wordpress.com/programming-notes/python-environment-set-up/).)
- nose
- GAMS Python bindings
    - See GAMS/win64/XX.X/apifiles/readme.txt
    - See GAMS/win64/XX.X/apifiles/Python/api/setup.py, in particular, run
        
        ```bash
        python setup.py install
        ```

### Get the Latest Package

```bash
pip install git+https://github.com/NREL/gdx-pandas.git@master
```

or 

```bash
pip install git+https://github.com/NREL/gdx-pandas.git@v0.5.2
```

Versions are listed at https://github.com/NREL/gdx-pandas/releases.

Unfortunately on Windows, while this command nominally works (after running it, `pip list` will show gdxpds as installed), it may [exit with errors](http://stackoverflow.com/q/23938896/1470262).

After installation, you can test the package using nose:

```bash
nosetests gdxpds
```

## Uninstall

```
pip uninstall gdxpds
```
