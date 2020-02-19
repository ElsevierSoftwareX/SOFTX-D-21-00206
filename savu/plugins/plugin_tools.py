from savu.data.meta_data import MetaData
import savu.plugins.docstring_parser as doc
# from dataclasses import dataclass
from collections import OrderedDict


class PluginCitations(object):
    """ Get this citation dictionary so get_dictionary of the metadata type
        should return a dictionary of all the citation info as taken from docstring
        """
    def __init__(self):
        super(PluginCitations, self).__init__()
        self.cite = MetaData()
        self.set_cite()

    def set_cite(self):
        self.cite.set('bibtex', self.get_bibtex.__doc__)
        self.cite.set('endnote', self.get_endnote.__doc__)

    def get_bibtex(self):
        pass

    def get_endnote(self):
        pass

class PluginParameters(object):
    """ Get this parameter dictionary so get_dictionary of the metadata type
    should return a dictionary of all the parameters as taken from docstring
    """
    def __init__(self):
        super(PluginParameters, self).__init__()
        self.param = MetaData(ordered=True)
        self.set_plugin_parameters()

    def set_plugin_parameters(self):
        # function to get plugin parameters

        yaml_text = self.define_parameters.__doc__
        all_params, verbose = doc.load_yaml_doc(yaml_text)
        for p_name, p_value in all_params.items():
            self.param.set(p_name, p_value)
            #vis = p_value['visibility']
            #dtype = p_value['dtype']
            #dep = p_value['dependency'] \
            #    if 'dependency' in all_params.keys() else None
            #params[p_name] = Parameter(vis, dtype, dep)

    def define_parameters(self):
        pass

    """
    @dataclass
    class Parameter:
        ''' Descriptor of Parameter Information for plugins
        '''
        visibility: int
        datatype: specific_type
        description: str
        default: int
        Options: Optional[[str]]
        dependency: Optional[]

        def _get_param(self):
            param_dict = {}
            param_dict['visibility'] = self.visibility
            param_dict['type'] = self.dtype
            param_dict['description'] = self.description
            # and the rest
            return param_dict
    """
class PluginDocumentation(object):
    """ Get this documentation
     diction so get_dictionary of the metadata type
        should return a dictionary of all the parameters as taken from docstring
    """
    def __init__(self):
        super(PluginDocumentation, self).__init__()
        self.doc = MetaData()
        self.doc_set()

    def doc_set(self):
        self.doc.set('verbose', self.__doc__)

class PluginTools(PluginCitations, PluginParameters, PluginDocumentation):

    def __init__(self, plugin_tools=MetaData()):
        self.plugin_tools = plugin_tools
        super(PluginTools, self).__init__()
        self.plugin_tools.append('cite', self.cite.get_dictionary())
        self.plugin_tools.append('param', self.param.get_dictionary())
        self.plugin_tools.append('doc', self.doc.get_dictionary())




