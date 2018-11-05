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

from qgis.PyQt.QtCore import pyqtSignal
from processing.gui.InputLayerSelectorPanel import InputLayerSelectorPanel
from processing.core.parameters import ParameterRaster

class CustomInputLayerSelectorPanel(InputLayerSelectorPanel):
    """
    This class add a signal of the class InputLayerSelectorPanel
    With this, we can change/synchronize the QWidget 'QComboBox' 
    with the alg.param a.k.a INPUT_LAYER
    """
    currentIndexChanged = pyqtSignal()
    
    def __init__(self, options, param):
        """constructor"""
        super(CustomInputLayerSelectorPanel, self).__init__(options, param)

        # Connection of QComboBox signal with this signal 
        self.cmbText.currentIndexChanged.connect(lambda: self.currentIndexChanged.emit())
        



