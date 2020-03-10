# -*- coding: utf-8 -*-
# Copyright 2014 Diamond Light Source Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
.. module:: plugins_test
   :platform: Unix
   :synopsis: unittest test classes for plugins

.. moduleauthor:: Mark Basham <scientificsoftware@diamond.ac.uk>

"""

import unittest
import savu.test.test_utils as tu
from savu.test.travis.framework_tests.plugin_runner_test import \
    run_protected_plugin_runner_no_process_list    
import savu.test.base_checkpoint_test
import tempfile
import os

class AstraReconCPUTest(unittest.TestCase):
        
    def test_astra_recon_cpu(self):
        plugin = 'savu.plugins.reconstructions.astra_recons.astra_recon_cpu'
        self.test_folder = tempfile.mkdtemp(suffix='my_test/')        
        # set options 
        options = tu.set_experiment('tomo')
        options['out_path'] = os.path.join(self.test_folder)        
        #run the test
        run_protected_plugin_runner_no_process_list(options, plugin)     
        # perform folder cleaning 
        classb = savu.test.base_checkpoint_test.BaseCheckpointTest()        
        cp_folder = os.path.join(self.test_folder, 'checkpoint')
        classb._empty_folder(cp_folder)  
        os.removedirs(cp_folder)
        classb._empty_folder(self.test_folder)
        os.removedirs(self.test_folder)

    def test_astra_recon_cpu_stxm(self):
        plugin = 'savu.plugins.reconstructions.astra_recons.astra_recon_cpu'
        #create a temporal folder
        self.test_folder = tempfile.mkdtemp(suffix='my_test/')        
        options = tu.set_experiment('tomo')
        options['out_path'] = os.path.join(self.test_folder)              
        #run the test
        run_protected_plugin_runner_no_process_list(options, plugin)
        # perform folder cleaning 
        classb = savu.test.base_checkpoint_test.BaseCheckpointTest()        
        cp_folder = os.path.join(self.test_folder, 'checkpoint')
        classb._empty_folder(cp_folder)  
        os.removedirs(cp_folder)
        classb._empty_folder(self.test_folder)
        os.removedirs(self.test_folder)

if __name__ == "__main__":
    unittest.main()
