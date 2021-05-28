[![Latest release](https://img.shields.io/github/v/tag/biosimulators/Biosimulators_pyNeuroML)](https://github.com/biosimulations/Biosimulators_pyNeuroML/releases)
[![PyPI](https://img.shields.io/pypi/v/biosimulators_pyneuroml)](https://pypi.org/project/biosimulators_pyneuroml/)
[![CI status](https://github.com/biosimulators/Biosimulators_pyNeuroML/workflows/Continuous%20integration/badge.svg)](https://github.com/biosimulators/Biosimulators_pyNeuroML/actions?query=workflow%3A%22Continuous+integration%22)
[![Test coverage](https://codecov.io/gh/biosimulators/Biosimulators_pyNeuroML/branch/dev/graph/badge.svg)](https://codecov.io/gh/biosimulators/Biosimulators_pyNeuroML)

# BioSimulators-pyNeuroML
BioSimulators-compliant command-line interface and Docker image for the [pyNeuroML](https://github.com/NeuroML/pyNeuroML) simulation program.

This command-line interface and Docker image enable users to use pyNeuroML to execute [COMBINE/OMEX archives](https://combinearchive.org/) that describe one or more simulation experiments (in [SED-ML format](https://sed-ml.org)) of one or more models (in [NeuroML format](https://neuroml.org/])).

A list of the algorithms and algorithm parameters supported by pyNeuroML is available at [BioSimulators](https://biosimulators.org/simulators/pyneuroml).

A simple web application and web service for using pyNeuroML to execute COMBINE/OMEX archives is also available at [runBioSimulations](https://run.biosimulations.org).

## Installation

### Install Python package

1. Install Java
2. Install this package
   ```
   pip install biosimulators-pyneuroml
   ```

### Install Docker image
```
docker pull ghcr.io/biosimulators/pyneuroml
```

## Usage

### Local usage
```
usage: pyneuroml [-h] [-d] [-q] -i ARCHIVE [-o OUT_DIR] [-v]

BioSimulators-compliant command-line interface to the pyNeuroML <https://github.com/NeuroML/pyNeuroML> simulation program.

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           full application debug mode
  -q, --quiet           suppress all console output
  -i ARCHIVE, --archive ARCHIVE
                        Path to OMEX file which contains one or more SED-ML-
                        encoded simulation experiments
  -o OUT_DIR, --out-dir OUT_DIR
                        Directory to save outputs
  -v, --version         show program's version number and exit
```

### Usage through Docker container
The entrypoint to the Docker image supports the same command-line interface described above.

For example, the following command could be used to use the Docker image to execute the COMBINE/OMEX archive `./modeling-study.omex` and save its outputs to `./`.

```
docker run \
  --tty \
  --rm \
  --mount type=bind,source="$(pwd)",target=/root/in,readonly \
  --mount type=bind,source="$(pwd)",target=/root/out \
  ghcr.io/biosimulators/pyneuroml:latest \
    -i /root/in/modeling-study.omex \
    -o /root/out
```

## Documentation
Documentation is available at https://biosimulators.github.io/Biosimulators_pyNeuroML/.

## License
This package is released under the [MIT](LICENSE).

## Development team
This package was developed by the [Karr Lab](https://www.karrlab.org) at the Icahn School of Medicine at Mount Sinai and the [Center for Reproducible Biomedical Modeling](https://reproduciblebiomodels.org/).

## Questions and comments
Please contact the [BioSimulators Team](mailto:info@biosimulators.org) with any questions or comments.
