""" BioSimulators-compliant command-line interface to the `pyNeuroML <https://github.com/NeuroML/pyNeuroML>`_ simulation program.

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-05-28
:Copyright: 2021, BioSimulators Team
:License: MIT
"""

from ..api import pyneuroml as api
from biosimulators_utils.simulator.cli import build_cli


def main(argv=None):
    """ Run the command-line interface to pyNeuroML

    Args:
        argv (:obj:`list` of :obj:`str`, optional): command-line arguments
    """
    App = build_cli('pyneuroml', api.__version__,
                    'pyNeuroML', api.get_simulator_version(), 'https://github.com/NeuroML/pyNeuroML',
                    api.exec_sedml_docs_in_combine_archive)

    with App(argv=argv) as app:
        app.run()


if __name__ == "__main__":
    main()
