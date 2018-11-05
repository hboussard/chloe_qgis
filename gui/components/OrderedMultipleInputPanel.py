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
from qgis.PyQt.QtCore import pyqtSignal
from qgis.core import QgsApplication

from processing.gui.MultipleInputDialog import MultipleInputDialog
from processing.gui.MultipleFileInputDialog import MultipleFileInputDialog

from .OrderedMultipleInputDialog import OrderedMultipleInputDialog
#pluginPath = os.path.split(os.path.dirname(__file__))[0]
pluginPath = str(QgsApplication.pkgDataPath())
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'python','plugins','processing','ui', 'widgetBaseSelector.ui'))


class OrderedMultipleInputPanel(BASE, WIDGET):

    selectionChanged = pyqtSignal()

    def __init__(self, options=None, datatype=None):
        super(OrderedMultipleInputPanel, self).__init__(None)
        self.setupUi(self)

        self.leText.setEnabled(False)
        self.leText.setText(self.tr('0 elements selected'))

        self.btnSelect.clicked.connect(self.showSelectionDialog)

        self.options = options
        self.datatype = datatype
        self.selectedoptions = []

    def setSelectedItems(self, selected):
        # No checking is performed!
        self.selectedoptions = selected
        self.leText.setText(
            self.tr('%d elements selected') % len(self.selectedoptions))

    def showSelectionDialog(self):
        if self.datatype is None:
            dlg = OrderedMultipleInputDialog(self.options, self.selectedoptions)
        else:
            dlg = MultipleFileInputDialog(self.selectedoptions)
        dlg.exec_()
        

            
        if dlg.selectedoptions is not None:
            self.selectedoptions = dlg.selectedoptions
            self.leText.setText(
                self.tr('%d elements selected') % len(self.selectedoptions))
            self.selectionChanged.emit()

    def updateForOptions(self, options):
        selectedoptions = []
        selected = [self.options[i] for i in self.selectedoptions]
        for sel in selected:
            try:
                idx = options.index(sel)
                selectedoptions.append(idx)
            except ValueError:
                pass
        self.options = options
        self.setSelectedItems(selectedoptions)
