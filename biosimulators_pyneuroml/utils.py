""" Utilities for pyNeuroML

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-06-02
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import Simulator, KISAO_ALGORITHM_MAP, RunLemsOptions, SEDML_TIME_OUTPUT_COLUMN_ID, SEDML_OUTPUT_FILE_ID
from biosimulators_utils.config import get_config
from biosimulators_utils.log.utils import StandardOutputErrorCapturer
from biosimulators_utils.sedml.data_model import ModelLanguage, UniformTimeCourseSimulation, Task, Variable, Symbol  # noqa: F401
from biosimulators_utils.sedml import validation
from biosimulators_utils.simulator.utils import get_algorithm_substitution_policy
from biosimulators_utils.utils.core import raise_errors_warnings
from kisao.utils import get_preferred_substitute_algorithm_by_ids
from pyneuroml import pynml
import lxml.etree
import os
import pandas
import psutil
import shutil
import tempfile

__all__ = [
    'validate_task',
    'set_sim_in_lems_xml',
    'run_lems_xml',
    'get_simulator_run_lems_method',
    'get_run_lems_options',
    'get_available_processors',
    'get_available_memory',
    'read_xml_file',
    'write_xml_file',
    'read_lems_output_files_configuration',
    'write_lems_output_files_configuration',
]


def validate_task(task, variables, simulator):
    """ Validate a task

    Args:
        task (:obj:`Task`): task
        variables (:obj:`list` of :obj:`Variable`): variables
        simulator (:obj:`Simulator`): simulator

    Returns:
        :obj:`str`: KiSAO id for a possibly alternative simulation algorithm
    """
    config = get_config()

    model = task.model
    sim = task.simulation

    if config.VALIDATE_SEDML:
        raise_errors_warnings(validation.validate_task(task),
                              error_summary='Task `{}` is invalid.'.format(task.id))
        raise_errors_warnings(validation.validate_model_language(task.model.language, ModelLanguage.LEMS),
                              error_summary='Language for model `{}` is not supported.'.format(model.id))
        raise_errors_warnings(validation.validate_model_change_types(task.model.changes, ()),
                              error_summary='Changes for model `{}` are not supported.'.format(model.id))
        raise_errors_warnings(*validation.validate_model_changes(task.model),
                              error_summary='Changes for model `{}` are invalid.'.format(model.id))
        raise_errors_warnings(validation.validate_simulation_type(sim, (UniformTimeCourseSimulation, )),
                              error_summary='{} `{}` is not supported.'.format(sim.__class__.__name__, sim.id))
        raise_errors_warnings(*validation.validate_simulation(sim),
                              error_summary='Simulation `{}` is invalid.'.format(sim.id))
        raise_errors_warnings(*validation.validate_data_generator_variables(variables),
                              error_summary='Data generator variables for task `{}` are invalid.'.format(task.id))

    if sim.initial_time != 0:
        raise NotImplementedError('Initial time must be 0, not {}'.format(sim.initial_time))

    number_of_steps = (
        sim.output_end_time - sim.initial_time
    ) / (
        sim.output_end_time - sim.output_start_time
    ) * sim.number_of_steps
    if abs(number_of_steps - int(number_of_steps)) > 1e-8:
        msg = (
            'Number of steps must be an integer, not `{}`'
            '\n  Initial time: {}'
            '\n  Output start time: {}'
            '\n  Output end time: {}'
            '\n  Number of steps: {}'
        ).format(number_of_steps, sim.initial_time, sim.output_start_time, sim.output_end_time, sim.number_of_steps)
        raise NotImplementedError(msg)

    simulator_kisao_alg_map = {kisao_id: alg_props for kisao_id,
                               alg_props in KISAO_ALGORITHM_MAP.items() if simulator in alg_props['simulators']}

    algorithm_substitution_policy = get_algorithm_substitution_policy()
    exec_kisao_id = get_preferred_substitute_algorithm_by_ids(
        sim.algorithm.kisao_id, simulator_kisao_alg_map.keys(),
        substitution_policy=algorithm_substitution_policy)

    if sim.algorithm.changes:
        raise NotImplementedError('Algorithm parameters are not supported.')

    for variable in variables:
        if variable.symbol and variable.symbol != Symbol.time.value:
            msg = 'Symbol `{} is not supported. Only the `{}` symbol is supported.'.format(
                variable.symbol, Symbol.time.value)
            raise NotImplementedError(msg)

    return exec_kisao_id


def set_sim_in_lems_xml(lems_xml_root, task, variables):
    """ Set the simulation in a LEMS document

    Args:
        lems_xml_root (:obj:`lxml.etree._Element`): LEMS document
        task (:obj:`Task`): task
        variables (:obj:`list` of :obj:`Variable`): variables to record
    """
    lems_xml = lems_xml_root.xpath('/Lems')
    if len(lems_xml) != 1:
        raise ValueError('LEMS documents must contain a single `Lems` root element.')
    lems_xml = lems_xml[0]

    # modify simulation
    simulation_xml = lems_xml.xpath('Simulation')
    if len(simulation_xml) == 0:
        raise ValueError('LEMS document must have a `Simulation` element.')
    elif len(simulation_xml) > 1:
        raise ValueError('LEMS document must have a single `Simulation` element, not {}.'.format(len(simulation_xml)))
    simulation_xml = simulation_xml[0]

    # add simulation
    model = task.model
    simulation = task.simulation

    simulation_xml.attrib['target'] = model.id
    simulation_xml.attrib['length'] = '{}s'.format(simulation.output_end_time)
    simulation_xml.attrib['step'] = '{}s'.format((simulation.output_end_time - simulation.output_start_time) / simulation.number_of_steps)

    # set simulation algorithm; Note: pyNeuroML seems to ignore this
    simulation_xml.attrib['method'] = KISAO_ALGORITHM_MAP[simulation.algorithm.kisao_id]['id']

    # remove existing outputs
    for output_file_xml in simulation_xml.xpath('OutputFile'):
        simulation_xml.remove(output_file_xml)

    # set outputs
    if variables:
        output_file_xml = lxml.etree.Element('OutputFile')
        output_file_xml.attrib['id'] = SEDML_OUTPUT_FILE_ID
        output_file_xml.attrib['fileName'] = SEDML_OUTPUT_FILE_ID + '.tsv'
        simulation_xml.append(output_file_xml)

        for variable in variables:
            if variable.target:
                output_column_xml = lxml.etree.Element('OutputColumn')
                output_column_xml.attrib['id'] = variable.id
                output_column_xml.attrib['quantity'] = variable.target
                output_file_xml.append(output_column_xml)


def run_lems_xml(lems_xml_root, working_dirname='.', lems_filename=None,
                 simulator=Simulator.pyneuroml, num_processors=None, max_memory=None, verbose=None):
    """Run a LEMS document with a simulator

    Args:
        lems_xml_root (:obj:`lxml.etree._Element`): LEMS document
        working_dirname (:obj:`str`, optional): working directory for the LEMS document
        lems_filename (:obj:`str`, optional): path to file for the LEMS document
        simulator (:obj:`Simulator`, optional): simulator to run the LEMS document
        num_processors (:obj:`int`, optional): number of processors to use (only used with NetPyNe)
        max_memory (:obj:`int`, optional): maximum memory to use in bytes
        verbose (:obj:`bool`, optional): whether to display extra information about simulation runs

    Returns:
        :obj:`dict` of :obj:`str` => :obj:`pandas.DataFrame`: dictionary that maps the id of each output file
            to a Pandas data frame with its value
    """
    run_lems_method = get_simulator_run_lems_method(simulator)
    options = get_run_lems_options(num_processors=num_processors, max_memory=max_memory, verbose=verbose)

    # get outputs of LEMS document
    output_file_configs = read_lems_output_files_configuration(lems_xml_root)

    # config locations for outputs
    for i_output_file, output_file_config in enumerate(output_file_configs):
        output_file_config['file_name'] = str(i_output_file) + '.tsv'

    # create a new LEMS document with outputs directed to temporary files
    write_lems_output_files_configuration(lems_xml_root, output_file_configs)

    fid, temp_filename = tempfile.mkstemp(dir=working_dirname, suffix='.xml')
    os.close(fid)
    write_xml_file(lems_xml_root, temp_filename)

    results_dirname = tempfile.mkdtemp()
    options.exec_in_dir = results_dirname
    with StandardOutputErrorCapturer(relay=options.verbose) as captured:
        result = run_lems_method(temp_filename, **options.to_kw_args(simulator))
        if not result:
            os.remove(temp_filename)
            shutil.rmtree(results_dirname)

            msg = '`{}` was not able to execute {}:\n\n  {}'.format(
                simulator.value,
                '`{}`'.format(lems_filename) if lems_filename else 'the LEMS document',
                captured.get_text().replace('\n', '\n  '))
            raise RuntimeError(msg)

    # read results
    results = read_lems_output_files(output_file_configs, results_dirname)

    # cleanup temporary files
    os.remove(temp_filename)
    shutil.rmtree(results_dirname)

    # return results
    return results


def get_simulator_run_lems_method(simulator):
    """Get the LEMS run method for a simulator

    Args:
        simulator (:obj:`Simulator`): simulator to run the LEMS document

    Returns:
        :obj:`types.FunctionType`: run LEMS method
    """
    if simulator == Simulator.brian2:
        return pynml.run_lems_with_jneuroml_brian2

    elif simulator == Simulator.pyneuroml:
        return pynml.run_lems_with_jneuroml

    elif simulator == Simulator.netpyne:
        return pynml.run_lems_with_jneuroml_netpyne

    elif simulator == Simulator.neuron:
        return pynml.run_lems_with_jneuroml_neuron

    else:
        raise NotImplementedError('`{}` is not a supported simulator.'.format(simulator))


def get_run_lems_options(num_processors=None, max_memory=None, verbose=None):
    """ Get options for running a LEMS document

    Args:
        num_processors (:obj:`int`, optional): number of processors to use (only used with NetPyNe)
        max_memory (:obj:`int`, optional): maximum memory to use in bytes
        verbose (:obj:`bool`, optional): whether to display extra information about simulation runs

    Returns:
        :obj:`RunLemsOptions`: options
    """
    if num_processors is None:
        num_processors = max(1, get_available_processors() - 1)

    if max_memory is None:
        max_memory = get_available_memory() - 100 * 1000000

    if verbose is None:
        verbose = get_config().VERBOSE

    options = RunLemsOptions(num_processors=num_processors, max_memory=max_memory, verbose=verbose)

    return options


def get_available_processors():
    """ Get the amount of processors available

    Returns:
        :obj:`int`: amount of processors available
    """
    return os.cpu_count()


def get_available_memory():
    """ Get the amount of memory available

    Returns:
        :obj:`int`: amount of memory available in bytes
    """
    vmem = psutil.virtual_memory()
    return vmem.available


def read_xml_file(filename, remove_blank_text=True):
    """ Read an XML file

    Args:
        filename (:obj:`str`): path to an XML file
        remove_blank_text (:obj:`bool`, optional): whether to remove
            formatting so that the file could be exported pretty-printed

    Returns:
        :obj:`lxml.etree._Element`: root element for the XML file
    """
    parser = lxml.etree.XMLParser(remove_blank_text=remove_blank_text)
    return lxml.etree.parse(filename, parser).getroot()


def write_xml_file(root, filename, pretty_print=True):
    """ Write an XML file

    Args:
        root ( :obj:`lxml.etree._Element`): root element for the XML file
        filename (:obj:`str`): path to an XML file
        pretty_print (:obj:`bool`, optional): whether to pretty-print the file (required for NeuroML)
    """
    etree = lxml.etree.ElementTree(root)
    etree.write(filename, pretty_print=pretty_print)


def read_lems_output_files_configuration(xml_root):
    """ Read the configuration of the output files of a LEMS document

    Args:
        xml_root (:obj:`lxml.etree._Element`): LEMS document

    Returns:
        :obj:`list` of :obj:`dict`: configuration of the output files of a LEMS document
    """
    output_file_configs = []
    for sim_xml in xml_root.xpath('/Lems/Simulation'):
        for output_file_xml in sim_xml.xpath('OutputFile'):
            output_file_config = {
                'sim_id': sim_xml.attrib['id'],
                'id': output_file_xml.attrib['id'],
                'file_name': output_file_xml.attrib['fileName'],
                'columns': []
            }
            output_file_configs.append(output_file_config)

            for column_xml in output_file_xml.xpath('OutputColumn'):
                output_file_config['columns'].append({
                    'id': column_xml.attrib['id'],
                    'quantity': column_xml.attrib['quantity'],
                })

    return output_file_configs


def write_lems_output_files_configuration(xml_root, output_file_configs):
    """ Read the configuration of the output files of a LEMS document

    Args:
        xml_root (:obj:`lxml.etree._Element`): LEMS document
        output_file_configs (:obj:`list` of :obj:`dict`): configuration of the output files of a LEMS document
    """
    for sim_xml in xml_root.xpath('/Lems/Simulation'):
        for output_file_xml in sim_xml.xpath('OutputFile'):
            sim_xml.remove(output_file_xml)

        for output_file_config in output_file_configs:
            if output_file_config['sim_id'] == sim_xml.attrib['id']:
                output_file_xml = lxml.etree.Element('OutputFile')
                output_file_xml.attrib['id'] = output_file_config['id']
                output_file_xml.attrib['fileName'] = output_file_config['file_name']
                sim_xml.append(output_file_xml)

                for column in output_file_config['columns']:
                    column_xml = lxml.etree.Element('OutputColumn')
                    column_xml.attrib['id'] = column['id']
                    column_xml.attrib['quantity'] = column['quantity']
                    output_file_xml.append(column_xml)


def read_lems_output_files(output_file_configs, output_files_dirname='.'):
    """ Read the output files of the execution of a LEMS document

    Args:
        output_file_configs (:obj:`list` of :obj:`dict`): configuration of the output files of a LEMS document
        output_files_dirname (:obj:`str`, optional): base directory for output files

    Returns:
        :obj:`dict` of :obj:`str` => :obj:`pandas.DataFrame`: dictionary that maps the id of each output file
            to a Pandas data frame with its value
    """
    results = {}
    for output_file_config in output_file_configs:
        column_ids = [SEDML_TIME_OUTPUT_COLUMN_ID] + [column['id'] for column in output_file_config['columns']] + ['__extra__']
        results[output_file_config['id']] = pandas.read_csv(
            os.path.join(output_files_dirname, output_file_config['file_name']),
            sep='\t', names=column_ids).drop(columns=['__extra__'])
    return results
