# [LICENSE]
# Copyright (c) 2018, Alliance for Sustainable Energy.
# All rights reserved.
# 
# Redistribution and use in source and binary forms, 
# with or without modification, are permitted provided 
# that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above 
# copyright notice, this list of conditions and the 
# following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the 
# above copyright notice, this list of conditions and the 
# following disclaimer in the documentation and/or other 
# materials provided with the distribution.
# 
# 3. Neither the name of the copyright holder nor the 
# names of its contributors may be used to endorse or 
# promote products derived from this software without 
# specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND 
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, 
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF 
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR 
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, 
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, 
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) 
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE 
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# [/LICENSE]

import os

# if True, test products will be deleted on tear down
clean_up = True

base_dir = os.path.dirname(__file__)
run_dir = os.path.join(base_dir, 'output')

def apply_dirname(f, num_times):
    ret = f
    for _i in range(num_times):
        ret = os.path.dirname(ret)
    return ret

bin_prefix = ''    
# git repo (development)
candidate = os.path.join(apply_dirname(__file__,3), 'bin')
if os.path.isdir(candidate) and os.path.isfile(os.path.join(candidate,'gdx_to_csv.py')):
    bin_prefix = candidate

# anaconda set-up
candidate = os.path.join(apply_dirname(__file__,6), 'bin')
if os.path.isdir(candidate) and os.path.isfile(os.path.join(candidate,'gdx_to_csv.py')):
    bin_prefix = candidate

# install location for Windows
candidate = os.path.join(apply_dirname(__file__,5), 'Scripts')
if bin_prefix == '' and os.path.isdir(candidate) and os.path.isfile(os.path.join(candidate,'gdx_to_csv.py')):
    bin_prefix = candidate

# install location for Linux
candidate = os.path.join('/','usr','local','bin')
if bin_prefix == '' and os.path.isdir(candidate) and os.path.isfile(os.path.join(candidate,'gdx_to_csv.py')):
    bin_prefix = candidate
