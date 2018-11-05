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
from processing.gui.FileSelectionPanel import FileSelectionPanel


class CustomFileSelectionPanel(FileSelectionPanel):
    """
    This class add a signal of the class FileSelectionPanel
    With this, we can change/synchronize the QWidget 'QLineEdit' 
    with the alg.param a.k.a INPUT_FILE_*
    """
    textChanged = pyqtSignal()
    
    def __init__(self, isFolder, ext=None):
        """constructor"""
        super(CustomFileSelectionPanel, self).__init__(isFolder, ext)

        # Connection of QLineEdit signal with this signal 
        self.leText.textChanged.connect(lambda: self.textChanged.emit())



