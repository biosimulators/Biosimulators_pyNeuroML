""" BioSimulators-compliant command-line interface to the `NetPyNe <http://netpyne.org>`_ simulation program.

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-05-28
:Copyright: 2021, BioSimulators Team
:License: MIT
"""

from ..api import netpyne as api
from biosimulators_utils.simulator.cli import build_cli


def main(argv=None):
    """ Run the command-line interface to NetPyNe

    Args:
        argv (:obj:`list` of :obj:`str`, optional): command-line arguments
    """
    App = build_cli('netpyne', api.__version__,
                    'NetPyNe', api.get_simulator_version(), 'http://netpyne.org',
                    api.exec_sedml_docs_in_combine_archive)

    with App(argv=argv) as app:
        app.run()


if __name__ == "__main__":
    main()
