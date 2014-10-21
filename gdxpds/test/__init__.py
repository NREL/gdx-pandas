import os

# if True, test products will be deleted on tear down
clean_up = True

bin_prefix = ''
candidate = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'bin')
if os.path.isdir(candidate) and os.path.isfile(os.path.join(candidate, 'gdx_to_csv.py')):
    bin_prefix = candidate
