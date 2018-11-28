# Processing for ds107 dataset

This repository has various fragments for processing the raw data of the
[ds107 dataset](https://openneuro.org/datasets/ds000107).

The *raw data* is the data processed by the research team, to generate the
public ds107.  Many thanks to Professor Joe Devlin for searching out that data,
and having a filing system good enough to get the data back from an experiment
that is more than 10 years old.

The fragments are:

* `find_copy_cogents.py` - uses the functional image affine matrices to match
  the subjects in the raw data archive with the subjects in `ds107`, then
  copies their [Cogent](http://www.vislab.ucl.ac.uk/cogent.php) experiment logs
  to a directory structure matching `ds107`.  I committed the results in the
  `cogents` directory.
* `ana_cogent.py` - reconstruct the analysis of the Cogent log files to
  regenerate the `.tsv` task files corresponding to the data in the `ds107`
  dataset.  Test the results are the same for the good subjects.  In fact, only
  subject 43 of `ds107` had errors in this process, due to the presence of two
  experimental runs in the subject 43 Cogent logs.  This is fixed in the
  current `cogent` directory - track the changes to those files to see the
  originals.
* `fix43.py` regenerates the subject 43 `.tsv` files.
* `ds107_onsets.py` generates the 3-column event files for the four conditions,
  from the `.tsv` files.
* `test_ds107_onsets.py` tests `ds107_onsets.py`, and checks the results
  against the original OpenFMRI files giving the `ds107` experimental paradigm.
