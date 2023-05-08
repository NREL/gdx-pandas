import os

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
