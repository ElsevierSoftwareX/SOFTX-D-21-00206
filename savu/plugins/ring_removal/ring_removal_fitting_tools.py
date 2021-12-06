from savu.plugins.plugin_tools import PluginTools

class RingRemovalFittingTools(PluginTools):
    """Fitting-based method working in the sinogram space to remove ring
    artifacts.
    """
    def define_parameters(self):
        """
        sigmax:
            visibility: basic
            dtype: int
            description: Sigma of the Gaussian window in x-direction which
              controls the strength of the removal. Smaller is stronger.
            default: 5
        sigmay:
            visibility: intermediate
            dtype: int
            description: Sigma of the Gaussian window in y-direction.
            default: 30
        order:
            visibility: basic
            dtype: int
            description: polynomial fit order.
            default: 2
        """

    def citation(self):
        """
        The code of ring removal is the implementation of the work of
        Nghia T. Vo et al. taken from algorithm 1 in this paper
        bibtex:
                @article{vo2018superior,
                title = {Superior techniques for eliminating ring artifacts in X-ray micro-tomography},
                author={Vo, Nghia T and Atwood, Robert C and Drakopoulos, Michael},
                journal={Optics express},
                volume={26},
                number={22},
                pages={28396--28412},
                year={2018},
                publisher={Optical Society of America}}
        endnote:
                %0 Journal Article
                %T Superior techniques for eliminating ring artifacts in X-ray micro-tomography
                %A Vo, Nghia T
                %A Atwood, Robert C
                %A Drakopoulos, Michael
                %J Optics express
                %V 26
                %N 22
                %P 28396-28412
                %@ 1094-4087
                %D 2018
                %I Optical Society of America
        doi: "10.1364/OE.26.028396"
        """