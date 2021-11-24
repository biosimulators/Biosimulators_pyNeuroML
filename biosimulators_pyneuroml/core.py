""" Methods for using pyNeuroML to execute SED tasks in COMBINE archives and save their outputs

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-05-28
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import Simulator, KISAO_ALGORITHM_MAP, SEDML_TIME_OUTPUT_COLUMN_ID, SEDML_OUTPUT_FILE_ID
from .utils import validate_task, read_xml_file, set_sim_in_lems_xml, run_lems_xml, get_simulator_run_lems_method, validate_lems_document
from biosimulators_utils.combine.exec import exec_sedml_docs_in_archive
from biosimulators_utils.config import get_config, Config  # noqa: F401
from biosimulators_utils.log.data_model import CombineArchiveLog, TaskLog, StandardOutputErrorCapturerLevel  # noqa: F401
from biosimulators_utils.viz.data_model import VizFormat  # noqa: F401
from biosimulators_utils.report.data_model import ReportFormat, VariableResults, SedDocumentResults  # noqa: F401
from biosimulators_utils.sedml import validation
from biosimulators_utils.sedml.data_model import (Task, ModelAttributeChange, UniformTimeCourseSimulation,  # noqa: F401
                                                  Variable, Symbol)
from biosimulators_utils.sedml.exec import exec_sed_doc as base_exec_sed_doc
from biosimulators_utils.sedml.utils import apply_changes_to_xml_model
from biosimulators_utils.utils.core import raise_errors_warnings
import copy
import functools
import os

__all__ = [
    'exec_sedml_docs_in_combine_archive', 'exec_sed_doc', 'exec_sed_task', 'preprocess_sed_task',
]


def exec_sedml_docs_in_combine_archive(archive_filename, out_dir,
                                       config=None,
                                       simulator=Simulator.pyneuroml):
    """ Execute the SED tasks defined in a COMBINE/OMEX archive and save the outputs

    Args:
        archive_filename (:obj:`str`): path to COMBINE/OMEX archive
        out_dir (:obj:`str`): path to store the outputs of the archive

            * CSV: directory in which to save outputs to files
              ``{ out_dir }/{ relative-path-to-SED-ML-file-within-archive }/{ report.id }.csv``
            * HDF5: directory in which to save a single HDF5 file (``{ out_dir }/reports.h5``),
              with reports at keys ``{ relative-path-to-SED-ML-file-within-archive }/{ report.id }`` within the HDF5 file

        simulator (:obj:`Simulator`, optional): simulator
        config (:obj:`Config`, optional): BioSimulators common configuration

    Returns:
        :obj:`tuple`:

            * :obj:`SedDocumentResults`: results
            * :obj:`CombineArchiveLog`: log
    """
    sed_doc_executer = functools.partial(exec_sed_doc, simulator=simulator)
    return exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, out_dir,
                                      apply_xml_model_changes=True,
                                      config=config)


def exec_sed_doc(doc, working_dir, base_out_path, rel_out_path=None,
                 apply_xml_model_changes=False,
                 log=None, indent=0, pretty_print_modified_xml_models=False,
                 log_level=StandardOutputErrorCapturerLevel.c,
                 config=None,
                 simulator=Simulator.pyneuroml):
    """ Execute the tasks specified in a SED document and generate the specified outputs

    Args:
        doc (:obj:`SedDocument` or :obj:`str`): SED document or a path to SED-ML file which defines a SED document
        working_dir (:obj:`str`): working directory of the SED document (path relative to which models are located)

        base_out_path (:obj:`str`): path to store the outputs

            * CSV: directory in which to save outputs to files
              ``{base_out_path}/{rel_out_path}/{report.id}.csv``
            * HDF5: directory in which to save a single HDF5 file (``{base_out_path}/reports.h5``),
              with reports at keys ``{rel_out_path}/{report.id}`` within the HDF5 file

        rel_out_path (:obj:`str`, optional): path relative to :obj:`base_out_path` to store the outputs
        apply_xml_model_changes (:obj:`bool`, optional): if :obj:`True`, apply any model changes specified in the SED-ML file before
            calling :obj:`task_executer`.
        log (:obj:`SedDocumentLog`, optional): log of the document
        indent (:obj:`int`, optional): degree to indent status messages
        pretty_print_modified_xml_models (:obj:`bool`, optional): if :obj:`True`, pretty print modified XML models
        log_level (:obj:`StandardOutputErrorCapturerLevel`, optional): level at which to log output
        config (:obj:`Config`, optional): BioSimulators common configuration
        simulator (:obj:`Simulator`, optional): simulator

    Returns:
        :obj:`tuple`:

            * :obj:`ReportResults`: results of each report
            * :obj:`SedDocumentLog`: log of the document
    """
    return base_exec_sed_doc(functools.partial(exec_sed_task, simulator=simulator), doc, working_dir, base_out_path,
                             rel_out_path=rel_out_path,
                             apply_xml_model_changes=apply_xml_model_changes,
                             log=log,
                             indent=indent,
                             pretty_print_modified_xml_models=pretty_print_modified_xml_models,
                             log_level=log_level,
                             config=config)


def exec_sed_task(task, variables, preprocessed_task=None, log=None, config=None, simulator=Simulator.pyneuroml):
    ''' Execute a task and save its results

    Args:
        task (:obj:`Task`): task
        variables (:obj:`list` of :obj:`Variable`): variables that should be recorded
        preprocessed_task (:obj:`dict`, optional): preprocessed information about the task, including possible
            model changes and variables. This can be used to avoid repeatedly executing the same initialization
            for repeated calls to this method.
        log (:obj:`TaskLog`, optional): log for the task
        config (:obj:`Config`, optional): BioSimulators common configuration
        simulator (:obj:`Simulator`, optional): simulator

    Returns:
        :obj:`tuple`:

            :obj:`VariableResults`: results of variables
            :obj:`TaskLog`: log

    Raises:
        :obj:`ValueError`: if the task or an aspect of the task is not valid, or the requested output variables
            could not be recorded
        :obj:`NotImplementedError`: if the task is not of a supported type or involves an unsuported feature
    '''
    config = config or get_config()

    if config.LOG and not log:
        log = TaskLog()

    if preprocessed_task is None:
        preprocessed_task = preprocess_sed_task(task, variables, config=config, simulator=simulator)

    lems_root = preprocessed_task['model']

    if task.model.changes:
        raise_errors_warnings(validation.validate_model_change_types(task.model.changes, (ModelAttributeChange,)),
                              error_summary='Changes for model `{}` are not supported.'.format(task.model.id))

        model = copy.deepcopy(task.model)
        for change in model.changes:
            change.new_value = str(change.new_value)

        apply_changes_to_xml_model(model, lems_root, sed_doc=None, working_dir=None)

    lems_simulation = preprocessed_task['simulation']
    sim = task.simulation
    sim.algorithm = copy.deepcopy(sim.algorithm)
    sim.algorithm.kisao_id = preprocessed_task['algorithm_kisao_id']

    set_sim_in_lems_xml(lems_simulation, task, variables, simulator=simulator)
    lems_results = run_lems_xml(
        lems_root,
        working_dirname=os.path.dirname(task.model.source),
        lems_filename=task.model.source,
        simulator=simulator,
        verbose=config.VERBOSE,
        config=config,
    )[SEDML_OUTPUT_FILE_ID]

    # transform the results to an instance of :obj:`VariableResults`
    variable_results = VariableResults()
    for variable in variables:
        if variable.symbol:
            lems_result = lems_results.loc[:, SEDML_TIME_OUTPUT_COLUMN_ID]

        elif variable.target:
            lems_result = lems_results.loc[:, variable.id]

        variable_results[variable.id] = lems_result.to_numpy()[-(sim.number_of_points + 1):]

    # log action
    if config.LOG:
        log.algorithm = sim.algorithm.kisao_id
        log.simulator_details = {
            'method': preprocessed_task['simulation_method'],
            'lemsSimulation': {
                'length': '{}s'.format(sim.output_end_time),
                'step': '{}s'.format((sim.output_end_time - sim.output_start_time) / sim.number_of_steps),
                'method': preprocessed_task['algorithm_method'],
            },
        }

    # return results and log
    return variable_results, log


def preprocess_sed_task(task, variables, config=None, simulator=Simulator.pyneuroml):
    """ Preprocess a SED task, including its possible model changes and variables. This is useful for avoiding
    repeatedly initializing tasks on repeated calls of :obj:`exec_sed_task`.

    Args:
        task (:obj:`Task`): task
        variables (:obj:`list` of :obj:`Variable`): variables that should be recorded
        config (:obj:`Config`, optional): BioSimulators common configuration
        simulator (:obj:`Simulator`, optional): simulator

    Returns:
        :obj:`dict`: preprocessed information about the task
    """
    config = config or get_config()

    algorithm_kisao_id = validate_task(task, variables, simulator, config=config)

    lems_root = read_xml_file(task.model.source)
    lems_simulation = lems_root.xpath('/Lems/Simulation')[0]

    validate_lems_document(lems_root)

    # return preprocessed information
    return {
        'model': lems_root,
        'simulation': lems_simulation,
        'algorithm_kisao_id': algorithm_kisao_id,
        'simulation_method': 'pyneuroml.pynml.' + get_simulator_run_lems_method(simulator).__name__,
        'algorithm_method': KISAO_ALGORITHM_MAP[algorithm_kisao_id]['id'],
    }
