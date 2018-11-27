""" Tests for ds107 onsets module
"""

from os.path import (join as pjoin, dirname, relpath)
from glob import glob
from tempfile import TemporaryDirectory

from onftools.tsvtools import write_tasks
from onftools.check3col import check_task

from ds107_onsets import TASK_DEFS

HERE = dirname(__file__)
NEW_COND_PATH = pjoin(HERE, 'tsvs')
OLD_COND_PATH = pjoin(HERE, 'old_onsets')


def test_tasks():
    for task_name, added_args in (
        ('onebacktask', {}),
    ):
        with TemporaryDirectory() as tmpdir:
            info = TASK_DEFS[task_name]
            task_defs = {task_name: info}
            write_tasks(NEW_COND_PATH, task_defs, tmpdir)
            for tsv_path in glob(pjoin(NEW_COND_PATH,
                                       'sub-*',
                                       'func',
                                       'sub*{}*.tsv'.format(task_name))):
                # These were broken in the original
                if 'sub-43' in tsv_path:
                    continue
                label_path = pjoin(tmpdir,
                                   relpath(dirname(tsv_path), NEW_COND_PATH))
                check_task(tsv_path, OLD_COND_PATH, info,
                           label_path=label_path, **added_args)
