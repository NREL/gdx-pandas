# Developer How-To

## Create a new release

- Make the release on github
- Install from github and make sure tests pass
- Create package and push to pypi:

    ```
    python setup.py sdist
    twine upload --repository testpypi dist/*
    # look at https://test.pypi.org/project/gdxpds/
    twine upload --repository pypi dist/*
    ```
    