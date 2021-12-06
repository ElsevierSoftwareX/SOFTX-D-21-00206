"""
.. module:: statistics
   :platform: Unix
   :synopsis: Contains and processes statistics information for each plugin.

.. moduleauthor::Jacob Williamson <scientificsoftware@diamond.ac.uk>

"""

from savu.plugins.savers.utils.hdf5_utils import Hdf5Utils

import h5py as h5
import numpy as np
import os


class Statistics(object):
    has_setup = False

    def __init__(self, plugin_self):
        self.plugin = plugin_self
        self.plugin_name = plugin_self.name
        self.pad_dims = []
        self.stats = {'max': [], 'min': [], 'mean': [], 'standard_deviation': []}
        self.is_meta_data = True
        self._set_pattern_info()

    @classmethod
    def setup(cls, exp):
        """Sets up the statistics class for the whole experiment (only called once)"""
        cls.count = 1
        cls.data_stats = {}
        cls.volume_stats = {}
        n_plugins = len(exp.meta_data.plugin_list.plugin_list)
        for n in range(n_plugins):
            cls.data_stats[n + 1] = [None, None, None, None, None]
            cls.volume_stats[n + 1] = [None, None, None, None, None]
        cls.path = exp.meta_data['out_path']
        if cls.path[-1] == '/':
            cls.path = cls.path[0:-1]
        cls.path = f"{cls.path}/stats"
        if not os.path.exists(cls.path):
            os.mkdir(cls.path)
        cls.has_setup = True

    def set_slice_stats(self, slice1):
        """Appends arrays containing stats, with the stats parameters of the current slice"""
        if slice1 is not None:
            slice_num = self.plugin.pcount
            slice1 = self._de_list(slice1)
            slice1 = self._unpad_slice(slice1)
            self.stats['max'].append(slice1.max())
            self.stats['min'].append(slice1.min())
            self.stats['mean'].append(np.mean(slice1))
            self.stats['standard_deviation'].append(np.std(slice1))

    def get_slice_stats(self, stat, slice_num):
        return self.stats[stat][slice_num]

    def set_volume_stats(self):
        """Calculates volume-wide statistics from slice stats, and updates class-wide arrays with these values."""
        Statistics.count += 1
        p_num = Statistics.count
        Statistics.data_stats[p_num] = [None, None, None, None, None]
        Statistics.volume_stats[p_num] = [None, None, None, None, None]
        if len(self.stats['max']) != 0:
            if self.pattern in ['PROJECTION', 'SINOGRAM', 'TANGENTOGRAM']:
                Statistics.data_stats[p_num][0] = max(self.stats['max'])
                Statistics.data_stats[p_num][1] = min(self.stats['min'])
                Statistics.data_stats[p_num][2] = np.mean(self.stats['mean'])
                Statistics.data_stats[p_num][3] = np.mean(self.stats['standard_deviation'])
                Statistics.data_stats[p_num][4] = np.median(self.stats['standard_deviation'])
            elif self.pattern in ['VOLUME_XZ', 'VOLUME_XY', 'VOLUME_YZ']:
                Statistics.volume_stats[p_num][0] = max(self.stats['max'])
                Statistics.volume_stats[p_num][1] = min(self.stats['min'])
                Statistics.volume_stats[p_num][2] = np.mean(self.stats['mean'])
                Statistics.volume_stats[p_num][3] = np.mean(self.stats['standard_deviation'])
                Statistics.volume_stats[p_num][4] = np.median(self.stats['standard_deviation'])

        self._link_stats_to_datasets()
        slice_stats = np.array([self.stats['max'], self.stats['min'], self.stats['mean'],
                                self.stats['standard_deviation']])
        self._write_stats_to_file(slice_stats, p_num)

    def get_data_stats(self):
        return Statistics.data_stats

    def get_volume_stats(self):
        return Statistics.volume_stats

    def _set_pattern_info(self):
        """Gathers information about the pattern of the data in the current plugin."""
        out_datasets = self.plugin.get_out_datasets()
        try:
            self.pattern = self.plugin.parameters['pattern']
            if self.pattern == None:
                raise KeyError
        except KeyError:
            patterns = out_datasets[0].data_info["data_patterns"]
            for pattern in patterns:
                if 1 in patterns.get(pattern)["slice_dims"]:
                    self.pattern = pattern
                    break
        for dataset in out_datasets:
            if "METADATA" not in dataset.data_info.get("data_patterns"):
                self.is_meta_data = False

    def _link_stats_to_datasets(self):
        """Links the volume wide statistics to the output dataset(s)"""
        out_datasets = self.plugin.get_out_datasets()
        nOutput_datasets = self.plugin.nOutput_datasets()
        i = 1
        meta_name = "stats"
        if nOutput_datasets == 1:
            while meta_name in list(out_datasets[0].meta_data.get_dictionary().keys()):
                meta_name = f"stats{i}"
                i += 1
            out_datasets[0].meta_data.set([meta_name, "max"], max(self.stats['max']))
            out_datasets[0].meta_data.set([meta_name, "min"], min(self.stats['min']))
            out_datasets[0].meta_data.set([meta_name, "mean"], np.mean(self.stats['mean']))
            out_datasets[0].meta_data.set([meta_name, "mean_std_dev"], np.mean(self.stats['standard_deviation']))
            out_datasets[0].meta_data.set([meta_name, "median_std_dev"],
                                          np.median(self.stats['standard_deviation']))

    def _write_stats_to_file(self, slice_stats, p_num):
        """Writes slice-wide statistics to a h5 file"""
        path = Statistics.path
        filename = f"{path}/stats_p{p_num}_{self.plugin_name}.h5"
        slice_stats_dim = (slice_stats.shape[1],)
        self.hdf5 = Hdf5Utils(self.plugin.exp)
        with h5.File(filename, "a") as h5file:
            i = 1
            group_name = "/stats"
            while group_name in h5file:
                group_name = f"/stats{i}"
                i += 1
            group = h5file.create_group(group_name, track_order=None)
            max_ds = self.hdf5.create_dataset_nofill(group, "max", slice_stats_dim, slice_stats.dtype)
            min_ds = self.hdf5.create_dataset_nofill(group, "min", slice_stats_dim, slice_stats.dtype)
            mean_ds = self.hdf5.create_dataset_nofill(group, "mean", slice_stats_dim, slice_stats.dtype)
            standard_deviation_ds = self.hdf5.create_dataset_nofill(group, "standard_deviation",
                                                                    slice_stats_dim, slice_stats.dtype)
            max_ds[::] = slice_stats[0]
            min_ds[::] = slice_stats[1]
            mean_ds[::] = slice_stats[2]
            standard_deviation_ds[::] = slice_stats[3]

    def _unpad_slice(self, slice1):
        """If data is padded in the slice dimension, removes this pad"""
        out_datasets = self.plugin.get_out_datasets()
        if len(out_datasets) == 1:
            out_dataset = out_datasets[0]
        else:
            for dataset in out_datasets:
                if self.pattern in list(dataset.data_info.get(["data_patterns"]).keys()):
                    out_dataset = dataset
                    break
        slice_dims = out_dataset.get_slice_dimensions()
        if self.plugin.pcount == 0:
            self.slice_list, self.pad = self._get_unpadded_slice_list(slice1, slice_dims)
        if self.pad:
            for slice_dim in slice_dims:
                temp_slice = np.swapaxes(slice1, 0, slice_dim)
                temp_slice = temp_slice[self.slice_list[slice_dim]]
                slice1 = np.swapaxes(temp_slice, 0, slice_dim)
        return slice1

    def _get_unpadded_slice_list(self, slice1, slice_dims):
        """Creates slice object(s) for un-padded slices in the slice dimension(s)"""
        slice_list = list(self.plugin.slice_list[0])
        pad = False
        if len(slice_list) == len(slice1.shape):
            for i in slice_dims:
                slice_width = self.plugin.slice_list[0][i].stop - self.plugin.slice_list[0][i].start
                if slice_width != slice1.shape[i]:
                    pad = True
                    pad_width = (slice1.shape[i] - slice_width) // 2  # Assuming symmetrical padding
                    slice_list[i] = slice(pad_width, pad_width + 1, 1)
            return tuple(slice_list), pad
        else:
            return self.plugin.slice_list[0], pad

    def _de_list(self, slice1):
        """If the slice is in a list, remove it from that list"""
        if type(slice1) == list:
            if len(slice1) != 0:
                slice1 = slice1[0]
                slice1 = self._de_list(slice1)
        return slice1

    @classmethod
    def post_chain(cls):
        print(cls.data_stats)
        print(cls.volume_stats)
        cls.has_setup = False
