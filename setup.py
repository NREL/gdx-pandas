from pathlib import Path
from setuptools import setup, find_packages

here = Path(__file__).parent.resolve()
metadata = {}

with open(here / "gdxpds" / "_version.py", encoding='utf-8') as f:
    exec(f.read(), None, metadata)

with open(here / "README.txt", encoding="utf-8") as f:
    readme = f.read()

test_requires = [
    "pytest"
]

admin_requires = [
    "ghp-import",
    "numpydoc",
    "pandoc",
    "sphinx",
    "sphinx_rtd_theme",
    "twine",
    "setuptools",
    "wheel",
]

setup(
    name = metadata["__title__"],
    version = metadata["__version__"],
    author = metadata["__author__"],
    author_email = metadata["__author_email__"],
    url = metadata["__url__"],
    description = metadata["__description__"],
    long_description=readme,
    packages=find_packages(),
    package_data={
        'gdxpds.test': ['*.csv','*.gdx']
    },
    scripts = [
        'bin/csv_to_gdx.py', 
        'bin/gdx_to_csv.py'
    ],
    install_requires=[
        "enum34; python_version < '3.4'",
        "gdxcc",
        "pandas>=0.20.1",
        "numpy>=1.7"
    ],
    extras_require={
        "test": test_requires,
        "admin": test_requires + admin_requires
    },
)
