# Copyright (c) 2011 Incremental IP Limited
# see LICENSE for license information

import gdxcc
import sys
import os
import re


#- Errors ----------------------------------------------------------------------

class GDX_error(Exception):
     def __init__(self, H, msg):
         self.msg = msg
         if H:
             self.msg += ": " + gdxcc.gdxErrorStr(H, gdxcc.gdxGetLastError(H))[1]


#- GDX utilities ---------------------------------------------------------------

windows_gams_dir = None
def find_gams_on_windows():
    global windows_gams_dir
    if windows_gams_dir: return windows_gams_dir

    prog_dirs = ()
    for f in os.listdir("C:\\"):
        if f.startswith("Program Files"):
            prog_dirs = prog_dirs + (f,)

    gams_dirs = ()
    for p in prog_dirs:
        for f in os.listdir("C:\\" + p):
            if f.startswith("GAMS"):
                gams_dirs = gams_dirs + ("C:\\" + p + "\\" + f,)

    best_version = 0.0
    best_dir = None
    for g in gams_dirs:
        version = float(re.search("GAMS([0-9\.]+)", g).group(1))
        if version > best_version:
            version = best_version
            best_dir = g
    
    windows_gams_dir = best_dir
    return windows_gams_dir
                    

paths = {
    "darwin":           "/Applications/GAMS",
    "win32":            find_gams_on_windows,
}

def open(system_dir=None):
    H = gdxcc.new_gdxHandle_tp()
    if system_dir == None:
        system_dir = paths[sys.platform]
        if type(system_dir) != str:
            system_dir = system_dir()
    if not system_dir:
        raise GDX_error(None, "Couldn't find the GAMS system directory")
    rc = gdxcc.gdxCreateD(H, system_dir, gdxcc.GMS_SSSIZE)
    if not rc[0]: raise GDX_error(H, rc[1])
    return H


def file_info(H):
    ret, version, producer = gdxcc.gdxFileVersion(H)
    if ret != 1: raise GDX_error("Couldn't get file version")
    ret, symbol_count, element_count = gdxcc.gdxSystemInfo(H)
    if ret != 1: raise GDX_error(H, "Couldn't get file info")
    return {
      "version": version,
      "producer": producer,
      "symbol_count": symbol_count,
      "element_count": element_count
    }


symbol_type_text = [ "Set", "Parameter", "Variable", "Equation", "Alias" ]
variable_type_text = [ "Unknown", "Binary", "Integer", "Positive", "Negative", "Free", "Sos1", "Sos2", "Semicont", "Semiint" ]
def symbol_info(H, num):
    ret, name, dims, type = gdxcc.gdxSymbolInfo(H, num)
    if ret != 1: raise GDX_error(H, "Couldn't get symbol info")
    ret, records, userinfo, description = gdxcc.gdxSymbolInfoX(H, num)
    if ret != 1: raise GDX_error(H, "Couldn't get extended symbol info")

    if type == gdxcc.GMS_DT_PAR and dims == 0:
        typename = "Scalar"
    else:
        typename = symbol_type_text[type]

    full_typename = ""
    if type == gdxcc.GMS_DT_VAR:
        full_typename = variable_type_text[userinfo] + " "
    full_typename += typename

    domain = [None] * dims
    if dims > 0 and num > 0:
        ret, gdx_domain = gdxcc.gdxSymbolGetDomain(H, num)
        if ret != 1: raise GDX_error(H, "Couldn't get symbol domain")
        if len(gdx_domain) < dims: gdx_domain = None
        for i in range(dims):
            d = gdx_domain[i] if gdx_domain else 0
            domain[i] = { "index": d }
            if d == 0:
                domain[i]["key"] = "*"
            else:
                ret, domain[i]["key"], dummy1, dummy2 = gdxcc.gdxSymbolInfo(H, d)

    return {
      "name": name,
      "number": num,
      "type": type,
      "typename": typename,
      "full_typename": full_typename,
      "dims": dims,
      "records": records,
      "userinfo": userinfo,
      "description": description,
      "domain": domain
     }


#- EOF -------------------------------------------------------------------------

