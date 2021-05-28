""" BioSimulators-compliant command-line interface to the `pyNeuroML <https://github.com/NeuroML/pyNeuroML>`_ simulation program.

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-05-28
:Copyright: 2021, BioSimulators Team
:License: MIT
"""

from ._version import __version__
from .core import exec_sedml_docs_in_combine_archive
from biosimulators_utils.simulator.cli import build_cli
import pyneuroml

App = build_cli('pyneuroml', __version__,
                'pyNeuroML', pyneuroml.__version__, 'https://github.com/NeuroML/pyNeuroML',
                exec_sedml_docs_in_combine_archive)


def main():
    with App() as app:
        app.run()
