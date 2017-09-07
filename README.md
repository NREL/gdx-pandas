gdx-pandas
==========

Python package to translate between gdx (GAMS data) and pandas. 

[Install](#install) | [Use](#use) | [Uninstall](#uninstall)

## Use

There are two main ways to use gdxpds. The first use case is the one that was 
initially supported: direct conversion between GDX files on disk and pandas 
DataFrames or a csv version thereof. The Version 1.0.0 rewrite intoduces a 
second style of use, that is, interfacing with GDX files and symbols via the 
`gdxpds.gdx.GdxFile` and `gdxpds.gdx.GdxSymbol` classes.

[Direct Conversion](#direct-conversion) | [Backend Classes](#backend-classes)

### Direct Conversion

The two primary points of reference for the direct conversion utilities are GDX 
files on disk and python dicts of {symbol_name: pandas.DataFrame}, where 
each pandas.DataFrame contains data for a single set, parameter, equation, or 
variable. For sets and parameters, the last column of the DataFrame is assumed to
contain the value of the element, which for sets should be `True`, and for 
parameters should be a `float` (or one of the `gdxpds.gdx.NUMPY_SPECIAL_VALUES`). 
Equations and variables have additional 'value' columns, in particular a level, 
a marginal value, a lower bound, an upper bound, and a scale, as enumerated in 
`gdxpds.gdx.GamsValueType`. These values are all assumed to be found in the last 
five columns of the DataFrame, also see `gdxpds.gdx.GAMS_VALUE_COLS_MAP`.

The basic interface to convert from GDX to DataFrames is:

```python
import gdxpds

gdx_file = 'C:\path_to_my_gdx\data.gdx'
dataframes = gdxpds.to_dataframes(gdx_file)
for symbol_name, df in dataframes.items():
    print("Doing work with {}.".format(symbol_name))
```

And vice-versa:

```python
import gdxpds

# assume we have a DataFrame df with last column 'value'
data_ready_for_GAMS = { 'symbol_name': df }

gdx_file = 'C:\path_to_my_output_gdx\data_to_send_to_gams.gdx'
gdx = gdxpds.to_gdx(data_ready_for_GAMS, gdx_file)
```

Note that providing a gdx_file is optional, and the returned gdx is an object of 
type `gdxpds.gdx.GdxFile`.

Additional functions include:

- `gdxpds.list_symbols`
- `gdxpds.to_dataframe` (If the call to this method includes 
   old_interface=False, then the return value will be a plain DataFrame, not a 
   {'symbol_name': df} dict.)

The package also includes command line utilities for converting between GDX and 
CSV, see

```bash
python C:\your_python_path\Scripts\gdx_to_csv.py --help
python C:\your_python_path\Scripts\csv_to_gdx.py --help
```

### Backend Classes

The basic functionalities described above can also be achieved with direct use
of the backend classes now available in `gdxpds.gdx`. To duplicate the GDX read 
functionality shown above one would write:

```python
import gdxpds

gdx_file = 'C:\path_to_my_gdx\data.gdx'
with gdxpds.gdx.GdxFile(lazy_load=False) as f:
    f.read(gdx_file)
    for symbol in f:
        symbol_name = symbol.name
        df = symbol.dataframe
        print("Doing work with {}:\n{}".format(symbol_name,df.head()))
```

The backend especially gives more control over creating new data in GDX format. 
For example:

```python
import gdxpds

out_file = 'my_new_gdx_data.gdx'
with gdxpds.gdx.GdxFile() as gdx:
    # Create a new set with one dimension
    gdx.append(gdxpds.gdx.GdxSymbol('my_set',gdxpds.gdx.GamsDataType.Set,dims=['u']))
    data = pds.DataFrame([['u' + str(i)] for i in range(1,11)])
    data['Value'] = True
    gdx[-1].dataframe = data
    # Create a new parameter with one dimension
    gdx.append(gdxpds.gdx.GdxSymbol('my_parameter',gdxpds.gdx.GamsDataType.Parameter,dims=['u']))
    data = pds.DataFrame([['u' + str(i), i*100] for i in range(1,11)],
                         columns=(gdx[-1].dims + gdx[-1].value_col_names))
    gdx[-1].dataframe = data
```

## Install

### Preliminaries

- Python 2.6 or higher 2.X; Python 3.4 or higher 3.X
- pandas (In general you will want the SciPy stack. Anaconda comes with it, or see [my notes for Windows](http://elainethale.wordpress.com/programming-notes/python-environment-set-up/).)
- For Python versions < 3.4, enum34. Also **uninstall the enum package** if it is installed.
- psutil (optional--for monitoring memory use)
- pytest (optional--for running tests)
- GAMS Python bindings
    - See GAMS/win64/XX.X/apifiles/readme.txt on Windows, 
      GAMS/gamsXX.X_osx_x64_64_sfx/apifiles/readme.txt on Mac, or 
      /opt/gams/gamsXX.X_linux_x64_64_sfx/apifiles/readme.txt on Linux
    - Run the following for the correct version of the Python bindings
        
        ```bash
        python setup.py install
        ```

        or 

        ```bash
        python setup.py build --build-base=/path/to/somwhere/you/have/write/access install
        ```

        with the latter being for the case when you can install packages into 
        Python but don't have GAMS directory write access.

    - .../apifiles/Python/api/setup.py works for Python 2.7
    - For other versions of Python, especially 3.X, use 
      .../apifiles/Python/api_XX/setup.py. For Python 3.X in particular you will 
      need GAMS version >= 24.5.1 (Python 3.4, Windows and Linux), 
      24.7.4 (Python 3.4, Mac OS X), or >= 24.8.4 (Python 3.6)

### Get the Latest Package

```bash
pip install git+https://github.com/NREL/gdx-pandas.git@master
```

or 

```bash
pip install git+https://github.com/NREL/gdx-pandas.git@v1.0.0
```

Versions are listed at https://github.com/NREL/gdx-pandas/releases.

After installation, you can test the package using pytest:

```bash
pytest gdxpds
```

## Uninstall

```
pip uninstall gdxpds
```
