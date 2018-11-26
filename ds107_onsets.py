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
See check_ds009_onsets.py for tests.
"""

from glob import glob
from os import mkdir
from os.path import join as pjoin, split as psplit, isdir, dirname, exists
from argparse import ArgumentParser

import numpy as np

import pandas as pd


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


def parse_tsv_name(tsv_path):
    """ Parse tsv file name, return subject no, task name, run_no

    Parameters
    ----------
    tsv_path : str
        .tsv filename.

    Returns
    -------
    subject_no : str
        E.g. "sub-12"
    task_name : str
        E.g. "stopsignal"
    run_no : None or int
        None if no run number specified, otherwise a 1-based integer giving the
        run number, where 1 is the first run.
    """
    path, fname = psplit(tsv_path)
    parts = fname.split('_')
    if len(parts) == 3:
        run_no = None
    else:
        run_parts = parts.pop(2).split('-')
        assert run_parts[0] == 'run'
        run_no = int(run_parts[1])
    sub_parts = parts[0].split('-')
    assert sub_parts[0] == 'sub'
    sub_no = int(sub_parts[1])
    task_name = parts[1].split('-')[1]
    return sub_no, task_name, run_no


def three_column(df, name):
    """ Return 3-column onset, duration, amplitude data frame for event `name`
    """
    ons_dur_amp = df[df['trial_type'] == name]
    return ons_dur_amp[['onset', 'duration', 'amplitude']].values


def tsv2events(tsv_path):
    """ Return dictionary of 3-column event dataframes from `tsv_path`
    """
    sub_no, task_name, run_no = parse_tsv_name(tsv_path)
    if task_name not in TASK_DEFS:  # Task not properly defined
        return {}
    info = TASK_DEFS[task_name]
    df = pd.read_table(tsv_path)
    if info['preprocessor']:
        df = info['preprocessor'](df)
    return {name: three_column(df, name) for name in info['conditions']}


def write_task(tsv_path, out_path=None):
    """ Write .txt event files for .tsv event definitions

    Parameters
    ----------
    tsv_path : str
        Path to .tsv file.
    out_path : None or str
        If str, directory to write output .txt files.  If None, use directory
        containing the .tsv file in `tsv_path`.
    """
    sub_no, task_name, run_no = parse_tsv_name(tsv_path)
    events = tsv2events(tsv_path)
    if len(events) == 0:
        return
    tsv_dir, fname = psplit(tsv_path)
    path = tsv_dir if out_path is None else out_path
    run_part = '' if run_no is None else '_run-%02d' % run_no
    fname_prefix = pjoin(
        path,
        'sub-%02d_task-%s%s_label-' % (sub_no, task_name, run_part))
    for name in events:
        new_fname = fname_prefix + name + '.txt'
        oda = events[name]
        if len(oda):
            print('Writing from', tsv_path, 'to', new_fname)
            np.savetxt(new_fname, oda, '%f', '\t')


def write_all_tasks(start_path, out_path=None, event_names='all'):
    """ Write .txt event files for all tasks with defined processing.

    Parameters
    ----------
    start_path : str
        Path containing subject directories such as ``sub-01`` etc.
    out_path : None or str, optional
        If str, directory to write output .txt files.  If None, use directory
        containing the .tsv file, found by searching in `start_path`.
    event_names : list or "all", optional
        List of event names to process.  If string "all", process all known
        event names.
    """
    event_names = list(TASK_DEFS) if event_names == 'all' else event_names
    strange_events = set(event_names).difference(TASK_DEFS)
    if len(strange_events):
        raise ValueError("One or more event names without processors: " +
                           ', '.join(strange_events))
    globber = pjoin(start_path, 'sub-*', 'func', 'sub*tsv')
    matches = glob(globber)
    if len(matches) == 0:
        raise ValueError(f'No matches for glob "{globber}"')
    for tsv_path in matches:
        sub_no, task_name, run_no = parse_tsv_name(tsv_path)
        if task_name in event_names:
            write_task(tsv_path, out_path)


def main():
    # Process the command-line arguments to the script.
    parser = ArgumentParser(description="Write event files for ds009")
    parser.add_argument('data_dir',
                        help='Directory containing subject directories')
    parser.add_argument('out_dir', default=None, nargs='?',
                        help='Directory in which to write event files '
                        '(default is to write to same directory as .tsv file)')
    parser.add_argument('event_name', default='all', nargs='*',
                        help='Name(s) of events to write (can have more than '
                        'one, separated by spaces)')
    args = parser.parse_args()
    # Create the output directory if it does not exist.
    if args.out_dir is not None and not exists(args.out_dir):
        mkdir(args.out_dir)
    # Write the files
    write_all_tasks(args.data_dir, args.out_dir, args.event_name)


if __name__ == '__main__':
    # This code gets run if this Python file gets executed as a script.
    # It does not get run if the file is just imported.
    # https://stackoverflow.com/a/419185
    main()
