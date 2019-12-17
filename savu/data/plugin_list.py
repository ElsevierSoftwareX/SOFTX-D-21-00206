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
.. module:: plugin_list
   :platform: Unix
   :synopsis: Contains the PluginList class, which deals with loading and \
   saving the plugin list, and the CitationInformation class. An instance is \
   held by the MetaData class.

.. moduleauthor:: Nicola Wadeson <scientificsoftware@diamond.ac.uk>

"""
import os
import re
import ast
import yaml
import h5py
import json
import copy
import inspect
import logging

import numpy as np
from collections import defaultdict
from yamllint.config import YamlLintConfig
from yamllint import linter

from colorama import Fore
import savu.plugins.utils as pu
from savu.data.meta_data import MetaData
import savu.data.framework_citations as fc
import savu.plugins.loaders.utils.yaml_utils as yu


NX_CLASS = 'NX_class'


class PluginList(object):
    """
    The PluginList class handles the plugin list - loading, saving and adding
    citation information for the plugin
    """

    def __init__(self):
        self.plugin_list = []
        self.n_plugins = None
        self.n_loaders = 0
        self.n_savers = 0
        self.loader_idx = None
        self.saver_idx = None
        self.datasets_list = []
        self.saver_plugin_status = True
        self._template = None
        self.version = None

    def add_template(self, create=False):
        self._template = Template(self)
        if create:
            self._template.creating = True

    def _get_plugin_entry_template(self):
        template = {'active': True,
                    'name': None,
                    'id': None,
                    'desc': None,
                    'data': None,
                    'user': [],
                    'hide': [],
                    'types': None}
        return template

    def __get_json_keys(self):
        return ['data', 'desc', 'user', 'hide']

    def _populate_plugin_list(self, filename, activePass=False,
                              template=False):
        """ Populate the plugin list from a nexus file. """

        plugin_file = h5py.File(filename, 'r')
        
        if 'entry/savu_notes/version' in plugin_file:
            self.version = plugin_file['entry/savu_notes/version'][()]

        plugin_group = plugin_file['entry/plugin']
        self.plugin_list = []
        single_val = ['name', 'id', 'pos', 'active']
        exclude = ['citation']
        for key in plugin_group.keys():
            plugin = self._get_plugin_entry_template()
            entry_keys = plugin_group[key].keys()
            json_keys = [k for k in entry_keys for e in exclude if k not in
                         single_val and e not in k]

            if 'active' in entry_keys:
                plugin['active'] = plugin_group[key]['active'][0]

            if plugin['active'] or activePass:

                plugin['name'] = plugin_group[key]['name'][0]
                plugin['id'] = plugin_group[key]['id'][0]
                plugin['pos'] = key.encode('ascii').strip()

                for jkey in json_keys:
                    plugin[jkey] = \
                        self._byteify(json.loads(plugin_group[key][jkey][0]))
                self.plugin_list.append(plugin)

        if template:
            self.add_template()
            self._template.update_process_list(template)

        plugin_file.close()

    def _is_valid(self, value, subelem, pos):
        parameter_valid = False
        options = ''
        formats = ''
        examples = ''

        if subelem in self.plugin_list[pos]['types']:
            # The parameter is within the types
            ptype = self.plugin_list[pos]['types'][subelem]
            pdesc = self.plugin_list[pos]['desc'][subelem]
            if not isinstance(pdesc, str):
                if 'options' in pdesc.keys():
                    options = pdesc['options']
                if 'format' in pdesc:
                    formats = pdesc['format']
                if 'examples' in pdesc:
                    examples = pdesc['examples']

            if len(options) >= 1:
                options = [i.lower() for i in options]
                if value.lower() in options:
                    parameter_valid = True
                else:
                    print(Fore.CYAN + '\nSome options are:')
                    for o in options:
                        print(o)
                    print(Fore.RESET)
            else:
                if ptype == '[int]':
                    sequence = False
                    if isinstance(value, str) and ';' in value:
                        value = value.split(';')
                        if len(value[0]) == 1 and isinstance(value[0], int):
                            value = list(np.arange(0, value[0], 1))
                            parameter_valid = True
                            sequence = True
                        if ":" in value[0]:
                            # <first-value>:<last-value>:<difference>;
                            seq = value[0].split(':')
                            seq = [eval(s) for s in seq]
                            if len(seq) == 3:
                                # The sequence values
                                sequence_values = list(np.arange(seq[0], seq[1], seq[2]))
                                if len(sequence_values) == 0:
                                    raise RuntimeError('Ensure start:stop:step; values are valid.')
                                else:
                                    sequence = True
                                    parameter_valid = True
                                # value = [ast.literal_eval(i) for i in value]
                            elif len(seq) == 2:
                                if isinstance(seq[0], int) and isinstance(seq[1], int):
                                    value = list(np.arange(seq[0], seq[1], 1))
                                    parameter_valid = True
                                    sequence = True
                            else:
                                print('The format should be start:stop:step;')
                    if not sequence:
                        bracket_value = value.split('[')
                        bracket_value = bracket_value[1].split(']')
                        value = bracket_value[0]
                        entries = value.split(',')
                        print('Not a sequence')
                        # TO DO further split check

                elif ptype == 'range':
                    entries = value.split(',')
                    if len(entries) == 2:
                        if isinstance(entries[0], int) and isinstance(entries[1], int):
                            parameter_valid = True
                elif ptype == 'yaml_file':
                    if isinstance(value, str):
                        config_file = open('/home/glb23482/git_projects/Savu/savu/plugins/loaders/utils/yaml_config.yaml')
                        conf = YamlLintConfig(config_file)
                        f = open(value)
                        gen = linter.run(f, conf)
                        errors = list(gen)
                        if errors:
                            print('There were some errors with your yaml file structure.\n')

                            for e in errors:
                                print(e)
                        else:
                            parameter_valid = True

                elif ptype == '[path, int_path, int]':
                    try:
                        bracket_value = value.split('[')
                        bracket_value = bracket_value[1].split(']')
                        entries = bracket_value[0].split(',')
                        if len(entries) == 3:
                            file_path = entries[0]
                            if os.path.isfile(file_path):
                                int_path = entries[1]
                                hf = h5py.File(file_path, 'r')
                                try:
                                    # This returns a HDF5 dataset object
                                    int_data = hf.get(int_path)
                                    if int_data is None:
                                        print('\nThere is no data stored at that internal path.')
                                    else:
                                        int_data = np.array(int_data)
                                        if int_data.size >= 1:
                                            try:
                                                compensation_fact = int(entries[2])
                                                if isinstance(compensation_fact, int):
                                                    parameter_valid = True
                                                else:
                                                    print(Fore.BLUE + '\nThe compensation factor is'
                                                                      ' not valid.' + Fore.RESET)
                                            except ValueError:
                                                print('\nThe compensation factor is not an integer.')
                                            except Exception:
                                                print('There is a problem converting the compensation'
                                                      ' factor to an integer.')

                                except AttributeError:
                                    print('Attribute error.')
                                except:
                                    print(Fore.BLUE + '\nPlease choose another interior'
                                                      ' path.' + Fore.RESET)
                                    print('Example interior paths: ')
                                    for group in hf:
                                        for subgroup in hf[group]:
                                            subgroup_str = '/' + group + '/' + subgroup
                                            print(u'\t' + subgroup_str)
                                    raise
                                hf.close()
                            else:
                                print(Fore.BLUE + '\nThis file does not exist at this'
                                                  ' location.' + Fore.RESET)
                        else:
                            print(Fore.RED + '\nPlease enter three parameters.' + Fore.RESET)

                    except ValueError:
                        parameter_valid = False
                        print('Valid items have a format [<file path>,'
                              ' <interior file path>, int].')
                    except AttributeError:
                        print('You need to place some information inside the square brackets.')
                    except Exception as e:
                        print(e)

                elif ptype == 'path':
                    path = os.path.dirname(value)
                    path = path if path else '.'
                    if os.path.isdir(path):
                        parameter_valid = True
                        print('This path is to a directory.')
                    elif os.path.isfile(path):
                        parameter_valid = True
                        print('This path is to a file.')
                    else:
                        print('Valid items contain numbers, letters and \'/\'')
                        file_error = "INPUT_ERROR: Incorrect filepath."
                        raise Exception(file_error)

                elif ptype == 'int_path':
                    # Check if the entry is a string
                    # Could check if valid, but only if file_path known for another parameter
                    if isinstance(value, str):
                        parameter_valid = True
                    else:
                        print('Not a valid string.')

                elif ptype == 'int':
                    if isinstance(value, int):
                        parameter_valid = True
                    else:
                        print('%s is not a valid integer.' % value)

                elif ptype == 'bool':
                    if isinstance(value, bool):
                        parameter_valid = True
                    elif value == 'true' | value == 'false':
                        parameter_valid = True
                    else:
                        print('Not a valid boolean.')

                elif ptype == 'str':
                    if isinstance(value, str):
                        parameter_valid = True
                    else:
                        print('Not a valid string.')

                elif ptype == 'float':
                    if isinstance(value, float):
                        parameter_valid = True
                    else:
                        print('Not a valid float.')
                else:
                    parameter_valid = False

                if parameter_valid is False:
                    print('\nYour input for the parameter \'%s\' must match the'
                          ' required type %s' % (subelem, ptype))

                    if len(formats) >= 1:
                        print(Fore.CYAN + 'Format accepted for the parameter '
                                          'named \'%s\':' % subelem)
                        for f in formats:
                            print(f)
    
                    if len(examples) >= 1:
                        print(Fore.RED + '\nSome examples are:')
                        for e in examples:
                            print(e)
                    print(Fore.RESET)
        else:
            print('Not in parameter keys.')
        return parameter_valid

    def _save_plugin_list(self, out_filename):
        with h5py.File(out_filename, 'w') as nxs_file:
            entry_group = nxs_file.require_group('entry')
            
            citations_group = entry_group.create_group('framework_citations')
            citations_group.attrs[NX_CLASS] = 'NXcollection'
            self._save_framework_citations(citations_group)
            
            savu_notes_group = entry_group.create_group('savu_notes')
            savu_notes_group.attrs[NX_CLASS] = 'NXnote'
            self.__save_savu_notes(savu_notes_group)
            
            plugins_group = entry_group.create_group('plugin')
            plugins_group.attrs[NX_CLASS] = 'NXprocess'

            count = 1
            for plugin in self.plugin_list:
                self.__populate_plugins_group(plugins_group, plugin, count)

        if self._template and self._template.creating:
            fname = os.path.splitext(out_filename)[0] + '.savu'
            self._template._output_template(fname, out_filename)

    def __save_savu_notes(self, notes):
        from savu.version import __version__
        notes['version'] = __version__

    def __populate_plugins_group(self, plugins_group, plugin, count):
        if 'pos' in plugin.keys():
            num = int(re.findall('\d+', plugin['pos'])[0])
            letter = re.findall('[a-z]', plugin['pos'])
            letter = letter[0] if letter else ""
            plugin_group = \
                plugins_group.create_group("%*i%*s" % (4, num, 1, letter))
        else:
            plugin_group = plugins_group.create_group("%*i" % (4, count))

        plugin_group.attrs[NX_CLASS] = 'NXnote'
        required_keys = self._get_plugin_entry_template().keys()
        json_keys = self.__get_json_keys()

        if 'cite' in plugin.keys():
            if plugin['cite'] is not None:
                self._output_plugin_citations(plugin['cite'], plugin_group)

        for key in required_keys:
            # only need to apply dumps if saving in configurator
            data = self.__dumps(plugin[key]) if key == 'data' else plugin[key]
            array = np.array([json.dumps(data)]) if key in json_keys else\
                np.array([plugin[key]])
            plugin_group.create_dataset(key, array.shape, array.dtype, array)

    def __dumps(self, data_dict):
        """ Replace any missing quotes around variables
        """
        for key, val in data_dict.iteritems():
            if isinstance(val, str):
                try:
                    data_dict[key] = ast.literal_eval(val)
                    continue
                except:
                    pass
                try:
                    data_dict[key] = yaml.load(val, Loader=yaml.SafeLoader)
                    continue
                except:
                    pass
                try:
                    isdict = re.findall("[\{\}]+", val)
                    if isdict:
                        val = val.replace("[", "'[").replace("]", "]'")
                        data_dict[key] = self.__dumps(yaml.load(val))
                    else:
                        data_dict[key] = pu.parse_config_string(val)
                    continue
                except:
                    # for when parameter tuning with lists is added to the framework
                    if len(val.split(';')) > 1:
                        pass
                    else:
                        raise Exception("Invalid string %s" % val)
        return data_dict

    def _add(self, idx, entry):
        self.plugin_list.insert(idx, entry)
        self.__set_loaders_and_savers()

    def _remove(self, idx):
        del self.plugin_list[idx]
        self.__set_loaders_and_savers()

    def _output_plugin_citations(self, citations, group):
        if not isinstance(citations, list):
            citations = [citations]
        for cite in citations:
            citation_group = group.create_group(cite.name)
            cite.write(citation_group)

    def _save_framework_citations(self, group):
        framework_cites = fc.get_framework_citations()
        count = 0
        for cite in framework_cites:
            citation_group = group.create_group(cite['name'])
            citation = CitationInformation()
            del cite['name']
            for key, value in cite.iteritems():
                exec('citation.' + key + '= value')
            citation.write(citation_group)
            count += 1

    def _get_docstring_info(self, plugin):
        plugin_inst = pu.plugins[plugin]()
        plugin_inst._populate_default_parameters()
        return plugin_inst.docstring_info

    def _byteify(self, input):
        if isinstance(input, dict):
            return {self._byteify(key): self._byteify(value)
                    for key, value in input.iteritems()}
        elif isinstance(input, list):
            temp = [self._byteify(element) for element in input]
            return temp
        elif isinstance(input, unicode):
            return input.encode('utf-8')
        else:
            return input

    def _set_datasets_list(self, plugin):
        in_pData, out_pData = plugin.get_plugin_datasets()
        in_data_list = self._populate_datasets_list(in_pData)
        out_data_list = self._populate_datasets_list(out_pData)
        self.datasets_list.append({'in_datasets': in_data_list,
                                   'out_datasets': out_data_list})

    def _populate_datasets_list(self, data):
        data_list = []
        for d in data:
            name = d.data_obj.get_name()
            pattern = copy.deepcopy(d.get_pattern())
            pattern[pattern.keys()[0]]['max_frames_transfer'] = \
                d.meta_data.get('max_frames_transfer')
            pattern[pattern.keys()[0]]['transfer_shape'] = \
                d.meta_data.get('transfer_shape')
            data_list.append({'name': name, 'pattern': pattern})
        return data_list

    def _get_datasets_list(self):
        return self.datasets_list

    def _reset_datasets_list(self):
        self.datasets_list = []

    def _get_n_loaders(self):
        return self.n_loaders

    def _get_n_savers(self):
        return self.n_savers

    def _get_loaders_index(self):
        return self.loader_idx

    def _get_savers_index(self):
        return self.saver_idx

    def _get_n_processing_plugins(self):
        return len(self.plugin_list) - self._get_n_loaders()

    def __set_loaders_and_savers(self):
        """ Get lists of loader and saver positions within the plugin list and
        set the number of loaders.

        :returns: loader index list and saver index list
        :rtype: list(int(loader)), list(int(saver))
        """
        from savu.plugins.loaders.base_loader import BaseLoader
        from savu.plugins.savers.base_saver import BaseSaver
        loader_idx = []
        saver_idx = []
        self.n_plugins = len(self.plugin_list)

        for i in range(self.n_plugins):
            bases = inspect.getmro(pu.load_class(self.plugin_list[i]['id']))
            loader_list = [b for b in bases if b == BaseLoader]
            saver_list = [b for b in bases if b == BaseSaver]
            if loader_list:
                loader_idx.append(i)
            if saver_list:
                saver_idx.append(i)
        self.loader_idx = loader_idx
        self.saver_idx = saver_idx
        self.n_loaders = len(loader_idx)
        self.n_savers = len(saver_idx)

    def _check_loaders_and_savers(self):
        """ Check plugin list starts with a loader and ends with a saver.
        """
        self.__set_loaders_and_savers()
        loaders = self._get_loaders_index()
        savers = self._get_savers_index()

        if loaders:
            if loaders[0] is not 0 or loaders[-1]+1 is not len(loaders):
                raise Exception("All loader plugins must be at the beginning "
                                "of the process list")
            if len(loaders) > 1:
                print('You have more than one loader plugin.')
        else:
            raise Exception("The first item in the process list must be a "
                            "loader plugin.")

        if savers:
            if savers[-1]+1 is not self.n_plugins:
                raise Exception("All saver plugins must be at the end "
                                "of the process list")
            if len(savers) > 1:
                print('You have more than one saver plugin.')
        else:
            raise Exception("The last item in the process list must be a "
                            "saver plugin.")

    def _add_missing_savers(self, data_names):
        """ Add savers for missing datasets. """
        saved_data = []
        for i in self._get_savers_index():
            saved_data.append(self.plugin_list[i]['data']['in_datasets'])
        saved_data = set([s for sub_list in saved_data for s in sub_list])

        for name in [data for data in data_names if data not in saved_data]:
            process = {}
            pos = int(re.search(r'\d+', self.plugin_list[-1]['pos']).group())+1
            self.saver_idx.append(pos)
            plugin = pu.get_plugin('savu.plugins.savers.hdf5_saver')
            plugin.parameters['in_datasets'] = [name]
            process['name'] = plugin.name
            process['id'] = plugin.__module__
            process['pos'] = str(pos)
            process['data'] = plugin.parameters
            process['active'] = True
            process['desc'] = plugin.parameters_desc
            self._add(pos, process)

    def _get_dataset_flow(self):
        datasets_idx = []
        n_loaders = self._get_n_loaders()
        n_plugins = self._get_n_processing_plugins()
        for i in range(self.n_loaders, n_loaders+n_plugins):
            datasets_idx.append(self.plugin_list[i]['data']['out_datasets'])
        return datasets_idx

    def _contains_gpu_processes(self):
        """ Returns True if gpu processes exist in the process list. """
        try:
            from savu.plugins.driver.gpu_plugin import GpuPlugin
            for i in range(self.n_plugins):
                bases = inspect.getmro(pu.load_class(self.plugin_list[i]['id']))
                if GpuPlugin in bases:
                    return True
        except ImportError as ex:
            if "pynvml" in ex.message:
                logging.error('Error while importing GPU dependencies: %s',
                              ex.message)
            else:
                raise

        return False


class Template(object):
    """ A class to read and write templates for plugin lists.
    """

    def __init__(self, plist):
        super(Template, self).__init__()
        self.plist = plist
        self.creating = False

    def _output_template(self, fname, process_fname):
        plist = self.plist.plugin_list
        index = [i for i in range(len(plist)) if plist[i]['active']]

        local_dict = MetaData(ordered=True)
        global_dict = MetaData(ordered=True)
        local_dict.set(['process_list'], os.path.abspath(process_fname))

        for i in index:
            params = self.__get_template_params(plist[i]['data'], [])
            name = plist[i]['name']
            for p in params:
                ptype, isyaml, key, value = p
                if isyaml:
                    data_name = isyaml if ptype == 'local' else 'all'
                    local_dict.set([i+1, name, data_name, key], value)
                elif ptype == 'local':
                    local_dict.set([i+1, name, key], value)
                else:
                    global_dict.set(['all', name, key], value)

        with open(fname, 'w') as stream:
            local_dict.get_dictionary().update(global_dict.get_dictionary())
            yu.dump_yaml(local_dict.get_dictionary(), stream)

    def __get_template_params(self, params, tlist, yaml=False):
        for key, value in params.iteritems():
            if key == 'yaml_file':
                yaml_dict = self._get_yaml_dict(value)
                for entry in yaml_dict.keys():
                    self.__get_template_params(
                            yaml_dict[entry]['params'], tlist, yaml=entry)
            value = pu.is_template_param(value)
            if value is not False:
                ptype, value = value
                isyaml = yaml if yaml else False
                tlist.append([ptype, isyaml, key, value])
        return tlist

    def _get_yaml_dict(self, yfile):
        from savu.plugins.loaders.yaml_converter import YamlConverter
        yaml = YamlConverter()
        template_check = pu.is_template_param(yfile)
        yfile = template_check[1] if template_check is not False else yfile
        yaml.parameters = {'yaml_file': yfile}
        return yaml.setup(template=True)

    def update_process_list(self, template):
        tdict = yu.read_yaml(template)
        del tdict['process_list']

        for plugin_no, entry in tdict.iteritems():
            plugin = entry.keys()[0]
            for key, value in entry.values()[0].iteritems():
                depth = self.dict_depth(value)
                if depth == 1:
                    self._set_param_for_template_loader_plugin(
                            plugin_no, key, value)
                elif depth == 0:
                    if plugin_no == 'all':
                        self._set_param_for_all_instances_of_a_plugin(
                                plugin, key, value)
                    else:
                        data = self._get_plugin_data_dict(str(plugin_no))
                        data[key] = value
                else:
                    raise Exception("Template key not recognised.")

    def dict_depth(self, d, depth=0):
        if not isinstance(d, dict) or not d:
            return depth
        return max(self.dict_depth(v, depth+1) for k, v in d.iteritems())

    def _set_param_for_all_instances_of_a_plugin(self, plugin, param, value):
        # find all plugins with this name and replace the param
        for p in self.plist.plugin_list:
            if p['name'] == plugin:
                p['data'][param] = value

    def _set_param_for_template_loader_plugin(self, plugin_no, data, value):
        param_key = value.keys()[0]
        param_val = value.values()[0]
        pdict = self._get_plugin_data_dict(str(plugin_no))['template_param']
        pdict = defaultdict(dict) if not pdict else pdict
        pdict[data][param_key] = param_val

    def _get_plugin_data_dict(self, plugin_no):
        """ input plugin_no as a string """
        plist = self.plist.plugin_list
        index = [plist[i]['pos'] for i in range(len(plist))]
        return plist[index.index(plugin_no)]['data']


class CitationInformation(object):
    """
    Descriptor of Citation Information for plugins
    """

    def __init__(self):
        super(CitationInformation, self).__init__()
        self.description = "Default Description"
        self.doi = "Default DOI"
        self.endnote = "Default Endnote"
        self.bibtex = "Default Bibtex"
        self.name = 'citation'

    def write(self, citation_group):
        citation_group.attrs[NX_CLASS] = 'NXcite'
        description_array = np.array([self.description])
        citation_group.create_dataset('description',
                                      description_array.shape,
                                      description_array.dtype,
                                      description_array)
        doi_array = np.array([self.doi])
        citation_group.create_dataset('doi',
                                      doi_array.shape,
                                      doi_array.dtype,
                                      doi_array)
        endnote_array = np.array([self.endnote])
        citation_group.create_dataset('endnote',
                                      endnote_array.shape,
                                      endnote_array.dtype,
                                      endnote_array)
        bibtex_array = np.array([self.bibtex])
        citation_group.create_dataset('bibtex',
                                      bibtex_array.shape,
                                      bibtex_array.dtype,
                                      bibtex_array)
