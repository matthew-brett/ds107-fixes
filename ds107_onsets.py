""" Utilties for writing ds107 3-column event files.

Run with something like:

    python ds107_onsets.py tsvs event_file_dir

where "tsv" is the path containing the subject directories, such as "sub-01",
"event_file_dir" is a directory in which to write the new .txt event files.

Try:

    python ds107_onsets.py --help

for more information.
"""

"""
See check_ds107_onsets.py for tests.
"""

from glob import glob
from os import mkdir
from os.path import join as pjoin, split as psplit, isdir, dirname, exists
from argparse import ArgumentParser

import numpy as np

import pandas as pd

from onftools import parse_tsv_name, tsv2events, three_column, write_tasks


# Where to look for condition files
NEW_COND_PATH=None
if isdir('tsv'):
    NEW_COND_PATH = pjoin(dirname(__file__), 'tsv')
elif isdir('sub-01'):
    NEW_COND_PATH = dirname(__file__)


# Correct task name / number mappings
GOOD_LOOKUP = {'words': 1,
               'objects': 3,
               'scrambled': 4,
               'consonant': 2}
INV_LOOKUP = {v: k for k, v in GOOD_LOOKUP.items()}


def oneback_preprocessor(df):
    """ Process dataframe for all trial types """
    trial_type = df['1'].apply(lambda v : INV_LOOKUP[v])
    amplitude = pd.Series(np.ones(len(df)))
    classified = pd.concat([trial_type, df['onset'], df['duration'],
                            amplitude], axis=1)
    classified.columns = ['trial_type', 'onset', 'duration', 'amplitude']
    return classified


TASK_DEFS = dict(
    onebacktask=dict(old_no=1,
                     preprocessor=oneback_preprocessor,
                     conditions=list(GOOD_LOOKUP),
                     ok = True,  # Set False to disable processing
                    ),
)

# Throw away incomplete TASK_DEFS (where field 'ok' is not True).
TASK_DEFS = {name: task_def for name, task_def in TASK_DEFS.items()
             if task_def.get('ok')}


def main():
    # Process the command-line arguments to the script.
    parser = ArgumentParser(description="Write event files for ds009")
    parser.add_argument('data_dir',
                        help='Directory containing subject directories')
    parser.add_argument('out_dir', default=None, nargs='?',
                        help='Directory in which to write event files '
                        '(default is to write to same directory as .tsv file)')
    parser.add_argument('task_name', default='all', nargs='*',
                        help='Name(s) of events to write (can have more than '
                        'one, separated by spaces)')
    args = parser.parse_args()
    # Create the output directory if it does not exist.
    if args.out_dir is not None and not exists(args.out_dir):
        mkdir(args.out_dir)
    # Write the files
    if 'all' in args.task_name:
        defs = TASK_DEFS
    else:
        defs = {k: v for k, v in TASK_DEFS.items() if k in args.task_name}
    write_tasks(args.data_dir, args.out_dir, defs)


if __name__ == '__main__':
    # This code gets run if this Python file gets executed as a script.
    # It does not get run if the file is just imported.
    # https://stackoverflow.com/a/419185
    main()
