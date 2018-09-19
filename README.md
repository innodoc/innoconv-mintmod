[![build status](https://gitlab.tubit.tu-berlin.de/innodoc/innoconv-mintmod/badges/master/build.svg)](https://gitlab.tubit.tu-berlin.de/innodoc/innoconv-mintmod/commits/master) [![coverage report](https://gitlab.tubit.tu-berlin.de/innodoc/innoconv-mintmod/badges/master/coverage.svg)](https://gitlab.tubit.tu-berlin.de/innodoc/innoconv-mintmod/commits/master) [![Documentation Status](https://readthedocs.org/projects/innoconv-for-mintmod/badge/?version=latest)](https://innoconv-for-mintmod.readthedocs.io/en/latest/?badge=latest)

# innoConv (for mintmod)

Converter for interactive educational content.

**This program converts mintmod source.**

**If you don't know what mintmod is you probably don't need it.**

## Quick installation

It is recommended to install innoConv in a [virtual environment](https://docs.python.org/3/library/venv.html).

```sh
# Create a virtual environment in a place of your choice
$ python3 -m venv /path/to/virtual/environment
# Activate venv
$ source /path/to/virtual/environment/bin/activate
# Install using pip
$ pip install --process-dependency-links -e git+https://gitlab.tubit.tu-berlin.de/innodoc/innoconv-mintmod.git#egg=innoconv-mintmod
```

The ``innoconv-mintmod`` command is now available.

## Documentation

You can read it up online or [build it yourself](#generate-documentation).

- [HTML](https://innoconv-for-mintmod.readthedocs.io/en/latest/index.html)
- [PDF](https://media.readthedocs.org/pdf/innoconv-for-mintmod/latest/innoconv-for-mintmod.pdf)

## Development

### Setup environment

```sh
$ python3 -m venv venv
$ . venv/bin/activate
$ pip install -r requirements.txt
$ ./setup.py develop
```

### Commands

#### Build tub_base

##### JSON

Get the content source code and convert it to JSON.

```sh
$ git clone -b innoconv git@gitlab.tubit.tu-berlin.de:innodoc/tub_base
$ innoconv-mintmod tub_base
```

##### HTML (for debugging/development)

```
$ innoconv-mintmod -d tub_base
```

#### Linting

Adhere to [PEP8](https://www.python.org/dev/peps/pep-0008/). Before pushing code please run lint and fix **all** problems.

```sh
$ ./setup.py lint
```

#### Tests

```sh
$ ./setup.py test
```

#### Build HTML coverage report

Do this after calling `./setup.py test`.

```sh
$ ./setup.py coverage
```

#### Generate documentation

```sh
$ ./setup.py build_doc
```

You can find the documentation in `build/sphinx`.
