""" Process Cogent file to generate OpenFMRI .tsv equivalent
"""

import re
import io
from os.path import join as pjoin

from nibabel.openers import Opener

timing_re = re.compile('\d+\t\[\d+\]')

BAD_LOOKUP = {1: 'Words',
              2: 'Objects',
              3: 'Scrambled objects',
              4: 'Consonant strings'}

GOOD_LOOKUP = {1: 'Words',
               3: 'Objects',
               4: 'Scrambled objects',
               2: 'Consonant strings'}

COL_FORMATS = (('onset', '{:.3f}'),
               ('duration', '{:.3f}'),
               ('trial_type', '{!s}'),
               ('0', '{!s}'),
               ('1', '{:d}'),
               ('2', '{!s}'),
               ('3', '{!s}'))

COL_NAMES = tuple(n for n, f in COL_FORMATS)
COL_FMT_STR = '\t'.join(f for n, f in COL_FORMATS) + '\n'

DURATION = 0.35


def proc_cogent(fname):
    """ Process Cogent file
    """
    with open(fname, 'rt') as fobj:
        content = fobj.read()

    lines = content.splitlines()

    for i, line in enumerate(lines):
        if timing_re.match(line):
            break
    else:
        raise ValueError(f'No timing lines in {fname}')

    parts_0 = lines[i].split('\t')
    assert parts_0[-1].strip() == 'COGENT START'
    parts_1 = lines[i + 1].split('\t')
    last_part = parts_1[-1].strip()
    assert last_part.startswith('Start of experiment: ')
    start_onset = int(parts_1[0])
    start_time = int(last_part.split(':')[1])
    assert start_onset >= start_time <= start_onset + 1
    parts_m1 = lines[-1].split('\t')
    assert parts_m1[-1].strip() == 'COGENT STOP'
    # In fact, the start time seems to come from the first stimulus
    start_time = int(lines[i + 2].split('\t')[0])

    def exp_time(raw_time, start_time):
        return round((int(raw_time) - start_time) / 1000, 1)

    stimuli = []
    last_time = None
    for line in lines[i + 2:-1]:
        assert timing_re.match(line)
        parts = line.split('\t')
        assert parts[2] == ':'
        if parts[-1].startswith('Rest at:'):
            assert len(parts) >= 4
            continue
        if parts[3] == 'Key':
            assert len(parts) >= 8
            if parts[5] == 'UP':
                continue
            assert parts[5:7] == ['DOWN', 'at']
            # Fill response and RT in previous stimulus
            this_stimulus = stimuli[-1]
            key = parts[4]
            rt = int(parts[7]) - last_time
            this_stimulus[-2:] = [key, rt]
            continue
        assert parts[3] == 'Stim:'
        assert len(parts) >= 6
        stim_type = int(parts[4])
        stim_name = parts[5]
        # Joe only models to 1/10 of a second
        onset = exp_time(parts[0], start_time)
        stimuli.append([onset, stim_type, stim_name, 'NR', 'NR'])
        # For RT calculation above
        last_time = int(parts[0])

    return stimuli


def write_stimuli(stimuli, fname):
    lines = []
    for row in stimuli:
        onset, stim_type, stim_name, key, RT = row
        values = [onset, DURATION, BAD_LOOKUP[stim_type],
                  stim_name, stim_type, key, RT]
        lines.append(values)
    with Opener(fname, 'wt') as fobj:
        fobj.write('\t'.join(COL_NAMES) + '\n')
        for line in lines:
            fobj.write(COL_FMT_STR.format(*line))



def test_cogents():
    for in_fname, out_fname in (
        (pjoin('cogents', 'sub-01', 'oneback_1.log'),
         pjoin('tsvs', 'sub-01', 'func',
               'sub-01_task-onebacktask_run-01_events.tsv')),
        (pjoin('cogents', 'sub-01', 'oneback_2.log'),
         pjoin('tsvs', 'sub-01', 'func',
               'sub-01_task-onebacktask_run-02_events.tsv')),
        (pjoin('cogents', 'sub-02', 'oneback_1.log'),
         pjoin('tsvs', 'sub-02', 'func',
               'sub-02_task-onebacktask_run-01_events.tsv')),
        (pjoin('cogents', 'sub-02', 'oneback_2.log'),
         pjoin('tsvs', 'sub-02', 'func',
               'sub-02_task-onebacktask_run-02_events.tsv')),
        (pjoin('cogents', 'sub-03', 'oneback_2.log'),
         pjoin('tsvs', 'sub-03', 'func',
               'sub-03_task-onebacktask_run-02_events.tsv'))
    ):
        with open(out_fname, 'rt') as fobj:
            contents = fobj.read()
        stimuli = proc_cogent(in_fname)
        out = io.StringIO()
        write_stimuli(stimuli, out)
        assert out.getvalue() == contents
