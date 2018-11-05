# -*- coding: utf-8 -*-

#####################################################################################################
# Chloe - landscape metrics
#
# Copyright 2018 URCAUE-Nouvelle Aquitaine
# Author(s) J-C. Naud, O. Bedel - Alkante (http://www.alkante.com) ;
#           H. Boussard - INRA UMR BAGAP (https://www6.rennes.inra.fr/sad)
# 
# Created on Mon Oct 22 2018
# This file is part of Chloe - landscape metrics.
# 
# Chloe - landscape metrics is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Chloe - landscape metrics is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Chloe - landscape metrics.  If not, see <http://www.gnu.org/licenses/>.
#####################################################################################################

from processing.core.AlgorithmProvider import AlgorithmProvider
from processing.core.ProcessingConfig  import Setting, ProcessingConfig

# Group : generate ascii grid
from .algorithm.from_csv_algorithm       import FromCSVAlgorithm
from .algorithm.from_shapefile_algorithm import FromShapefileAlgorithm

# Group : util
from .algorithm.search_and_replace_algorithm  import SearchAndReplaceAlgorithm
from .algorithm.overlay_algorithm             import OverlayAlgorithm
from .algorithm.distance_algorithm            import DistanceAlgorithm
from .algorithm.classification_algorithm      import ClassificationAlgorithm
from .algorithm.cluster_algorithm             import ClusterAlgorithm
#from .algorithm.combine_algorithm             import CombineAlgorithm
from .algorithm.filter_algorithm              import FilterAlgorithm

# Group : lanscape metrics
from .algorithm.map_algorithm                 import MapAlgorithm
from .algorithm.grid_algorithm                import GridAlgorithm
from .algorithm.grid_multi_algorithm          import GridMultiAlgorithm
from .algorithm.sliding_algorithm             import SlidingAlgorithm
from .algorithm.sliding_multi_algorithm       import SlidingMultiAlgorithm
from .algorithm.selected_algorithm            import SelectedAlgorithm
from .algorithm.selected_multi_algorithm      import SelectedMultiAlgorithm

# tooling
from PyQt4.QtGui import QIcon
import os
from .ChloeUtils import ChloeUtils


class ChloeProvider(AlgorithmProvider):
    """
    Class provider used to :
    - provide generale parameter (can be modified by users in MENU->Processing->Options)
    """
    #MY_DUMMY_SETTING = 'MY_DUMMY_SETTING'
	
    def __init__(self):
        AlgorithmProvider.__init__(self)

        # Deactivate provider by defaults
        self.activate = False

        # List of algorithms loaded
        self.alglist = [
          FromCSVAlgorithm(),           # Group : generate ascii grid  v1   
          FromShapefileAlgorithm(),     # //                           v1
          SearchAndReplaceAlgorithm(),  # Group : util                 v1
          OverlayAlgorithm(),           # //                           v1
          DistanceAlgorithm(),          # //                           v1
          ClassificationAlgorithm(),    # //                           v1
          ClusterAlgorithm(),           # //                           v1
          #CombineAlgorithm(),           # // (Not implemented)
          FilterAlgorithm(),            # //                           v1
          MapAlgorithm(),               # // landscape metric          v1
          GridAlgorithm(),              # //                           v1
          GridMultiAlgorithm(),         # //                           v1
          SlidingAlgorithm(),           # //                           v1
          SlidingMultiAlgorithm(),      # //                           v1
          SelectedAlgorithm(),           # //                           v1
          SelectedMultiAlgorithm()      # //                           v1
        ]

        for alg in self.alglist:
            alg.provider = self


    def initializeSettings(self):
        """In this method we add settings needed to configure our
        provider.

        Do not forget to call the parent method, since it takes care
        or automatically adding a setting for activating or
        deactivating the algorithms in the provider.
        """
        AlgorithmProvider.initializeSettings(self)
			
        ProcessingConfig.addSetting(Setting(self.getDescription(),
            ChloeUtils.JAVA,
            'Path java exe', ''))

    def unload(self):
        """Setting should be removed here, so they do not appear anymore
        when the plugin is unloaded.
        """
        AlgorithmProvider.unload(self)
        ProcessingConfig.removeSetting(
            ChloeUtils.JAVA)

    def getName(self):
        """This is the name that will appear on the toolbox group.

        It is also used to create the command line name of all the
        algorithms from this provider.
        """
        return 'Chloe'

    def getDescription(self):
        """This is the provired full name.
        """
        return self.tr('Chloe - Landscape metrics')

    def getIcon(self):
        """We return the default icon.
        """
        return QIcon(os.path.dirname(__file__)+os.sep+"images"+os.sep+"chloe_icon.png")

    def _loadAlgorithms(self):
        """Here we fill the list of algorithms in self.algs.

        This method is called whenever the list of algorithms should
        be updated. If the list of algorithms can change (for instance,
        if it contains algorithms from user-defined scripts and a new
        script might have been added), you should create the list again
        here.

        In this case, since the list is always the same, we assign from
        the pre-made list. This assignment has to be done in this method
        even if the list does not change, since the self.algs list is
        cleared before calling this method.
        """
        self.algs = self.alglist

    def getSupportedOutputRasterLayerExtensions(self):
        return ['asc']

