Installation instructions
=========================

BioSimulators-pyNeuroML is available as four command-line programs and four command-line programs encapsulated into four Docker images.

Command-line program
--------------------

First, install `Python <https://www.python.org/downloads/>`_ (>= 3.7), `pip <https://pip.pypa.io/>`_, and `Java <https://java.com/>`_.

Second, install the following additional programs to use NetPyNe and NEURON:

* NEURON

    * gcc
    * g++
    * make

* NetPyNe
    
    * All of the above
    * mpi
    * libmpich-dev

Third, run the following command to install BioSimulators-pyNeuroML:

.. code-block:: text

    pip install biosimulators-pyneuroml

Add the ``brian2`` option to install support for Brian 2.

.. code-block:: text

    pip install biosimulators-pyneuroml[brian2]

Add the ``netpyne`` option to install support for NetPyNe.

.. code-block:: text

    pip install biosimulators-pyneuroml[netpyne]

Add the ``neuron`` option to install support for NEURON.

.. code-block:: text

    pip install biosimulators-pyneuroml[neuron]


Docker images with command-line entrypoints
-------------------------------------------

After installing `Docker <https://docs.docker.com/get-docker/>`_, run the following commands to install the Docker images for jNeuroML/pyNeuroML, NetPyNe, and NEURON:

.. code-block:: text

    docker pull ghcr.io/biosimulators/brian2
    docker pull ghcr.io/biosimulators/netpyne
    docker pull ghcr.io/biosimulators/neuron
    docker pull ghcr.io/biosimulators/pyneuroml
