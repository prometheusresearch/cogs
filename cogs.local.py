#
# Copyright (c) 2013, Prometheus Research, LLC
# Released under MIT license, see `LICENSE` for details.
#


from cogs import task, env
from cogs.fs import exe


@task
def TEST():
    """run regression tests"""
    with env(debug=True):
        exe("pbbt test/input.yaml test/output.yaml -q")


@task
def TRAIN():
    """run regression tests in the train mode"""
    with env(debug=True):
        exe("pbbt test/input.yaml test/output.yaml --train")


@task
def PURGE_TEST():
    """purge stale output records from regression tests"""
    with env(debug=True):
        exe("pbbt test/input.yaml test/output.yaml -q --train --purge")


@task
def LINT():
    """detect errors in the source code with PyFlakes"""
    with env(debug=True):
        exe("pyflakes src/cogs")


