gdx-pandas
==========

Python package to translate between gdx (GAMS data) and pandas.

## Preliminaries

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
