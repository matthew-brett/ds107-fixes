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
See test_ds107_onsets.py for tests.
"""

from os import mkdir
from os.path import join as pjoin, dirname, isdir, exists
from argparse import ArgumentParser
from collections import OrderedDict

import numpy as np

import pandas as pd

from onftools import write_tasks


# Where to look for condition files
NEW_COND_PATH=None
if isdir('tsv'):
    NEW_COND_PATH = pjoin(dirname(__file__), 'tsv')
elif isdir('sub-01'):
    NEW_COND_PATH = dirname(__file__)


# Correct task name / number mappings
GOOD_LOOKUP = OrderedDict(words=1,
                          strings=2,
                          objects=3,
                          scrambled=4)
INV_LOOKUP = {v: k for k, v in GOOD_LOOKUP.items()}


def oneback_processor(df):
    """ Process dataframe for all trial types """
    trial_type = df['1'].map(INV_LOOKUP)
    amplitude = pd.Series(np.ones(len(df)))
    classified = pd.concat([trial_type, df['onset'], df['duration'],
                            amplitude], axis=1)
    classified.columns = ['trial_type', 'onset', 'duration', 'amplitude']
    return classified


TASK_DEFS = dict(
    onebacktask=dict(old_task_no=1,
                     processor=oneback_processor,
                     conditions=list(GOOD_LOOKUP),
                    ),
)


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
    # Main work done by write_tasks function in onftools
    write_tasks(args.data_dir, defs, args.out_dir)


if __name__ == '__main__':
    # This code gets run if this Python file gets executed as a script.
    # It does not get run if the file is just imported.
    # https://stackoverflow.com/a/419185
    main()
