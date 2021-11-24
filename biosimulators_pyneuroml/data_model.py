""" Data model for pyNeuroML algorithms and their parameters

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-06-02
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import collections
import enum

__all__ = [
    'Simulator',
    'SIMULATOR_ENABLED',
    'KISAO_ALGORITHM_MAP',
    'RunLemsOptions',
    'SEDML_TIME_OUTPUT_COLUMN_ID',
    'SEDML_OUTPUT_FILE_ID',
]


class Simulator(str, enum.Enum):
    """ A LEMS simulator """
    brian2 = 'Brian2'
    neuron = 'NEURON'
    netpyne = 'NetPyNe'
    pyneuroml = 'pyNeuroML'


SIMULATOR_ENABLED = {
    Simulator.brian2: True,
    Simulator.neuron: True,
    Simulator.netpyne: True,
    Simulator.pyneuroml: True,
}


KISAO_ALGORITHM_MAP = collections.OrderedDict([
    ('KISAO_0000019', {
        'kisao_id': 'KISAO_0000019',
        'id': 'cvode',
        'name': 'CVODE',
        'parameters': {
        },
        'simulators': [
            Simulator.neuron,
            Simulator.netpyne,
        ],
    }),
    ('KISAO_0000030', {
        'kisao_id': 'KISAO_0000030',
        'id': 'eulerTree',
        'name': 'Euler forward method',
        'parameters': {
        },
        'simulators': [
            Simulator.brian2,
            Simulator.pyneuroml,
        ],
    }),
    ('KISAO_0000032', {
        'kisao_id': 'KISAO_0000032',
        'id': 'rk4',
        'name': '4th order Runge-kutta method',
        'parameters': {
        },
        'simulators': [
            Simulator.brian2,
            Simulator.pyneuroml,
        ],
    }),
    ('KISAO_0000381', {
        'kisao_id': 'KISAO_0000381',
        'id': 'rk2',
        'name': '2nd order Runge-kutta method',
        'parameters': {
        },
        'simulators': [
            Simulator.brian2,
        ],
    }),
])


class RunLemsOptions(object):
    """ Options for running a LEMS file

    Attributes:
        paths_to_include (:obj:`list` of :obj:`str`)
        num_processors (:obj:`int`)
        max_memory (:obj:`int`): maximum memory in bytes
        skip_run (:obj:`bool`)
        no_gui (:obj:`bool`)
        load_saved_data (:obj:`bool`)
        reload_events (:obj:`bool`)
        plot (:obj:`bool`)
        show_plot_already (:obj:`bool`)
        exec_in_dir (:obj:`str`)
        verbose (:obj:`bool`)
        exit_on_fail (:obj:`bool`)
        cleanup (:obj:`bool`)
        only_generate_scripts (:obj:`bool`)
        compile_mods (:obj:`bool`)
        realtime_output (:obj:`bool`)
    """

    def __init__(self,
                 paths_to_include=None,
                 num_processors=None,
                 max_memory=None,
                 skip_run=False,
                 no_gui=True,
                 load_saved_data=False,
                 reload_events=False,
                 plot=False,
                 show_plot_already=False,
                 exec_in_dir='.',
                 verbose=False,
                 exit_on_fail=False,
                 cleanup=True,
                 only_generate_scripts=False,
                 compile_mods=True,
                 realtime_output=False,
                 ):
        """
        Args:
            paths_to_include (:obj:`list` of :obj:`str`, optional)
            num_processors (:obj:`int`, optional)
            max_memory (:obj:`int`, optional): maximum memory in bytes
            skip_run (:obj:`bool`, optional)
            no_gui (:obj:`bool`, optional)
            load_saved_data (:obj:`bool`, optional)
            reload_events (:obj:`bool`, optional)
            plot (:obj:`bool`, optional)
            show_plot_already (:obj:`bool`, optional)
            exec_in_dir (:obj:`str`, optional)
            verbose (:obj:`bool`, optional)
            exit_on_fail (:obj:`bool`, optional)
            cleanup (:obj:`bool`, optional)
            only_generate_scripts (:obj:`bool`, optional)
            compile_mods (:obj:`bool`, optional)
            realtime_output (:obj:`bool`, optional)
        """
        self.paths_to_include = paths_to_include or []
        self.num_processors = num_processors
        self.max_memory = max_memory
        self.skip_run = skip_run
        self.no_gui = no_gui
        self.load_saved_data = load_saved_data
        self.reload_events = reload_events
        self.plot = plot
        self.show_plot_already = show_plot_already
        self.exec_in_dir = exec_in_dir
        self.verbose = verbose
        self.exit_on_fail = exit_on_fail
        self.cleanup = cleanup
        self.only_generate_scripts = only_generate_scripts
        self.compile_mods = compile_mods
        self.realtime_output = realtime_output

    def to_kw_args(self, simulator):
        """ Format options as keyword arguments for a LEMS run method

        Args:
            simulator (:obj:`Simulator`): simulator

        Returns:
            :obj:`dict`: keyword arguments for a LEMS run method
        """
        options = {
            'paths_to_include': self.paths_to_include,
            'max_memory': str(int(self.max_memory / 1e6)) + 'M',
            'skip_run': self.skip_run,
            'nogui': self.no_gui,
            'reload_events': self.reload_events,
            'plot': self.plot,
            'show_plot_already': self.show_plot_already,
            'exec_in_dir': self.exec_in_dir,
            'verbose': self.verbose,
            'exit_on_fail': self.exit_on_fail,
            'cleanup': self.cleanup,
        }

        if simulator == Simulator.netpyne:
            options['num_processors'] = self.num_processors
            options['only_generate_scripts'] = self.only_generate_scripts

        elif simulator == Simulator.neuron:
            options['only_generate_scripts'] = self.only_generate_scripts
            options['compile_mods'] = self.compile_mods
            options['realtime_output'] = self.realtime_output

        return options


SEDML_TIME_OUTPUT_COLUMN_ID = '__time__'
SEDML_OUTPUT_FILE_ID = '__output_file__'
