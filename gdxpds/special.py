
import copy
import logging

import gdxcc
import numpy as np


# List of numpy special values in gdxGetSpecialValues order
#                      1E300,  2E300,  3E300,   4E300,               5E300
NUMPY_SPECIAL_VALUES = [None, np.nan, np.inf, -np.inf, np.finfo(float).eps]

logger = logging.getLogger(__name__)


def convert_gdx_to_np_svs(df, num_dims, gdxf):
    """
    Converts GDX special values to the corresponding numpy versions.

    Parmeters
    ---------
    df : pandas.DataFrame
        a GdxSymbol DataFrame as it was read directly from GDX
    num_dims : int
        the number of columns in df that list the dimension values for which the
        symbol value is non-zero / non-default
    gdxf : GdxFile
        the GdxFile containing the symbol. Used to provide the gdx_to_np_svs map.

    Returns
    -------
    pandas.DataFrame
        copy of df for which all GDX special values have been converted to
        their numpy equivalents
    """

    # single-value mapping function
    def to_np_svs(value):
        if value in gdxf.gdx_to_np_svs:
            return gdxf.gdx_to_np_svs[value]
        return value

    # create clean copy of df
    try:
        tmp = copy.deepcopy(df)
    except:
        logger.warning("Unable to deepcopy:\n{}".format(df))
        tmp = copy.copy(df)

    # apply the map to the value columns and merge with the dimensional information
    tmp = (tmp.iloc[:, :num_dims]).merge(tmp.iloc[:, num_dims:].applymap(to_np_svs),
                                         left_index=True, right_index=True)
    return tmp


def is_np_eps(val):
    """
    Parameters
    ----------
    val : numeric
        value to test

    Returns
    -------
    bool
        True if val is equal to eps (np.finfo(float).eps), False otherwise
    """
    return np.abs(val - NUMPY_SPECIAL_VALUES[-1]) < NUMPY_SPECIAL_VALUES[-1]


def is_np_sv(val):
    """
    Parameters
    ----------
    val : numeric
        value to test

    Returns
    -------
    bool
        True if val is NaN, eps, or is in NUMPY_SPECIAL_VALUES; False otherwise
    """
    return np.isnan(val) or (val in NUMPY_SPECIAL_VALUES) or is_np_eps(val)


def convert_np_to_gdx_svs(df, num_dims, gdxf):
    """
    Converts numpy special values to the corresponding GDX versions.

    Parmeters
    ---------
    df : pandas.DataFrame
        a GdxSymbol DataFrame in pandas/numpy form
    num_dims : int
        the number of columns in df that list the dimension values for which the
        symbol value is non-zero / non-default
    gdxf : GdxFile
        the GdxFile containing the symbol. Used to provide the np_to_gdx_svs map.

    Returns
    -------
    pandas.DataFrame
        copy of df for which all numpy special values have been converted to
        their GDX equivalents
    """

    # converts a single value; NANs are assumed already handled
    def to_gdx_svs(value):
        # find numpy special values by direct comparison
        for i, npsv in enumerate(NUMPY_SPECIAL_VALUES):
            if value == npsv:
                return gdxf.np_to_gdx_svs[i]
        # eps values are not always caught by ==, use is_np_eps which applies
        # a tolerance
        if is_np_eps(value):
            return gdxf.np_to_gdx_svs[4]
        return value

    # get a clean copy of df
    try:
        tmp = copy.deepcopy(df)
    except:
        logger.warning("Unable to deepcopy:\n{}".format(df))
        tmp = copy.copy(df)

    # fillna and apply map to value columns, then merge with dimensional columns
    try:
        values = tmp.iloc[:, num_dims:].fillna(gdxf.np_to_gdx_svs[1]).applymap(to_gdx_svs)
        tmp = (tmp.iloc[:, :num_dims]).merge(values, left_index=True, right_index=True)
    except:
        logger.error("Unable to convert numpy special values to GDX special values." + \
                     "num_dims: {}, dataframe:\n{}".format(num_dims, df))
        raise
    return tmp


def gdx_isnan(val, gdxf):
    """
    Utility function for equating the GDX special values that map to None or NaN
    (which are indistinguishable in pandas).

    Parameters
    ----------
    val : numeric
        value to test
    gdxf : GdxFile
        GDX file containing the value. Provides np_to_gdx_svs map.

    Returns
    -------
    bool
        True if val is a GDX encoded special value that maps to None or numpy.nan;
        False otherwise
    """
    return val in [gdxf.np_to_gdx_svs[0], gdxf.np_to_gdx_svs[1]]


def gdx_val_equal(val1, val2, gdxf):
    """
    Utility function used to test special value conversions.

    Parameters
    ----------
    val1 : float or GDX special value
        first value to compare
    val2 : float or GDX special value
        second value to compare
    gdxf : GdxFile
        GDX file containing val1 and val2

    Returns
    -------
    bool
        True if val1 and val2 are equal in the sense of == or they are
        equivalent GDX-format special values. The values that map to None
        and np.nan are assumed to be equal because pandas cannot be relied
        upon to make the distinction.
    """
    if gdx_isnan(val1, gdxf) and gdx_isnan(val2, gdxf):
        return True
    return val1 == val2


def special_getter():
    H = gdxcc.new_gdxHandle_tp()
    rc = gdxcc.gdxCreateD(H, None, gdxcc.GMS_SSSIZE)
    if not rc:
        raise Exception(rc[1])
    # get special values
    special_values = gdxcc.doubleArray(gdxcc.GMS_SVIDX_MAX)
    gdxcc.gdxGetSpecialValues(H, special_values)

    gdx_to_np_svs = {}
    np_to_gdx_svs = {}
    for i in range(gdxcc.GMS_SVIDX_MAX):
        if i >= len(NUMPY_SPECIAL_VALUES):
            break
        gdx_val = special_values[i]
        gdx_to_np_svs[gdx_val] = NUMPY_SPECIAL_VALUES[i]
        np_to_gdx_svs[i] = gdx_val

    gdxcc.gdxFree(H)
    return gdx_to_np_svs, np_to_gdx_svs


GDX_TO_NP_SVS, NP_TO_GDX_SVS = special_getter()
