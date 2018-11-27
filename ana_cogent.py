""" Process Cogent file to generate OpenFMRI .tsv equivalent
"""

import re
import io
from os.path import join as pjoin
from itertools import product
from contextlib import contextmanager


@contextmanager
def null_cm(obj):
    yield obj


def check_mode(obj, mode):
    if 'a' in mode:
        return hasattr(obj, 'read') and hasattr(obj, 'write')
    if 'w' in mode:
        return hasattr(obj, 'write')
    return hasattr(obj, 'read')


def opened(obj, mode):
    return null_cm(obj) if check_mode(obj, mode) else open(obj, mode)


timing_re = re.compile(r'\d+\t\[\d+\]')

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
    with opened(fname, 'rt') as fobj:
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
    last_stim_time = None
    for line in lines[i + 2:-1]:
        assert timing_re.match(line)
        parts = line.split('\t')
        assert parts[2] == ':'
        if parts[-1].startswith('Rest at:'):
            assert len(parts) >= 4
            last_stim_time = None
            continue
        if parts[3] == 'Key':
            assert len(parts) >= 8
            if parts[5] == 'UP':
                continue
            assert parts[5:7] == ['DOWN', 'at']
            if last_stim_time is None:
                continue
            # Fill response and RT in previous stimulus
            this_stimulus = stimuli[-1]
            key = parts[4]
            rt = int(parts[7]) - last_stim_time
            this_stimulus[-2:] = [key, rt]
            last_stim_time = None
            continue
        assert parts[3] == 'Stim:'
        assert len(parts) >= 6
        stim_type = int(parts[4])
        stim_name = parts[5]
        # Joe only models to 1/10 of a second
        onset = exp_time(parts[0], start_time)
        stimuli.append([onset, stim_type, stim_name, 'NR', 'NR'])
        # For RT calculation above
        last_stim_time = int(parts[0])

    return stimuli


def write_stimuli(stimuli, fname):
    lines = []
    for row in stimuli:
        onset, stim_type, stim_name, key, RT = row
        values = [onset, DURATION, BAD_LOOKUP[stim_type],
                  stim_name, stim_type, key, RT]
        lines.append(values)
    with opened(fname, 'wt') as fobj:
        fobj.write('\t'.join(COL_NAMES) + '\n')
        for line in lines:
            fobj.write(COL_FMT_STR.format(*line))



def test_cogents():
    # Check analysis gives same answers as original TSV files.
    for sub_no, run_no in product(range(1, 50), [1, 2]):
        if sub_no == 25:
            continue
        if (sub_no, run_no) == (41, 2):
            continue
        sub_str = f'sub-{sub_no:02d}'
        in_fname = pjoin('cogents', sub_str, f'oneback_{run_no}.log')
        out_fname = pjoin(
            'tsvs', sub_str, 'func',
            f'{sub_str}_task-onebacktask_run-{run_no:02d}_events.tsv')
        with open(out_fname, 'rt') as fobj:
            contents = fobj.read()
        stimuli = proc_cogent(in_fname)
        out = io.StringIO()
        write_stimuli(stimuli, out)
        assert out.getvalue() == contents
