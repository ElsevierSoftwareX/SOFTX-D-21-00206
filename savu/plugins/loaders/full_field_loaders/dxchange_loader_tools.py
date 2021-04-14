from savu.plugins.plugin_tools import PluginTools

class DxchangeLoaderTools(PluginTools):
    """A class to load tomography data from a hdf5 file
    """
    def define_parameters(self):
        """
        data_path:
            visibility: basic
            dtype: hdf5path
            description: Path to the data.
            default: 'exchange/data'
        dark:
            visibility: intermediate
            dtype: list[hdf5path, int]
            description: Dark data path and scale
            default: "['exchange/data_dark', 1]"
        flat:
            visibility: intermediate
            dtype: list[hdf5path, int]
            description: Flat data path and scale value.
            default: "['exchange/data_white', 1]"
        logfile:
            visibility: intermediate
            dtype: filepath
            description: Path to the log file.
            default: None
        angles:
            visibility: hidden
            dtype: list
            description: Angles list
            default: '[1,2,3]'
        image_key_path:
            visibility: advanced
            dtype: hdf5path
            description: Not required.
            default: None

        """
