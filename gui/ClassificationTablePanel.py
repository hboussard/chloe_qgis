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

import os

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QMenu, QAction, QInputDialog, QListWidget, QListWidgetItem, QDialog
from qgis.PyQt.QtGui import QCursor

from qgis.gui import QgsMessageBar, QgsExpressionBuilderDialog, QgsFileWidget
from qgis.core import QgsRasterLayer, QgsVectorLayer, QgsApplication
from qgis.utils import iface

from processing.gui.RectangleMapTool import RectangleMapTool
from processing.core.parameters import ParameterRaster
from processing.core.parameters import ParameterVector
from processing.core.parameters import ParameterMultipleInput
from processing.core.ProcessingConfig import ProcessingConfig
from processing.tools import dataobjects

from processing.gui.ListMultiselectWidget import ListMultiSelectWidget


from .components.TableInputDialog import TableInputDialog
import math

#from PyQt4.QtGui import

pluginPath = str(QgsApplication.pkgDataPath())
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'python','plugins','processing','ui', 'widgetBaseSelector.ui'))


class ClassificationTablePanel(BASE, WIDGET):

    def __init__(self, dialog, alg, default=None):
        super(ClassificationTablePanel, self).__init__(None)
        self.setupUi(self) 
        self.dialog = dialog
        self.params = alg.parameters
        if hasattr(self.leText, 'setPlaceholderText'):
            self.leText.setPlaceholderText('Domain1, class1;Domain2, class2')
        
        self.btnSelect.clicked.connect(self.selectValues) # Bouton "..."


    def selectValues(self):
        """Values selector
            return item (duck typing)
        """
        # Get initial value
        text = self.leText.text()
        values = ""

        # Dialog list check box
        dial = TableInputDialog(self.tr("Fill the class mapping table"))
        result = dial.run(text)
    
        # result
        if result:
            self.leText.setText(result)


    def getValue(self):
        return unicode(self.leText.text())

    def setExtentFromString(self, s):
        self.leText.setText(s)

    def text(self):
        return self.leText

