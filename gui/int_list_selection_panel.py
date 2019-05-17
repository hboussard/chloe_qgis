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
from qgis.PyQt.QtWidgets import QMenu, QAction, QInputDialog, QListWidget, QListWidgetItem, QDialog, QAbstractItemView
from processing.gui.ListMultiselectWidget import ListMultiSelectWidget
import math


pluginPath = os.path.split(os.path.dirname(__file__))[0]
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'gui', 'ui', 'IntListSelector.ui'))


class IntListSelectionPanel(BASE, WIDGET):

    def __init__(self, dialog, alg, initialValue=None):
        super(IntListSelectionPanel, self).__init__(None)
        self.setupUi(self) 
        self.dialog = dialog
        self.alg = alg
        self.initialValue = initialValue
        self.window_sizes_selected = set()
        self.initGui()
        

    def initGui(self):
        self.listDest.setSelectionMode(QAbstractItemView.ExtendedSelection) # Activer la multi selection
        self.lineEdit.setReadOnly(True)
        self.sbInt.setValue(self.initialValue)
        # connecting signals
        self.pbRight.clicked.connect(self.addIntInListDst)
        self.pbRemove.clicked.connect(self.removeIntInListDst)
        self.pbClear.clicked.connect(self.removeIntAllListDst)

    #@pyqtSlot(str)
    def addIntInListDst(self):
        """Add grid size integer in listSrc"""
        int_value = self.sbInt.value()
        self.window_sizes_selected.add(str(self.sbInt.value()))
        self.listDest.clear()
        self.listDest.addItems(list(self.window_sizes_selected))
        self.updateWindowsSizesLigneEdit()

    #@pyqtSlot()
    def removeIntAllListDst(self):
        """Remove all grid sizes in listDest"""
        self.listDest.clear()
        self.window_sizes_selected = set()
        self.updateWindowsSizesLigneEdit()

    #@pyqtSlot(str)
    def removeIntInListDst(self):
        """Remove grid sizes selected in listDest"""
        selected = self.listDest.selectedItems()
        for lw in selected:
            self.window_sizes_selected.remove(lw.text())
        self.listDest.clear()
        self.listDest.addItems(list(self.window_sizes_selected))
        self.updateWindowsSizesLigneEdit()

    def updateWindowsSizesLigneEdit(self):
        """update Gris sizes (QLineEdit in readOnly mode)"""
        window_sizes = list(self.window_sizes_selected)
        if window_sizes:
            self.lineEdit.setText(";".join(window_sizes))
        else:
            self.lineEdit.setText("") 

    def getValue(self):
        return unicode(self.lineEdit.text())

    def setExtentFromString(self, s):
        self.lineEdit.setText(s)

    def text(self):
        return self.lineEdit.text()


