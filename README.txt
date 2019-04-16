gdx-pandas: Python package to translate between gdx (GAMS data) and pandas. 

There are two main ways to use gdxpds. The first use case is the one that was 
initially supported: direct conversion between GDX files on disk and pandas 
DataFrames or a csv version thereof. Starting with the Version 1.0.0 rewrite,
there is now a second style of use which involves interfacing with GDX files and 
symbols via the `gdxpds.gdx.GdxFile` and `gdxpds.gdx.GdxSymbol` classes.

Please visit http://nrel.github.io/gdx-pandas for the latest documentation.


DEPENDENCIES

- Python 3.4 or higher 3.X (support for Python 2.X has been discontinued)
- pandas (In general you will want the SciPy stack. Anaconda comes with it, or see [my notes for Windows](http://elainethale.wordpress.com/programming-notes/python-environment-set-up/).)
- For Python versions < 3.4, enum34. Also **uninstall the enum package** if it is installed.
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


TESTING

After installation, you can test the package using pytest:

pytest --pyargs gdxpds

If the tests fail due to permission IOErrors, apply `chmod g+x` and `chmod a+x` 
to the `gdx-pandas/gdxpds/test` folder.
