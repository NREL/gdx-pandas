'''
'''

from distutils.core import setup
import os

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'gdxpds', '_version.py'), encoding='utf-8') as f:
    version = f.read()

version = version.split()[2].strip('"').strip("'")

setup(
    name = 'gdxpds',
    version = version,
    author = 'Elaine T. Hale',
    author_email = 'elaine.hale@nrel.gov',
    packages = ['gdxpds', 'gdxpds.test'],
    scripts = ['bin/csv_to_gdx.py', 'bin/gdx_to_csv.py'],
    url = 'https://github.com/NREL/gdx-pandas',
    description = 'Python package to translate between gdx (GAMS data) and pandas.',
    long_description=open('README.txt').read(),
    package_data={
        'gdxpds.test': ['*.csv','*.gdx']
    },
    install_requires=open('requirements.txt').read()
)
