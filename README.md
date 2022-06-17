# islatu

X-ray reflectometry reduction from Diamond Light Source

[![codecov](https://codecov.io/gh/RBrearton/islatu/branch/master/graph/badge.svg?token=FGIV0MVHS8)](https://codecov.io/gh/RBrearton/islatu)
[![Actions Status](https://github.com/RBrearton/islatu/workflows/pytest/badge.svg)](https://github.com/pytest/islatu/actions)
[![Documentation Status](https://readthedocs.org/projects/islatu/badge/?version=latest)](https://islatu.readthedocs.io/en/latest/?badge=latest)

### Install

This package can be easily installed using `pip install islatu`.

### Installation from source

To install in a fresh environment, first ensure that pip is available. For
example, using conda:

```
conda create --name islatu
conda activate islatu
conda install pip
```

Assuming that pip is available, installation of the library from source can be
done by cloning this repository. Navigate to its directory and use pip to
install this package and its dependencies as follows:

```
python -m pip install . -r requirements.txt
```

Make sure that your installation is functioning by running `pytest`.

### Documentation

To generate documentation, make sure you have sphinx installed on your system.
Go to the docs directory and run

```
make html
```
