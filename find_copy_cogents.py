""" Script finds matches between raw and openfmri subjects
"""

import shutil
import os
from os.path import join as pjoin, isdir, basename
from glob import glob

import numpy as np

import nibabel as nib


def get_offsets(globber, offset_label):
    positions = {}
    offsets = set()
    for sub_dir in glob(globber):
        if not isdir(sub_dir):
            continue
        sub_id = basename(sub_dir)
        bolds = sorted(glob(pjoin(sub_dir, 'func', '*_bold.nii.gz')))
        assert len(bolds) == 2
        img = nib.load(bolds[0])
        offset = float(img.header['qoffset_' + offset_label])
        assert offset not in offsets
        offsets.add(offset)
        positions[sub_id] = offset
    return positions


direction = 'z'
positions = get_offsets('ds000107-download/sub-*', direction)
offsets = {value: key for key, value in positions.items()}

sub_dirs = glob('*')

matches = {}

for sub_dir in sub_dirs:
    bolds = sorted(glob(pjoin(sub_dir, 'oneback*.nii.gz')))
    if len(bolds) == 0:
        continue
    assert len(bolds) == 2
    for run_no, fname in enumerate(bolds):
        img = nib.load(fname)
        run_offset = float(img.header['qoffset_' + direction])
        for offset in offsets:
            if not np.isclose(offset, run_offset, atol=0.001):
                continue
            assert sub_dir not in matches
            matches[sub_dir] = offsets[offset]
            break
        else:
            continue
        break

rev_match = {value: key for key, value in matches.items()}
for key in sorted(rev_match):
    print(key, rev_match[key])


print('Missing', ', '.join(sorted(
    set(positions).difference(set(matches.values())))))

if isdir('cogents'):
    shutil.rmtree('cogents')
os.mkdir('cogents')

for orig_dir, of_dir in matches.items():
    out_dir = pjoin('cogents',  of_dir)
    os.mkdir(out_dir)
    for fname in glob(pjoin(orig_dir, '*.log')):
        parts = basename(fname).split('_')
        out_fname = pjoin(out_dir, '_'.join(parts[:2]) + '.log')
        shutil.copyfile(fname, out_fname)
