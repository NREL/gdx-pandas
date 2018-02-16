
from distutils.core import setup

setup(
    name = 'gdxpds',
    version = "1.0.3",
    author = 'Elaine T. Hale',
    author_email = 'elaine.hale@nrel.gov',
    packages = ['gdxpds', 'gdxpds.test'],
    scripts = ['bin/csv_to_gdx.py', 'bin/gdx_to_csv.py'],
    url = 'https://github.com/NREL/gdx-pandas',
    description = 'Python package to translate between gdx (GAMS data) and pandas.',
    long_description=open('README.md').read(),
    package_data={
        'gdxpds.test': ['*.csv','*.gdx']
    },
    install_requires=open('requirements.txt').read()
)
