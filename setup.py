
from distutils.core import setup
import gdxpds

setup(
    name = 'gdxpds',
    version = gdxpds.__version__,
    author = 'Elaine T. Hale',
    author_email = 'elaine.hale@nrel.gov',
    packages = ['gdxpds'],
    url = 'https://github.nrel.gov/ehale/gdx-pandas',
    description = 'Python package to translate between gdx (GAMS data) and pandas.',
    install_requires=open('requirements.txt').read()
)