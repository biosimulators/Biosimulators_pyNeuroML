Tutorial
========

BioSimulators-pyNeuroML is available as three command-line programs and as a command-line programs encapsulated into three Docker images.


Creating COMBINE/OMEX archives and encoding simulation experiments into SED-ML
------------------------------------------------------------------------------

Information about how to create COMBINE/OMEX archives which can be executed by BioSimulators-pyNeuroML is available at `BioSimulators <https://biosimulators.org/help>`_.

A list of the algorithms and algorithm parameters supported by jNeuroML/pyNeuroML, NetPyNe, and NEURON is available at `BioSimulators <https://biosimulators.org/simulators/>`_.


Command-line program
--------------------

The command-line programs can be used to execute COMBINE/OMEX archives that describe simulations as illustrated below.

.. code-block:: text

    usage: biosimulators-pyneuroml [-h] [-d] [-q] -i ARCHIVE [-o OUT_DIR] [-v]

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

For example, the following commands could be used to execute the simulations described in ``./modeling-study.omex`` and save their results to ``./``:

.. code-block:: text

    biosimulators-netpyne -i ./modeling-study.omex -o ./
    biosimulators-neuron -i ./modeling-study.omex -o ./
    biosimulators-pyneuroml -i ./modeling-study.omex -o ./


Docker images with command-line entrypoints
-------------------------------------------

The entrypoints to the Docker images support the same command-line interface described above.

For example, the following command could be used to use the jNeuroML/pyNeuroML Docker image to execute the same simulations described in ``./modeling-study.omex`` and save their results to ``./``:

.. code-block:: text

    docker run \
        --tty \
        --rm \
        --mount type=bind,source="$(pwd),target=/tmp/working-dir \
        ghcr.io/biosimulators/pyneuroml:latest \
            -i /tmp/working-dir/modeling-study.omex \
            -o /tmp/working-dir
