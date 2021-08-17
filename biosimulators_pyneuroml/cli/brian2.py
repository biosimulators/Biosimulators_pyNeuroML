""" BioSimulators-compliant command-line interface to the `Brian 2 <https://briansimulator.org>`_ simulation program.

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-05-28
:Copyright: 2021, BioSimulators Team
:License: MIT
"""

from ..api import brian2 as api
from biosimulators_utils.simulator.cli import build_cli


def main(argv=None):
    """ Run the command-line interface to Brian 2

    Args:
        argv (:obj:`list` of :obj:`str`, optional): command-line arguments
    """
    App = build_cli('brian2', api.__version__,
                    'Brian 2', api.get_simulator_version(), 'https://briansimulator.org',
                    api.exec_sedml_docs_in_combine_archive)

    with App(argv=argv) as app:
        app.run()


if __name__ == "__main__":
    main()
