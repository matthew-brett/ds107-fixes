""" Write new versions of subject 43 tsv files
"""

from os.path import join as pjoin

from ana_cogent import proc_cogent, write_stimuli


for in_fname, out_fname in (
    (pjoin('cogents', 'sub-43', 'oneback_1.log'),
    pjoin('tsvs', 'sub-43', 'func',
        'sub-43_task-onebacktask_run-01_events.tsv')),
    (pjoin('cogents', 'sub-43', 'oneback_2.log'),
    pjoin('tsvs', 'sub-43', 'func',
        'sub-43_task-onebacktask_run-02_events.tsv')),
):
    stimuli = proc_cogent(in_fname)
    write_stimuli(stimuli, out_fname)
