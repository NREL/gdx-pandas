'''
[LICENSE]
Copyright (c) 2015, Alliance for Sustainable Energy.
All rights reserved.

Redistribution and use in source and binary forms, 
with or without modification, are permitted provided 
that the following conditions are met:

1. Redistributions of source code must retain the above 
copyright notice, this list of conditions and the 
following disclaimer.

2. Redistributions in binary form must reproduce the 
above copyright notice, this list of conditions and the 
following disclaimer in the documentation and/or other 
materials provided with the distribution.

3. Neither the name of the copyright holder nor the 
names of its contributors may be used to endorse or 
promote products derived from this software without 
specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND 
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, 
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF 
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR 
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, 
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, 
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) 
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE 
OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
[/LICENSE]
'''
# Copyright (c) 2011 Incremental IP Limited
# see LICENSE for license information

# Performance improvements added by Elaine Hale, 12/2014
#     - lazy_load
#     - caching, etc.

import gdxcc
import gdxpds.gdxx as gdxx
import sys
import string
from collections import OrderedDict
import time


#- Errors ----------------------------------------------------------------------

class gdxdict_error(Exception):
     def __init__(self, msg):
         self.msg = msg


#- Data ------------------------------------------------------------------------

level_names = [ ".l", ".m", ".lo", ".ub", ".scale" ]

type_codes = {
    "set": 0,
    "parameter": 1,
    "scalar": 1,
    "variable": 2,
    "equation": 3,
    "alias": 4,
}

def get_type_code(typename):
    return type_codes[string.lower(typename)]


GMS_SV_PINF = 3e300
GMS_SV_MINF = 4e300

default_variable_fields = [
#     .l   .m           .lo         .ub  .scale
    [ 0.0, 0.0,         0.0,         0.0, 1.0 ],    # unknown
    [ 0.0, 0.0,         0.0,         1.0, 1.0 ],    # binary
    [ 0.0, 0.0,         0.0,       100.0, 1.0 ],    # integer
    [ 0.0, 0.0,         0.0, GMS_SV_PINF, 1.0 ],    # positive
    [ 0.0, 0.0, GMS_SV_MINF,         0.0, 1.0 ],    # negative
    [ 0.0, 0.0, GMS_SV_MINF, GMS_SV_PINF, 1.0 ],    # free
    [ 0.0, 0.0,         0.0, GMS_SV_PINF, 1.0 ],    # sos1
    [ 0.0, 0.0,         0.0, GMS_SV_PINF, 1.0 ],    # sos2
    [ 0.0, 0.0,         1.0, GMS_SV_PINF, 1.0 ],    # semicont
    [ 0.0, 0.0,         1.0,       100.0, 1.0 ]     # semiint
]


#- One dimension of a gdxdict --------------------------------------------------

class gdxdim(object):

    def __init__(self, parent, symbol_name = None):
        self.parent = parent
        self.items = {}
        self.info = {}
        self.key_map = {}
        self.symbol_name = symbol_name
        self.__read_in = True
        if symbol_name is not None:
            self.__read_in = False
        self.__my_key_names = []
        
    def __setitem__(self, key, value):
        kl = self.parent.add_key(key)
        self.items[kl] = value
        self.__my_key_names.append(self.parent.universal[kl]['name'])
        # cache key.lower()
        self.key_map[key] = kl
        self.key_map[kl] = kl
        self.__read_in = True

    def __getitem__(self, key):
        if not self.__read_in:
            self.__read_in_now()
        try:
            return self.items[self.key_map[key]]
        except:
            kl = key.lower()
            if kl in self.items:
                self.key_map[key] = kl
            return self.items[kl]

    def __iter__(self):
        if not self.__read_in:
            self.__read_in_now()
        for key_name in self.__my_key_names:
            yield key_name

    def __contains__(self, key):
        if not self.__read_in:
            self.__read_in_now()
        return (key in self.key_map) or (key.lower() in self.items)

    def getinfo(self, key, ikey=None):
        kl = key.lower()
        if kl in self.info:
            if ikey:
                return self.info[kl][ikey]
            else:
                return self.info[kl]
        else:
            if ikey:
                return None
            else:
                return {}

    def setinfo(self, key, ikey=None, value=None):
        kl = self.key_map[key] if key in self.key_map else key.lower()
        if not kl in self.info:
            self.info[kl] = {}
        if ikey:
            self.info[kl][ikey] = value
        else:
            return self.info[kl]
            
    def __read_in_now(self): 
        self.parent.read_symbol(self.symbol_name)
        assert(self.__read_in)
        

#- Reading tools ---------------------------------------------------------------

def read_symbol(H, d, name, typename, values):
    d[name] = True if typename == "Set" else values[gdxcc.GMS_VAL_LEVEL]

    if typename[0] == "V" or typename[0] == "E":
        # typename is 'Variable' or 'Equation'
        limits = OrderedDict()
        for i, level_name in enumerate(level_names):
            limits[level_name] = values[i]
        d.setinfo(name)["limits"] = limits
    elif typename[0:2] == "Se":
        # typename is 'Set'
        ret, description, node = gdxcc.gdxGetElemText(H, int(values[gdxcc.GMS_VAL_LEVEL]))
        if ret != 0:
            d.setinfo(name)["description"] = description


#- Writing Tools ---------------------------------------------------------------

values = gdxcc.doubleArray(gdxcc.GMS_VAL_MAX)


def set_symbol(H, d, name, typename, userinfo, values, dims):
    if typename == "Set":
        text_index = 0
        if "description" in d.getinfo(name):
            ret, text_index = gdxcc.gdxAddSetText(H, d.getinfo(name)["description"])
        values[gdxcc.GMS_VAL_LEVEL] = float(text_index)
    else:
        values[gdxcc.GMS_VAL_LEVEL] = d[name]

    if (typename == "Variable" or typename == "Equation") and "limits" in d.getinfo(name):
        limits = d.getinfo[name]("limits")
        for i in range(1, 5):
            ln = level_names[i]
            if ln in limits:
                values[i] = limits[ln]

    gdxcc.gdxDataWriteStr(H, dims + [name], values)


def write_symbol(H, typename, userinfo, s, dims):
    for k in s:
        s2 = s[k]
        if isinstance(s2, gdxdim):
            write_symbol(H, typename, userinfo, s2, dims + [k])
        else:
            set_symbol(H, s, k, typename, userinfo, values, dims)


#- Guessing domains ------------------------------------------------------------

def guess_domains(G, set_map, all_keys):
    # We don't always get symbol domains from GDX (in 23.7.2 and below
    # gdxSymbolGetDomain doesn't work and otherwise, some GDX files don't seem
    # to contain this information).  So here we try to guess

    # Then run through all the symbols trying to guess any missing domains
    for k in G:
        info = G.getinfo(k)
        if info["dims"] > 0:
            skip = True
            for i in range(info["dims"]):
                if info["domain"][i]["key"] == "*": skip = False
            if skip: continue

            if not k in all_keys: continue
            keys = all_keys[k]

            for i in range(info["dims"]):
                if info["domain"][i]["key"] != "*": continue
                # For each dimension that currently has '*' as its domain,
                # work out all the possible sets
                pd = None
                for j in keys[i]:
                    if pd == None:
                        pd = {}
                        if j in set_map:
                            for s in set_map[j]: pd[s] = True
                    else:
                        remove = []
                        for s in pd:
                            if not s in set_map[j]: remove.append(s)
                        for r in remove: del pd[r]

                # If the symbol is a set itself, then we probably found that, but we don't want it
                if pd and k in pd: del pd[k]
                if pd and len(pd) > 0:
                    # If we found more than one possible set, pick the shortest
                    # one: our guess is that the set is the smallest set that
                    # contains all the keys that appear in this dimension
                    smallest_set = None
                    length = 1e9 # Can you get DBL_MAX in Python?  A billion out to be enough for anyone.
                    min_length = 0
                    # If we're working with a set, we don't want to pick a set
                    # with the exact same length - we want this to be a subset
                    # of a longer set
                    if info["type"] == gdxcc.GMS_DT_SET:
                        min_length = len(keys[i])
                    for s in pd:
                        l = G.getinfo(s)["records"]
                        if l < length and l > min_length:
                            length = l
                            smallest_set = s
                    if smallest_set:
                        info["domain"][i] = { "index":G.getinfo(smallest_set)["number"], "key":smallest_set }


def guess_ancestor_domains(G):
    for k in G:
        info = G.getinfo(k)
        if info["dims"] == 0: continue
        for i in range(info["dims"]):
            ancestors = [info["domain"][i]["key"]]
            while ancestors[-1] != '*':
                ancestors.append(G.getinfo(ancestors[-1])["domain"][0]["key"])
            info["domain"][i]["ancestors"] = ancestors


#- GDX Dict --------------------------------------------------------------------

class gdxdict:

    def __init__(self, lazy_load = False):
        self.file_info = {}

        self.universal = OrderedDict()
        self.__universal_items = None # cache for self.universal.items()
        self.universal_info = {}

        self.symbols = {}
        self.symbol_names = {}
        self.info = {}
        
        self.key_map = {}
        
        self.lazy_load = lazy_load

    def __getitem__(self, key):
        return self.symbols[key.lower()]

    def __setitem__(self, key, value):
        self.symbols[key.lower()] = value

    def __contains__(self, key):
        return key.lower() in self.symbols

    def __iter__(self):
        seen = {}
        for stage in range(4):
            for k in self.symbols:
                info = self.getinfo(k)
                dims = info["dims"]
                domain1 = dims > 0 and info["domain"][0]["key"]
                typename = "typename" in info and info["typename"]
                if (not k in seen and
                    ((stage == 0 and typename == "Set" and dims == 1 and domain1 == "*") or
                     (stage == 1 and typename == "Set" and dims == 1 and domain1 != "*") or
                     (stage == 2 and typename == "Set" and dims > 1) or
                     (stage == 3 and typename != "Set"))):
                    for d in info["domain"]:
                        dkl = d["key"].lower()
                        if dkl != "*" and not dkl in seen:
                            yield self.symbol_names[dkl]
                            seen[dkl] = True
                    yield self.symbol_names[k]
                    seen[k] = True
                    
    def universal_items(self):
        if self.__universal_items is None:
            self.__universal_items = self.universal.items()
        return self.__universal_items

    def getinfo(self, key, ikey=None):
        kl = key.lower()
        if ikey:
            return self.info[kl][ikey]
        else:
            return self.info[kl]

    def setinfo(self, key, ikey=None, value=None):
        kl = key.lower()
        if not kl in self.info:
            self.info[kl] = {}
        if ikey:
            self.info[kl] = value
        else:
            return self.info[kl]

    def add_key(self, key, description=None):
        kl = None
        if key in self.key_map:
            kl = self.key_map[key]
        else:
            kl = key.lower()
            self.key_map[key] = kl
            if not kl in self.universal:
                self.universal[kl] = { 'name': key, 'description': description }
                self.key_map[kl] = kl
                self.__universal_map = None
        return kl

    def add_symbol(self, info):
        key = info["name"].lower()
        if not "type" in info and "typename" in info:
            info["type"] = get_type_code(info["typename"])
        if not "userinfo" in info:
            info["userinfo"] = 0
        if not "description" in info:
            info["description"] = ""
        
        if not key in self.info:
            self.info[key] = {}
            if info["dims"] > 0:
                symbol_name = info['name'] if self.lazy_load else None
                self.symbols[key] = gdxdim(self, symbol_name)
            else:
                self.symbols[key] = None
            self.symbol_names[key] = info["name"]
        else:
            sinfo = self.info[key]
            if "type" in sinfo and "type" in info and sinfo["type"] != info["type"]:
                raise gdxdict_error("Incompatible types for symbol '%s' (%s and %s)" % (info["name"], sinfo["type"], info["type"]))
            if "dims" in sinfo and "dims" in info and sinfo["dims"] != info["dims"]:
                raise gdxdict_error("Incompatible dimensions for symbol '%s' (%d and %d)" % (info["name"], sinfo["dims"], info["dims"]))
            if "domain" in sinfo and "domain" in info:
                for d in range(len(sinfo["domain"])):
                    d1 = sinfo["domain"][d]
                    d2 = info["domain"][d]
                    if d1 and d2 and d1["key"] != d2["key"]:
                        raise gdxdict_error("Incompatible domain %d for symbol '%s' (%s and %s)" % (d, info["name"], d1["key"], d2["key"]))

        for k in info:
            if not k in self.info[key]:
                self.info[key][k] = info[k]

    def set_type(self, name, t):
        if type(t) == str:
            typename = t
            typecode = get_type_code(t)
        else:
            typecode = t
            typename = gdxx.symbol_type_text[t]
    
        info = self.setinfo(name)
        if "type" in info and info["type"] != typecode:
            raise gdxdict_error("Incompatible types for symbol '%s' (%s and %s)" % (name, info["typename"], typename))
            
        info["type"] = typecode
        info["typename"] = typename


# -- Read a gdx file -----------------------------------------------------------

    def read(self, filename, gams_dir=None):
        if self.lazy_load:
            self.filename = filename
            self.gams_dir = gams_dir
    
        H = gdxx.open(gams_dir)
        assert gdxcc.gdxOpenRead(H, filename)[0], "Couldn't open %s" % filename

        info = gdxx.file_info(H)
        for k in info:
            if not k in self.file_info:
                self.file_info[k] = info[k]

        # read the universal set
        uinfo = gdxx.symbol_info(H, 0)
        for k in uinfo:
            if not k in self.universal_info: 
                self.universal_info[k] = uinfo[k]

        ok, records = gdxcc.gdxDataReadStrStart(H, 0)        
        for i in range(records):
            ok, elements, values, afdim = gdxcc.gdxDataReadStr(H)
            if not ok: raise gdxx.GDX_error(H, "Error in gdxDataReadStr")
            key = elements[0]
            ret, description, node = gdxcc.gdxGetElemText(H, int(values[gdxcc.GMS_VAL_LEVEL]))
            if ret == 0: description = None
            self.add_key(key, description)
        
        all_keys = {}

        # Read all the 1-D sets
        # Map backwards so we have a map from every set key back to all the sets it's in
        set_map = {}
        for i in range(1, info["symbol_count"]+1):
            sinfo = gdxx.symbol_info(H, i)
            if sinfo["typename"] == "Set" and sinfo["dims"] == 1:

                self.add_symbol(sinfo)
                symbol_name = sinfo["name"]
                all_keys[symbol_name] = [{}]
                keys = all_keys[symbol_name]
                symbol = self[symbol_name]
                symbol._gdxdim__read_in = True
                ok, records = gdxcc.gdxDataReadStrStart(H, i)
                for i in range(records):
                    ok, elements, values, afdim = gdxcc.gdxDataReadStr(H)
                    if not ok: raise gdxx.GDX_error(H, "Error in gdxDataReadStr")
                    e = elements[0]
                    read_symbol(H, symbol, e, sinfo["typename"], values)
                    if not e in set_map: set_map[e] = {}
                    set_map[e][symbol_name] = True
                    keys[0][e] = True
        
        # Read all the other symbols
        for i in range(1, info["symbol_count"]+1):
            sinfo = gdxx.symbol_info(H, i)
            if sinfo["typename"] == "Set" and sinfo["dims"] == 1: continue

            self.add_symbol(sinfo)
            if self.lazy_load and sinfo["dims"] > 0:
                continue
                
            self.__read_one_symbol(H, sinfo, all_keys)

        gdxcc.gdxClose(H)
        gdxcc.gdxFree(H)

        guess_domains(self, set_map, all_keys)
        guess_ancestor_domains(self)
        if self.lazy_load:
            self.set_map = set_map
            self.all_keys = all_keys
        
    def read_symbol(self, symbol_name):
        if not (self.lazy_load and self.filename):
            raise RuntimeError("""This feature only works if the gdxdict is initialized in 
                               lazy_load mode, and read has already been called.""")
        if not symbol_name in self:
            raise RuntimeError("{} is not a symbol in this gdxdict.".format(symbol_name))
            
        H = gdxx.open(self.gams_dir)
        assert gdxcc.gdxOpenRead(H, self.filename)[0], "Couldn't open %s" % filename
        
        sinfo = self.getinfo(symbol_name)
        set_map = self.set_map
        all_keys = self.all_keys
        
        self.__read_one_symbol(H, sinfo, all_keys)

        gdxcc.gdxClose(H)
        gdxcc.gdxFree(H)

        guess_domains(self, set_map, all_keys)
        guess_ancestor_domains(self)
        self.set_map = set_map
        self.set_map = all_keys
        
    def __read_one_symbol(self, H, sinfo, all_keys):
        symbol_name = sinfo["name"]
        all_keys[symbol_name] = []
        keys = all_keys[symbol_name]
        for d in range(sinfo["dims"]): keys.append({})

        ok, records = gdxcc.gdxDataReadStrStart(H, sinfo["number"])
    
        symbol = self[symbol_name]
        if isinstance(symbol, gdxdim):
            symbol._gdxdim__read_in = True
            
        current_list = [(symbol_name, symbol)]
        for i in range(records):
            ok, elements, values, afdim = gdxcc.gdxDataReadStr(H)
            if not ok: raise gdxx.GDX_error(H, "Error in gdxDataReadStr")
            if sinfo["dims"] == 0:
                read_symbol(H, self, symbol_name, sinfo["typename"], values)
            else:
                for d in range(sinfo["dims"]-1):
                    key = elements[d]
                    keys[d][key] = True
                    if (len(current_list) < d+2) or (current_list[d+1][0] != key):
                        current_list = current_list[0:d+1]
                        if not key in current_list[d][1]:
                            current_list[d][1][key] = gdxdim(self)
                        current_list = current_list + [(key, current_list[d][1][key])]
                d = sinfo["dims"]-1
                key = elements[d]
                keys[d][key] = True
                read_symbol(H, current_list[d][1], key, sinfo["typename"], values)

#- Write a GDX file ------------------------------------------------------------

    def write(self, filename, gams_dir=None):
        H = gdxx.open(gams_dir)
        assert gdxcc.gdxOpenWrite(H, filename, "gdxdict.py")[0], "Couldn't open %s" % filename

        # write the universal set
        gdxcc.gdxUELRegisterRawStart(H)
        for key, key_data in self.universal_items():
            gdxcc.gdxUELRegisterRaw(H, key_data['name'])
        gdxcc.gdxUELRegisterDone(H)

        for k in self:
            symbol = self[k]
            info = self.getinfo(k)
            if info["dims"] == 0:
                if not gdxcc.gdxDataWriteStrStart(H, k, info["description"], 0, get_type_code(info["typename"]), info["userinfo"]):
                    raise gdxx.GDX_error(H, "couldn't start writing data")
                set_symbol(H, self, k, info["typename"], info["userinfo"], values, [])
                gdxcc.gdxDataWriteDone(H)
            else:
                if not gdxcc.gdxDataWriteStrStart(H, k, info["description"], info["dims"], get_type_code(info["typename"]), info["userinfo"]):
                    raise gdxx.GDX_error(H, "couldn't start writing data")
                domain = []
                for d in info["domain"]:
                    domain.append(d["key"])
                if gdxcc.gdxSymbolSetDomain(H, domain) != 1:
                    raise gdxx.GDX_error(H, "couldn't set domain for symbol %s to %s" % (k, domain))
                write_symbol(H, info["typename"], info["userinfo"], symbol, [])
                gdxcc.gdxDataWriteDone(H)

        gdxcc.gdxClose(H)
        gdxcc.gdxFree(H)


#- UEL Handling ----------------------------------------------------------------

    def merge_UELs(self, G2):
        for key, key_data in G2.universal_items():
            self.add_key(key_data['name'], key_data['description'])


#- EOF -------------------------------------------------------------------------
