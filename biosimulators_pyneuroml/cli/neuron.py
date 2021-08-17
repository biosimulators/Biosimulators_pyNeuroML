""" BioSimulators-compliant command-line interface to the `NEURON <https://neuron.yale.edu>`_ simulation program.

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-05-28
:Copyright: 2021, BioSimulators Team
:License: MIT
"""

from ..api import neuron as api
from biosimulators_utils.simulator.cli import build_cli


def main(argv=None):
    """ Run the command-line interface to NEURON

    Args:
        argv (:obj:`list` of :obj:`str`, optional): command-line arguments
    """
    App = build_cli('neuron', api.__version__,
                    'NEURON', api.get_simulator_version(), 'https://neuron.yale.edu',
                    api.exec_sedml_docs_in_combine_archive)

    with App() as app:
        app.run()


if __name__ == "__main__":
    main()
