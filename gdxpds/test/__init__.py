import os

# if True, test products will be deleted on tear down
clean_up = True

def apply_dirname(f, num_times):
    ret = f
    for i in range(num_times):
        ret = os.path.dirname(ret)
    return ret

bin_prefix = ''    
# git repo (development)
candidate = os.path.join(apply_dirname(__file__,3), 'bin')
if os.path.isdir(candidate) and os.path.isfile(os.path.join(candidate, 'gdx_to_csv.py')):
    bin_prefix = candidate

# install location for Windows
candidate = os.path.join(apply_dirname(__file__,5), 'Scripts')
if bin_prefix == '' and os.path.isdir(candidate) and os.path.isfile(os.path.join(candidate, 'gdx_to_csv.py')):
    bin_prefix = candidate

# TODO: install location for Mac

# TODO: install location for Linux