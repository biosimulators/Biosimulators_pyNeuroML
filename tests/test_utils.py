""" Tests of the utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-05-28
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from biosimulators_pyneuroml import data_model
from biosimulators_pyneuroml import utils
from biosimulators_utils.sedml.data_model import (
    Model, ModelLanguage, UniformTimeCourseSimulation, Algorithm, AlgorithmParameterChange, Task, Variable, Symbol)
from kisao.exceptions import AlgorithmCannotBeSubstitutedException
from kisao.warnings import AlgorithmSubstitutedWarning
from pyneuroml import pynml
from unittest import mock
import copy
import lxml.etree
import numpy.testing
import os
import shutil
import tempfile
import unittest


class UtilsTestCase(unittest.TestCase):
    def test_validate_task(self):
        task = Task(
            model=Model(
                id='net1',
                source=os.path.join(os.path.dirname(__file__), 'fixtures', 'LEMS_NML2_Ex5_DetCell.xml'),
                language=ModelLanguage.LEMS.value,
            ),
            simulation=UniformTimeCourseSimulation(
                id='sim',
                initial_time=0.,
                output_start_time=0.,
                output_end_time=10.,
                number_of_steps=10,
                algorithm=Algorithm(
                    kisao_id='KISAO_0000030',
                    changes=[],
                )
            ),
        )
        variables = [
            Variable(id='time', symbol=Symbol.time.value, task=task),
            Variable(id='v', target='hhpop[0]/v', task=task),
        ]

        self.assertEqual(utils.validate_task(task, variables, simulator=data_model.Simulator.pyneuroml), 'KISAO_0000030')

        task2 = copy.deepcopy(task)
        task2.simulation.initial_time = 5.
        task2.simulation.output_start_time = 5.
        with self.assertRaises(NotImplementedError):
            utils.validate_task(task2, variables, simulator=data_model.Simulator.pyneuroml)

        task2 = copy.deepcopy(task)
        task2.simulation.output_start_time = 0.1
        with self.assertRaises(NotImplementedError):
            utils.validate_task(task2, variables, simulator=data_model.Simulator.pyneuroml)

        task2 = copy.deepcopy(task)
        task2.simulation.algorithm.kisao_id = 'KISAO_0000019'
        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'NONE'}):
            with self.assertRaises(AlgorithmCannotBeSubstitutedException):
                utils.validate_task(task2, variables, simulator=data_model.Simulator.pyneuroml)
        with mock.patch.dict('os.environ', {'ALGORITHM_SUBSTITUTION_POLICY': 'SIMILAR_VARIABLES'}):
            with self.assertWarns(AlgorithmSubstitutedWarning):
                self.assertEqual(utils.validate_task(task2, variables, simulator=data_model.Simulator.pyneuroml), 'KISAO_0000030')

        task2 = copy.deepcopy(task)
        task2.simulation.algorithm.changes.append(AlgorithmParameterChange(kisao_id='KISAO_0000415', new_value='500'))
        with self.assertRaises(NotImplementedError):
            utils.validate_task(task2, variables, simulator=data_model.Simulator.pyneuroml)

        variables2 = copy.deepcopy(variables)
        variables2.append(Variable(id='symbol', symbol='undefined', task=task))
        with self.assertRaises(NotImplementedError):
            utils.validate_task(task, variables2, simulator=data_model.Simulator.pyneuroml)

    def test_set_sim_in_lems_xml(self):
        filename = os.path.join(os.path.dirname(__file__), 'fixtures', 'LEMS_NML2_Ex5_DetCell.xml')
        task = Task(
            model=Model(id='net1'),
            simulation=UniformTimeCourseSimulation(
                id='sim',
                initial_time=0.,
                output_start_time=0.,
                output_end_time=10.,
                number_of_steps=10,
                algorithm=Algorithm(
                    kisao_id='KISAO_0000030',
                    changes=[],
                ),
            ),
        )
        variables = [
            Variable(id='time', symbol=Symbol.time.value),
            Variable(id='v', target='hhpop[0]/v'),
        ]
        lems_xml_root = utils.read_xml_file(filename)
        sim_xml = lems_xml_root.xpath('/Lems/Simulation')[0]
        utils.set_sim_in_lems_xml(sim_xml, task, variables)
        self.assertEqual(sim_xml.attrib['length'], '10.0s')
        self.assertEqual(sim_xml.attrib['step'], '1.0s')
        self.assertEqual(sim_xml.attrib['method'], 'eulerTree')

        lems_xml_root = lxml.etree.Element('Undefined')
        with self.assertRaisesRegex(ValueError, 'must contain a single `Lems`'):
            utils.validate_lems_document(lems_xml_root)

        lems_xml_root = lxml.etree.Element('Lems')
        with self.assertRaisesRegex(ValueError, 'must have a `Simulation`'):
            utils.validate_lems_document(lems_xml_root)

        lems_xml_root = lxml.etree.Element('Lems')
        lems_xml_root.append(lxml.etree.Element('Simulation'))
        lems_xml_root.append(lxml.etree.Element('Simulation'))
        with self.assertRaisesRegex(ValueError, 'must have a single `Simulation`'):
            utils.validate_lems_document(lems_xml_root)

    def test_get_available_processors(self):
        processors = utils.get_available_processors()
        self.assertGreaterEqual(processors, 1)

    def test_get_available_memory(self):
        memory = utils.get_available_memory()
        self.assertGreater(memory, 100 * 1e6)

    def test_get_simulator_run_lems_method(self):
        self.assertEqual(utils.get_simulator_run_lems_method(data_model.Simulator.brian2), pynml.run_lems_with_jneuroml_brian2)
        self.assertEqual(utils.get_simulator_run_lems_method(data_model.Simulator.pyneuroml), pynml.run_lems_with_jneuroml)
        self.assertEqual(utils.get_simulator_run_lems_method(data_model.Simulator.netpyne), pynml.run_lems_with_jneuroml_netpyne)
        self.assertEqual(utils.get_simulator_run_lems_method(data_model.Simulator.neuron), pynml.run_lems_with_jneuroml_neuron)
        with self.assertRaises(NotImplementedError):
            utils.get_simulator_run_lems_method(None)

    def test_get_run_lems_options(self):
        options = utils.get_run_lems_options()
        self.assertGreaterEqual(options.num_processors, 1)
        self.assertGreaterEqual(options.max_memory, 100e6)

    def test_read_lems_output_files_configuration(self):
        filename = os.path.join(os.path.dirname(__file__), 'fixtures', 'LEMS_NML2_Ex5_DetCell.xml')
        root = lxml.etree.parse(filename).getroot()
        config = utils.read_lems_output_files_configuration(root)
        self.assertEqual(config, self._get_output_files_configuration())

    def test_write_lems_output_files_configuration(self):
        filename = os.path.join(os.path.dirname(__file__), 'fixtures', 'LEMS_NML2_Ex5_DetCell.xml')
        root = lxml.etree.parse(filename).getroot()
        config = self._get_output_files_configuration()
        config[0]['id'] = 'of2'
        config[1]['id'] = 'of3'
        utils.write_lems_output_files_configuration(root, config)

        fid, filename2 = tempfile.mkstemp(suffix='.xml')
        os.close(fid)
        copy_etree = lxml.etree.ElementTree(root)
        copy_etree.write(filename2)

        root = lxml.etree.parse(filename2).getroot()
        config2 = utils.read_lems_output_files_configuration(root)
        self.assertEqual(config2, config)

        os.remove(filename2)

    def _get_output_files_configuration(self):
        return [
            {
                'sim_id': 'sim1',
                'id': 'of0',
                'file_name': 'results/ex5_v.dat',
                'columns': [
                    {
                        'id': 'v',
                        'quantity': 'hhpop[0]/v'
                    },
                ],
            },
            {
                'sim_id': 'sim1',
                'id': 'of1',
                'file_name': 'results/ex5_vars.dat',
                'columns': [
                    {
                        'id': 'm',
                        'quantity': 'hhpop[0]/bioPhys1/membraneProperties/NaConductances/NaConductance/m/q'
                    },
                    {
                        'id': 'h',
                        'quantity': 'hhpop[0]/bioPhys1/membraneProperties/NaConductances/NaConductance/h/q'
                    },
                    {
                        'id': 'n',
                        'quantity': 'hhpop[0]/bioPhys1/membraneProperties/KConductances/KConductance/n/q'
                    },
                ],
            },
        ]

    def test_read_lems_output_files(self):
        filename = os.path.abspath(os.path.join(os.path.dirname(__file__), 'fixtures', 'LEMS_NML2_Ex5_DetCell.xml'))
        cur_dirname = os.getcwd()
        temp_dirname = tempfile.mkdtemp()
        os.chdir(temp_dirname)
        os.mkdir('results')

        pynml.run_lems_with_jneuroml(filename,
                                     skip_run=False, nogui=True, load_saved_data=False,
                                     reload_events=False, plot=False, show_plot_already=False,
                                     verbose=False, exit_on_fail=True, cleanup=True)

        filename = os.path.join(os.path.dirname(__file__), 'fixtures', 'LEMS_NML2_Ex5_DetCell.xml')
        root = lxml.etree.parse(filename).getroot()
        config = utils.read_lems_output_files_configuration(root)
        results = utils.read_lems_output_files(config)
        self.assertEqual(set(results.keys()), set(['of0', 'of1']))
        self.assertEqual(results['of1'].columns.values.tolist(), ['__time__', 'm', 'h', 'n'])
        numpy.testing.assert_allclose(results['of1'].loc[:, '__time__'], numpy.linspace(0., 300e-3, 30000 + 1))
        os.chdir(cur_dirname)
        shutil.rmtree(temp_dirname)

    def test_run_lems_xml(self):
        filename = os.path.join(os.path.dirname(__file__), 'fixtures', 'LEMS_NML2_Ex5_DetCell.xml')
        for simulator in [data_model.Simulator.pyneuroml]:
            lems_xml_root = utils.read_xml_file(filename)
            results = utils.run_lems_xml(lems_xml_root, os.path.dirname(filename), simulator=simulator)
            self.assertEqual(set(results.keys()), set(['of0', 'of1']))
            self.assertEqual(results['of1'].columns.values.tolist(), ['__time__', 'm', 'h', 'n'])
            numpy.testing.assert_allclose(results['of1'].loc[:, '__time__'], numpy.linspace(0., 300e-3, 30000 + 1))

        with mock.patch('pyneuroml.pynml.run_lems_with_jneuroml', return_value=False):
            with self.assertRaises(RuntimeError):
                utils.run_lems_xml(lems_xml_root, os.path.dirname(filename))
