from __future__ import absolute_import, print_function

from builtins import super
from collections import defaultdict, OrderedDict
from enum import Enum
import logging
from six import string_types

# try to import gdx loading utility
HAVE_GDX2PY = False
try:
    import gdx2py
    HAVE_GDX2PY = True
except ImportError: pass

import gdxcc

from gdxpds.tools import Error, NeedsGamsDir

logger = logging.getLogger(__name__)


class GdxError(Error):
    def __init__(self, H, msg):
        """
        Pulls information from gdxcc about the last encountered error and appends
        it to msg.

        Positional Arguments:
            - H (pointer or None) - SWIG binding pointer to a GDX object
            - msg (str) - gdxpds error message
        """
        self.msg = msg + "."
        if H:
            self.msg += " " + gdxcc.gdxErrorStr(H, gdxcc.gdxGetLastError(H))[1] + "."
        super().__init__(self.msg)


class GdxFile(NeedsGamsDir):

    def __init__(self,gams_dir=None,lazy_load=True):
        """
        Initializes a GdxFile object by connecting to GAMS and creating a pointer.

        Throws a GdxError if either of those operations fail.
        """
        self.lazy_load = lazy_load
        self._version = None
        self._producer = None
        self._filename = None
        self.universal_set = None
        self.symbols = OrderedDict()

        super().__init__(gams_dir=gams_dir)
        self._H = self._create_gdx_object()

    @property
    def empty(self):
        """
        Returns True if this GdxFile object contains any data.
        """
        return (self.num_symbols == 0)

    @property
    def H(self):
        """
        GDX object handle
        """
        return self._H

    @property
    def filename(self):
        return self._filename

    @property
    def version(self):
        """
        GDX file version
        """
        return self._version

    @property
    def producer(self):
        """
        Also a GDX file version string
        """
        return self._producer

    @property
    def num_symbols(self):
        return len(self.symbols)

    @property
    def num_elements(self):
        return sum([symbol.num_records for symbol_name, symbol in self.symbols.items()])

    @property
    def dataframes(self):
        return OrderedDict([(symbol_name, symbol.dataframe) for symbol_name, symbol in self.symbols.items()])

    def read(self,filename):
        """
        Opens gdx file at filename and reads meta-data. If not self.lazy_load, 
        also loads all symbols.

        Throws an Error if not self.empty.

        Throws a GdxError if any calls to gdxcc fail.
        """
        if not self.empty:
            raise Error("GdxFile.read can only be used if the GdxFile is .empty")

        # open the file
        rc = gdxcc.gdxOpenRead(self.H,filename)
        if not rc[0]:
            raise GdxError(self.H,"Could not open '{}'".format(filename))
        self._filename = filename

        # read in meta-data ...
        # ... for the file
        ret, self._version, self._producer = gdxcc.gdxFileVersion(self.H)
        if ret != 1: 
            raise GDXError(self.H,"Could not get file version")
        ret, symbol_count, element_count = gdxcc.gdxSystemInfo(self.H)
        logger.info("Opening '{}' with {} symbols and {} elements with lazy_load = {}.".format(filename,symbol_count,element_count,self.lazy_load))
        # ... for the symbols
        ret, name, dims, data_type = gdxcc.gdxSymbolInfo(self.H,0)
        if ret != 1:
            raise GdxError(self.H,"Could not get symbol info for the universal set")
        self.universal_set = GdxSymbol(name,data_type,dims=dims,file=self,index=0)
        for i in range(symbol_count):
            index = i + 1
            ret, name, dims, data_type = gdxcc.gdxSymbolInfo(self.H,index)
            if ret != 1:
                raise GdxError(self.H,"Could not get symbol info for symbol {}".format(index))
            self.symbols[name] = GdxSymbol(name,data_type,dims=dims,file=self,index=index)

        # read all symbols if not lazy_load
        if not self.lazy_load:
            for symbol_name, symbol in self.symbols.items():
                symbol.load()

    def __str__(self):
        s = "GdxFile containing {} symbols and {} elements.".format(self.num_symbols,self.num_elements)
        sep =  " Symbols:\n  "
        for symbol_name, symbol in self.symbols.items():
            s += sep + str(symbol)
            sep = "\n  "
        return s

    def _create_gdx_object(self):
        H = gdxcc.new_gdxHandle_tp()
        rc = gdxcc.gdxCreateD(H,self.gams_dir,gdxcc.GMS_SSSIZE)
        if not rc[0]:
            raise GdxError(H,rc[1])
        return H


class GamsDataType(Enum):
    Set = gdxcc.GMS_DT_SET
    Parameter = gdxcc.GMS_DT_PAR
    Variable = gdxcc.GMS_DT_VAR
    Equation = gdxcc.GMS_DT_EQU
    Alias = gdxcc.GMS_DT_ALIAS


GAMS_VALUE_COLS_MAP = defaultdict(lambda : ['Value'])


class GamsVariableType(Enum):
    Unknown = gdxcc.GMS_VARTYPE_UNKNOWN
    Binary = gdxcc.GMS_VARTYPE_BINARY
    Integer = gdxcc.GMS_VARTYPE_INTEGER
    Positive = gdxcc.GMS_VARTYPE_POSITIVE
    Negative = gdxcc.GMS_VARTYPE_NEGATIVE
    Free = gdxcc.GMS_VARTYPE_FREE
    SOS1 = gdxcc.GMS_VARTYPE_SOS1
    SOS2 = gdxcc.GMS_VARTYPE_SOS2
    Semicont = gdxcc.GMS_VARTYPE_SEMICONT
    Semiint = gdxcc.GMS_VARTYPE_SEMIINT


class GdxSymbol(object): 
    def __init__(self,name,data_type,dims=0,file=None,index=None): 
        self.name = name
        self.data_type = GamsDataType(data_type)
        self._dataframe = None
        self.dims = dims       
        self._file = file
        self._index = index        

        if self.file:
            # loading
            self._loaded = False
            # get additional meta-data
            ret, records, userinfo, description = gdxcc.gdxSymbolInfoX(self.file.H,self.index)
            if ret != 1:
                raise GdxError(self.file.H,"Unable to get extended symbol information for {}".format(self.name))
            self._num_records = records
            if self.data_type == GamsDataType.Variable:
                self.variable_type = GamsVariableType(userinfo)
            self.description = description
            if self.index > 0:
                ret, gdx_domain = gdxcc.gdxSymbolGetDomainX(self.file.H,self.index)
                if ret == 0:
                    raise GdxError(self.file.H,"Unable to get domain information for {}".format(self.name))
                assert len(gdx_domain) == len(self.dims), "Dimensional information read in from GDX should be consistent."
                self.dims = gdx_domain
        else:
            # writing
            self._loaded = True
            if self.data_type == GamsDataType.Variable:
                self.variable_type = GamsVariableType("Free")
            self._num_records = 0

    @property
    def file(self):
        return self._file

    @property
    def index(self):
        return self._index

    @property
    def loaded(self):
        return self._loaded

    @property
    def full_typename(self):
        if self.data_type == GamsDataType.Parameter and self.dims == 0:
            return 'Scalar'
        elif self.data_type == GamsDataType.Variable:
            return self.variable_type + " " + self.data_type.name
        return self.data_type.name

    @property
    def dims(self):
        return self._dims

    @dims.setter
    def dims(self, value):
        if self.dataframe is not None:
            if not isinstance(value,list) or len(value) != self.num_dims:
                logger.warn("Cannot set dims to {}, because dataframe is already set with dims {}.".format(value,self.dims))
        if isinstance(value,int):
            self._dims = ['*'] * value
            return
        if not isinstance(value, list):
            raise Error('dims must be an int or a list. Was passed {} of type {}.'.format(value, type(value)))
        for dim in value:
            if not isinstance(dim,string_types):
                raise Error('Individual dimensions must be denoted by strings. Was passed {} as element of {}.'.format(dim, value))
        self._dims = value

    @property
    def num_dims(self):
        return len(self.dims)        

    @property
    def value_cols(self):
        return GAMS_VALUE_COLS_MAP[self.data_type]

    @property
    def dataframe(self):
        return self._dataframe

    @dataframe.setter
    def dataframe(self, data):
        if isinstance(data, pds.DataFrame):
            # Fix up dimensions
            num_dims = len(data.columns) - len(self.value_cols)
            dim_cols = data.columns[:num_dims]
            replace_dims = True
            for col in dim_cols:
                if not isinstance(col,string_types):
                    replace_dims = False
                    break
            if replace_dims:
                self.dims = dim_cols
            if num_dims != self.num_dims:
                self.dims = num_dims
            self._dataframe = copy.deepcopy(data)
            self._dataframe.columns = self.dims + self.value_cols
        else:
            self._dataframe = pds.DataFrame(data,columns=self.dims + self.value_cols)
        self._num_records = len(self._dataframe.index)
        return

    @property
    def num_records(self):
        return self._num_records

    def __repr__(self):
        return "GdxSymbol({:s},{:d},{:s},file={:s},index={:s})".format(
                   self.name,
                   self.data_type,
                   self.dims,
                   self.file,
                   self.index)

    def __str__(self):
        s = self.name
        s += ", " + self.description    
        s += ", " + self.full_typename    
        s += ", {} records".format(self.num_records)
        s += ", {} dims {}".format(self.num_dims, self.dims)
        s += ", loaded" if self.loaded else ", not loaded"
        return s

    def load(self):
        if self.loaded:
            logger.info("Nothing to do. Symbol already loaded.")
            return
        if not self.file:
            raise Error("Cannot load {} because there is no file pointer".format(repr(self)))
        if not self.index:
            raise Error("Cannot load {} because there is no symbol index".format(repr(self)))

        if self.data_type == GamsDataType.Parameter and HAVE_GDX2PY:
            self.dataframe = gdx2py.par2list(self.file.filename,self.name) 
            self._loaded = True
            return

        raise NotImplementedError()
