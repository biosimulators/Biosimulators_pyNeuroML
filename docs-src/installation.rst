Installation instructions
=========================

BioSimulators-pyNeuroML is available as three command-line programs and three command-line programs encapsulated into three Docker images.

Command-line program
--------------------

After installing `Python <https://www.python.org/downloads/>`_ (>= 3.7), `pip <https://pip.pypa.io/>`_, and `Java <https://java.com/>`_ run the following command to install BioSimulators-pyNeuroML:

.. code-block:: text

    pip install biosimulators-pyneuroml

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

    docker pull ghcr.io/biosimulators/netpyne
    docker pull ghcr.io/biosimulators/neuron
    docker pull ghcr.io/biosimulators/pyneuroml
