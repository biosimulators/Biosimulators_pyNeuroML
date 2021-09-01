""" Methods for using pyNeuroML to execute SED tasks in COMBINE archives and save their outputs

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-05-28
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .data_model import Simulator, KISAO_ALGORITHM_MAP, SEDML_TIME_OUTPUT_COLUMN_ID, SEDML_OUTPUT_FILE_ID
from .utils import validate_task, read_xml_file, set_sim_in_lems_xml, run_lems_xml, get_simulator_run_lems_method
from biosimulators_utils.combine.exec import exec_sedml_docs_in_archive
from biosimulators_utils.config import get_config, Config  # noqa: F401
from biosimulators_utils.log.data_model import CombineArchiveLog, TaskLog  # noqa: F401
from biosimulators_utils.viz.data_model import VizFormat  # noqa: F401
from biosimulators_utils.report.data_model import ReportFormat, VariableResults, SedDocumentResults  # noqa: F401
from biosimulators_utils.sedml.data_model import (Task, UniformTimeCourseSimulation,  # noqa: F401
                                                  Variable, Symbol)
from biosimulators_utils.sedml.exec import exec_sed_doc
import copy
import functools
import os

__all__ = [
    'exec_sedml_docs_in_combine_archive', 'exec_sed_task',
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
    sed_doc_executer = functools.partial(exec_sed_doc, functools.partial(exec_sed_task, simulator=simulator))
    return exec_sedml_docs_in_archive(sed_doc_executer, archive_filename, out_dir,
                                      apply_xml_model_changes=True,
                                      config=config)


def exec_sed_task(task, variables, log=None, config=None, simulator=Simulator.pyneuroml):
    ''' Execute a task and save its results

    Args:
       task (:obj:`Task`): task
       variables (:obj:`list` of :obj:`Variable`): variables that should be recorded
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

    sim = task.simulation
    sim.algorithm = copy.deepcopy(sim.algorithm)
    sim.algorithm.kisao_id = validate_task(task, variables, simulator, config=config)

    lems_root = read_xml_file(task.model.source)

    set_sim_in_lems_xml(lems_root, task, variables)
    lems_results = run_lems_xml(lems_root, working_dirname=os.path.dirname(
        task.model.source), lems_filename=task.model.source,
        verbose=config.VERBOSE, config=config)[SEDML_OUTPUT_FILE_ID]

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
            'method': 'pyneuroml.pynml.' + get_simulator_run_lems_method(simulator).__name__,
            'lemsSimulation': {
                'length': '{}s'.format(sim.output_end_time),
                'step': '{}s'.format((sim.output_end_time - sim.output_start_time) / sim.number_of_steps),
                'method': KISAO_ALGORITHM_MAP[sim.algorithm.kisao_id]['id'],
            },
        }

    # return results and log
    return variable_results, log
