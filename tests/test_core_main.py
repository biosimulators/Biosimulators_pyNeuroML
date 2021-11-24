""" Tests of the command-line interface

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-05-28
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from biosimulators_pyneuroml import core
from biosimulators_pyneuroml.data_model import Simulator, SIMULATOR_ENABLED, KISAO_ALGORITHM_MAP
from biosimulators_utils.combine import data_model as combine_data_model
from biosimulators_utils.combine.io import CombineArchiveWriter
from biosimulators_utils.config import get_config
from biosimulators_utils.log.data_model import TaskLog
from biosimulators_utils.report import data_model as report_data_model
from biosimulators_utils.report.io import ReportReader
from biosimulators_utils.simulator.exec import exec_sedml_docs_in_archive_with_containerized_simulator
from biosimulators_utils.simulator.specs import gen_algorithms_from_specs
from biosimulators_utils.sedml import data_model as sedml_data_model
from biosimulators_utils.sedml.io import SedmlSimulationWriter
from unittest import mock
import datetime
import dateutil.tz
import importlib
import numpy
import numpy.testing
import os
import parameterized
import shutil
import tempfile
import unittest


class CoreCliTestCase(unittest.TestCase):
    DOCKER_IMAGES = {
        Simulator.brian2: 'ghcr.io/biosimulators/biosimulators_pyneuroml/brian2:latest',
        Simulator.netpyne: 'ghcr.io/biosimulators/biosimulators_pyneuroml/netpyne:latest',
        Simulator.neuron: 'ghcr.io/biosimulators/biosimulators_pyneuroml/neuron:latest',
        Simulator.pyneuroml: 'ghcr.io/biosimulators/biosimulators_pyneuroml/pyneuroml:latest',
    }
    FIXTURES_DIRNAME = os.path.join(os.path.dirname(__file__), 'fixtures')

    def setUp(self):
        self.dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dirname)

    def test_exec_sed_task(self):
        task, variables = self._get_simulation()
        log = TaskLog()
        results, log = core.exec_sed_task(task, variables, log=log)
        self._assert_variable_results(task, variables, results)

    def test_exec_sed_task_with_changes(self):
        # TODO: add test for continuation of time course
        # - Simulation 1: 0-10 ms
        # - Simulation 2: 0-5 ms
        # - Simulation 3: 5-10 ms starting from simulation #2

        task, variables = self._get_simulation()
        preprocessed_task = core.preprocess_sed_task(task, variables)

        core.exec_sed_task(task, variables, preprocessed_task=preprocessed_task)

        task.model.changes.append(sedml_data_model.ModelAttributeChange(
            target="/Lems/Include[@file='Cells.xml']/@file",
            new_value='Undefined.xml',
        ))
        with self.assertRaises(RuntimeError):
            core.exec_sed_task(task, variables, preprocessed_task=preprocessed_task)

    @parameterized.parameterized.expand([
        (name,) 
        for name, simulator in Simulator.__members__.items()
        if SIMULATOR_ENABLED[simulator]
    ])
    def test_exec_sed_task_with_simulator(self, simulator_name):
        task, variables = self._get_simulation()
        log = TaskLog()
        results, log = core.exec_sed_task(task, variables, log=log, simulator=Simulator[simulator_name])
        self._assert_variable_results(task, variables, results)

    def test_exec_sed_task_non_zero_output_start_time(self):
        task, variables = self._get_simulation()
        task.simulation.output_start_time = 100e-3
        task.simulation.number_of_steps = int(200 / 0.01)
        log = TaskLog()
        results, log = core.exec_sed_task(task, variables, log=log)
        self._assert_variable_results(task, variables, results)

    def test_exec_sedml_docs_in_combine_archive(self):
        doc, archive_filename = self._build_combine_archive()

        out_dir = os.path.join(self.dirname, 'out')

        config = get_config()
        config.REPORT_FORMATS = [report_data_model.ReportFormat.h5]
        config.BUNDLE_OUTPUTS = True
        config.KEEP_INDIVIDUAL_OUTPUTS = True

        _, log = core.exec_sedml_docs_in_combine_archive(archive_filename, out_dir, config=config)
        if log.exception:
            raise log.exception

        self._assert_combine_archive_outputs(doc, out_dir)

    def test_exec_sedml_docs_in_combine_archive_with_all_algorithms(self):
        for simulator in [Simulator.pyneuroml]:
            specs_filename = os.path.join(os.path.dirname(__file__), '..', 'biosimulators-{}.json'.format(simulator.name))
            for alg in gen_algorithms_from_specs(specs_filename).values():
                alg_props = KISAO_ALGORITHM_MAP[alg.kisao_id]
                doc, archive_filename = self._build_combine_archive(algorithm=alg)

                out_dir = os.path.join(self.dirname, 'out')

                config = get_config()
                config.REPORT_FORMATS = [report_data_model.ReportFormat.h5]
                config.BUNDLE_OUTPUTS = True
                config.KEEP_INDIVIDUAL_OUTPUTS = True

                _, log = core.exec_sedml_docs_in_combine_archive(archive_filename, out_dir, config=config, simulator=simulator)
                if log.exception:
                    raise log.exception

                self._assert_combine_archive_outputs(doc, out_dir)

    def _get_simulation(self, algorithm=None):
        if os.path.isdir(os.path.join(self.dirname, 'fixtures')):
            shutil.rmtree(os.path.join(self.dirname, 'fixtures'))
        shutil.copytree(self.FIXTURES_DIRNAME, os.path.join(self.dirname, 'fixtures'))

        model_source = os.path.join(self.dirname, 'fixtures', 'LEMS_NML2_Ex5_DetCell.xml')

        if algorithm is None:
            algorithm = sedml_data_model.Algorithm(
                kisao_id='KISAO_0000030',
                changes=[],
            )

        task = sedml_data_model.Task(
            model=sedml_data_model.Model(id='net1', source=model_source, language=sedml_data_model.ModelLanguage.LEMS.value),
            simulation=sedml_data_model.UniformTimeCourseSimulation(
                initial_time=0.,
                output_start_time=0.,
                output_end_time=300e-3,
                number_of_steps=int(300 / 0.01),
                algorithm=algorithm,
            ),
        )

        variables = [
            sedml_data_model.Variable(
                id='time',
                symbol=sedml_data_model.Symbol.time.value,
                task=task,
            ),
            sedml_data_model.Variable(
                id='v',
                target="hhpop[0]/v",
                task=task,
            ),
            sedml_data_model.Variable(
                id='m',
                target="hhpop[0]/bioPhys1/membraneProperties/NaConductances/NaConductance/m/q",
                task=task,
            ),
            sedml_data_model.Variable(
                id='h',
                target="hhpop[0]/bioPhys1/membraneProperties/NaConductances/NaConductance/h/q",
                task=task,
            ),
            sedml_data_model.Variable(
                id='n',
                target="hhpop[0]/bioPhys1/membraneProperties/KConductances/KConductance/n/q",
                task=task,
            ),
        ]

        return task, variables

    def _build_sed_doc(self, algorithm=None):
        task, variables = self._get_simulation(algorithm=algorithm)

        doc = sedml_data_model.SedDocument()

        model = task.model
        model.id = 'net1'
        doc.models.append(model)

        sim = task.simulation
        sim.id = 'simulation'
        doc.simulations.append(sim)

        task.id = 'task'
        doc.tasks.append(task)

        report = sedml_data_model.Report(id='report1')
        doc.outputs.append(report)
        for variable in variables:
            data_gen = sedml_data_model.DataGenerator(
                id='data_generator_' + variable.id,
                variables=[
                    variable,
                ],
                math=variable.id,
            )
            doc.data_generators.append(data_gen)
            report.data_sets.append(sedml_data_model.DataSet(id='data_set_' + variable.id, label=variable.id, data_generator=data_gen))

        return doc

    def _build_combine_archive(self, algorithm=None):
        doc = self._build_sed_doc(algorithm=algorithm)

        archive_dirname = os.path.join(self.dirname, 'archive')
        if not os.path.isdir(archive_dirname):
            os.mkdir(archive_dirname)

        model_filename = os.path.join(archive_dirname, 'model1.xml')
        shutil.copyfile(doc.models[0].source, model_filename)
        doc.models[0].source = 'model1.xml'

        archive = combine_data_model.CombineArchive(
            contents=[
                combine_data_model.CombineArchiveContent(
                    'model1.xml', combine_data_model.CombineArchiveContentFormat.LEMS.value),
                combine_data_model.CombineArchiveContent(
                    'simulation.sedml', combine_data_model.CombineArchiveContentFormat.SED_ML.value),
            ],
        )

        included_rel_model_files = [
            'NaConductance.channel.nml',
            'KConductance.channel.nml',
            'LeakConductance.channel.nml',
            'NML2_SingleCompHHCell.nml',
        ]
        for included_rel_model_file in included_rel_model_files:
            shutil.copyfile(
                os.path.join(self.FIXTURES_DIRNAME, included_rel_model_file),
                os.path.join(archive_dirname, included_rel_model_file))
            archive.contents.append(
                combine_data_model.CombineArchiveContent(
                    location=included_rel_model_file,
                    format=combine_data_model.CombineArchiveContentFormat.NeuroML.value,
                ),
            )

        sim_filename = os.path.join(archive_dirname, 'simulation.sedml')
        SedmlSimulationWriter().run(doc, sim_filename)

        archive_filename = os.path.join(self.dirname, 'archive.omex')
        CombineArchiveWriter().run(archive, archive_dirname, archive_filename)

        return (doc, archive_filename)

    def _assert_variable_results(self, task, variables, results):
        sim = task.simulation
        self.assertTrue(set(results.keys()), set([var.id for var in variables]))
        numpy.testing.assert_allclose(results['time'], numpy.linspace(sim.output_start_time, sim.output_end_time, sim.number_of_points + 1))
        for result in results.values():
            self.assertEqual(result.shape, (sim.number_of_points + 1,))
            self.assertFalse(numpy.any(numpy.isnan(result)))

    def _assert_combine_archive_outputs(self, doc, out_dir):
        sim = doc.simulations[0]
        report = doc.outputs[0]

        # check HDF report
        report_results = ReportReader().run(report, out_dir, 'simulation.sedml/report1', format=report_data_model.ReportFormat.h5)

        self.assertEqual(sorted(report_results.keys()), sorted([d.id for d in report.data_sets]))

        numpy.testing.assert_allclose(report_results['data_set_time'], numpy.linspace(
            sim.output_start_time, sim.output_end_time, sim.number_of_points + 1))
        for result in report_results.values():
            self.assertEqual(result.shape, (sim.number_of_points + 1,))
            self.assertFalse(numpy.any(numpy.isnan(result)))

    def test_raw_cli(self):
        for simulator in Simulator.__members__.values():
            cli = importlib.import_module('biosimulators_pyneuroml.cli.{}'.format(simulator.name))
            with mock.patch('sys.argv', ['', '--help']):
                with self.assertRaises(SystemExit) as context:
                    cli.main()
                    self.assertRegex(context.Exception, 'usage: ')

    def test_exec_sedml_docs_in_combine_archive_with_cli(self):
        doc, archive_filename = self._build_combine_archive()
        env = self._get_combine_archive_exec_env()

        for simulator in [Simulator.pyneuroml]:
            out_dir = os.path.join(self.dirname, 'out-' + simulator.name)
            cli = importlib.import_module('biosimulators_pyneuroml.cli.{}'.format(simulator.name))
            with mock.patch.dict(os.environ, env):
                cli.main(argv=['-i', archive_filename, '-o', out_dir])

            self._assert_combine_archive_outputs(doc, out_dir)

    @parameterized.parameterized.expand([
        (name,) 
        for name, simulator in Simulator.__members__.items()
        if SIMULATOR_ENABLED[simulator]
    ])
    def test_exec_sedml_docs_in_combine_archive_with_docker_image(self, simulator_name):
        doc, archive_filename = self._build_combine_archive()
        env = self._get_combine_archive_exec_env()

        simulator = Simulator[simulator_name]
        out_dir = os.path.join(self.dirname, 'out-' + simulator.name)
        exec_sedml_docs_in_archive_with_containerized_simulator(
            archive_filename, out_dir,
            self.DOCKER_IMAGES[simulator])

        self._assert_combine_archive_outputs(doc, out_dir)

    def _get_combine_archive_exec_env(self):
        return {
            'REPORT_FORMATS': 'h5'
        }
