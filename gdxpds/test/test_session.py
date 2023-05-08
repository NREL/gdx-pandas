import os
import shutil

import pytest

from gdxpds.test import run_dir

STARTUP = True

@pytest.fixture(scope="session",autouse=True)
def manage_rundir(request, clean_up):
    """
    At the beginning of the session, creates the test run_dir. If test.clean_up,
    deletes this folder after the tests have finished running.

    Arguments
    - request contains the pytest session, including collected tests
    """
    global STARTUP
    if STARTUP:
        if os.path.exists(run_dir):
            # create clean space for running tests
            shutil.rmtree(run_dir)
        STARTUP = False
        os.mkdir(run_dir)
    def finalize_rundir():
        if os.path.exists(run_dir) and clean_up:
            shutil.rmtree(run_dir)
    request.addfinalizer(finalize_rundir)
