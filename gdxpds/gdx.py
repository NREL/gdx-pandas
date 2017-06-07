from __future__ import absolute_import

from builtins import super
from collections import OrderedDict
from enum import Enum
import logging

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
        self._symbol_count = 0
        self.universal_set = None
        self.symbols = OrderedDict()

        super().__init__(gams_dir=gams_dir)
        self._H = self._create_gdx_object()

    @property
    def empty(self):
        """
        Returns True if this GdxFile object contains any data.
        """
        return not (self._version or self._universal_set)

    @property
    def H(self):
        """
        GDX object handle
        """
        return self._H

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

    def read(self,filename):
        """
        Opens gdx file at filename and reads meta-data. If not self.lazy_load, 
        also loads all symbols.

        Throws an Error if not self.empty.

        Throws a GdxError if any calls to gdxcc fail.
        """
        if not self.empty:
            raise Error("GdxFile.read can only be used if the GdxFile is .empty.")

        # open the file
        rc = gdxcc.gdxOpenRead(self.H,filename)
        if not rc[0]:
            raise GdxError(self.H,"Could not open '{}'".format(filename))

        # read in meta-data ...
        # ... for the file
        ret, self._version, self._producer = gdxcc.gdxFileVersion(self.H)
        if ret != 1: 
            raise GDXError(self.H,"Could not get file version.")
        ret, symbol_count, element_count = gdxcc.gdxSystemInfo(self.H)
        logger.info("Opening '{}' with {} symbols and {} elements with lazy_load = {}.".format(filename,symbol_count,element_count,self.lazy_load))
        # ... for the symbols
        ret, name, dims, data_type = gdxcc.gdxSymbolInfo(self.H,0)
        if ret != 1:
            raise GdxError(self.H,"Could not get symbol info for the universal set.")
        self.universal_set = GamsSymbol(name,data_type,dims,H=self.H,index=0)
        for i in range(symbol_count):
            index = i + 1
            ret, name, dims, data_type = gdxcc.gdxSymbolInfo(self.H,index)
            if ret != 1:
                raise GdxError(self.H,"Could not get symbol info for symbol {}.".format(index))
            self.symbols[name] = GamsSymbol(name,data_type,dims,H=self.H,index=index)

        # read all symbols if not lazy_load


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


class GdxSymbol(object): 
    def __init__(self,name,data_type,dims,H=None,index=None): 
        self.name = name
        self.data_type = GamsDataType(data_type)
        self.dims = dims
        self._H = H
        self._index = index

        if self.H:
            # loading
            self._loaded = False
            # get additional meta-data

        else:
            # writing
            self._loaded = True

    @property
    def H(self):
        return self._H

    @property
    def index(self):
        return self._index

    @property
    def loaded(self):
        return self._loaded

