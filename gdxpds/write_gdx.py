

def to_gdx(dfs, path = None, gams_dir = None):
    """
    Parameters:
      - dfs (map of pandas.DataFrame): symbol name to pandas.DataFrame 
        dict to be compiled into a single gdx file
      - path (optional string): if provided, the gdx file will be written
        to this path
        
    Returns a gdxdict.gdxdict, which is defined in [py-gdx](https://github.com/geoffleyland/py-gdx).
    """
      