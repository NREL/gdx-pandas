# gdx-pandas
[![PyPI](https://img.shields.io/pypi/v/gdxpds.svg)](https://pypi.python.org/pypi/gdxpds/)
[![Documentation](https://img.shields.io/badge/docs-ready-blue.svg)](https://nrel.github.io/gdx-pandas)

gdx-pandas is a python package to translate between gdx (GAMS data) and pandas. 

[Install](#install) | [Documentation](https://nrel.github.io/gdx-pandas) | [Uninstall](#uninstall)

## Install

### Preliminaries

- Python 3.4 or 3.6 (gdx-pandas support for Python 2.X has been discontinued; GAMS does not yet support Python 3.7)
- pandas (In general you will want the SciPy stack. Anaconda comes with it, or see [my notes for Windows](https://elainethale.wordpress.com/programming-notes/python-environment-set-up/).)
- For Python versions < 3.4, enum34. Also **uninstall the enum package** if it is installed.
- Install [GAMS](https://www.gams.com/download/)
- Put the GAMS directory in your `PATH` and/or assign it to the `GAMS_DIR` environment variable
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

    - For Python 3.X, use 
      .../apifiles/Python/api_XX/setup.py. For Python 3.X in particular you will 
      need GAMS version >= 24.5.1 (Python 3.4, Windows and Linux), 
      24.7.4 (Python 3.4, Mac OS X), or >= 24.8.4 (Python 3.6)

### Get the Latest Package

```bash
pip install gdxpds
```

or

```bash
pip install git+https://github.com/NREL/gdx-pandas.git@v1.2.0
```

or

```bash
pip install git+https://github.com/NREL/gdx-pandas.git@master
```


Versions are listed at [pypi](https://pypi.python.org/pypi/gdxpds/) and 
https://github.com/NREL/gdx-pandas/releases.

After installation, you can test the package using pytest:

```bash
pytest --pyargs gdxpds
```

If the tests fail due to permission IOErrors, apply `chmod g+x` and `chmod a+x` 
to the `gdx-pandas/gdxpds/test` folder.

## Uninstall

```
pip uninstall gdxpds
```
