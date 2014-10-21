
from distutils.core import setup
import gdxpds

setup(
    name = 'gdxpds',
    version = gdxpds.__version__,
    author = 'Elaine T. Hale',
    author_email = 'elaine.hale@nrel.gov',
    packages = ['gdxpds', 'gdxpds.test'],
    scripts = ['bin/csv_to_gdx.py', 'bin/gdx_to_csv.py']
    url = 'https://github.nrel.gov/ehale/gdx-pandas',
    description = 'Python package to translate between gdx (GAMS data) and pandas.',
    package_data={
        'gdxpds.test': ['gdxpds/test/*.csv',
                        'gdxpds/test/*.gdx']
    },
    install_requires=open('requirements.txt').read()
)