# -*- coding: utf-8 -*-

"""
***************************************************************************
    MultipleInputPanel.py
    ---------------------
    Date                 : January 2017

        email                : hugues.boussard at inra.fr
***************************************************************************

"""


__author__ = 'Jean-Charles Naud'
__date__ = 'January 2017'


# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

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
