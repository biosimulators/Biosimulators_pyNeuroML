""" Tests of the data model

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2021-05-28
:Copyright: 2021, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from biosimulators_pyneuroml import data_model
import json
import os
import unittest


class DataModelTestCase(unittest.TestCase):
    def test_KISAO_ALGORITHM_MAP(self):
        self.assertEqual(data_model.KISAO_ALGORITHM_MAP['KISAO_0000030']['id'], 'eulerTree')

    def test_KISAO_ALGORITHM_MAP_consistent_with_specs(self):
        for simulator in data_model.Simulator.__members__.values():
            with open(os.path.join(os.path.dirname(__file__), '..', 'biosimulators-{}.json'.format(simulator.name)), 'r') as file:
                specs = json.load(file)

            self.assertEqual(set(alg['kisao_id']
                                 for alg in data_model.KISAO_ALGORITHM_MAP.values()
                                 if simulator in alg['simulators']),
                             set(alg_specs['kisaoId']['id'] for alg_specs in specs['algorithms']))

            for alg_specs in specs['algorithms']:
                alg_props = data_model.KISAO_ALGORITHM_MAP[alg_specs['kisaoId']['id']]

                self.assertEqual(set(alg_props['parameters'].keys()),
                                 set(param_specs['kisaoId']['id'] for param_specs in alg_specs['parameters']))
                self.assertEqual(alg_props['parameters'], {})

    def test_Simulator(self):
        self.assertEqual(data_model.Simulator.neuron.value, 'NEURON')

    def test_RunLemsOptions(self):
        options = data_model.RunLemsOptions(num_processors=2, max_memory=1e6).to_kw_args(data_model.Simulator.netpyne)
        self.assertGreaterEqual(options['max_memory'], '1M')
        self.assertGreaterEqual(options['num_processors'], 2)
        self.assertGreaterEqual(options['only_generate_scripts'], False)
        self.assertNotIn('compile_mods', options)
        self.assertNotIn('realtime_output', options)

        options = data_model.RunLemsOptions(num_processors=2, max_memory=1e6).to_kw_args(data_model.Simulator.neuron)
        self.assertGreaterEqual(options['max_memory'], '1M')
        self.assertNotIn('num_processors', options)
        self.assertGreaterEqual(options['only_generate_scripts'], False)
        self.assertGreaterEqual(options['compile_mods'], True)
        self.assertGreaterEqual(options['realtime_output'], False)
