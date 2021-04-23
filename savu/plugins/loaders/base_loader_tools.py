from savu.plugins.plugin_tools import PluginTools

class BaseLoaderTools(PluginTools):
    """
    A base class for loader plugins. A base plugin from which all data loader
    plugins should inherit.
    """

    def define_parameters(self):
        """
        preview:
              visibility: basic
              dtype: preview
              description: A slice list of required frames.
              default: []
        in_datasets:
              # not inherited and not needed
              visibility: not
              dtype: [list[],list[str]]
              description: Create a list of the dataset(s) to process
              default: []
        out_datasets:
              # not inherited and not needed
              visibility: not
              dtype: [list[],list[str]]
              description: Create a list of the dataset(s) to create
              default: []

        """