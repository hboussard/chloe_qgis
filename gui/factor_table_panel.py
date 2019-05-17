# -*- coding: utf-8 -*-

"""
***************************************************************************
    ClassificationTablePanel.py
    ---------------------
    Date                 : August 2017

        email                : hugues.boussard at inra.fr
***************************************************************************

"""

__author__ = 'Jean-Charles Naud'
__date__ = 'August 2017'
__copyright__ = '(C) 2017, Jean-Charles Naud'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QMenu, QAction, QInputDialog, QListWidget, QListWidgetItem, QDialog
from qgis.PyQt.QtGui import QCursor

from qgis.gui import QgsMessageBar, QgsExpressionBuilderDialog, QgsFileWidget
from qgis.core import QgsRasterLayer, QgsVectorLayer, QgsApplication
from qgis.utils import iface

from processing.gui.RectangleMapTool import RectangleMapTool
from processing.tools import dataobjects

from processing.gui.ListMultiselectWidget import ListMultiSelectWidget


from .components.FactorInputDialog import FactorInputDialog
import math

from ..ChloeUtils import *
#from PyQt4.QtGui import

pluginPath = str(QgsApplication.pkgDataPath())
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'python','plugins','processing','ui', 'widgetBaseSelector.ui'))


class FactorTablePanel(BASE, WIDGET):

    def __init__(self, dialog, alg, default=None, inputMatrix=None): #,data = None
        super(FactorTablePanel, self).__init__(None)
        self.setupUi(self) 
        self.dialog = dialog
        self.alg = alg
        self.inputMatrix = inputMatrix
        #self.data = data
        if hasattr(self.leText, 'setPlaceholderText'):
            self.leText.setPlaceholderText('Factor expression')
        
        self.btnSelect.clicked.connect(self.selectValues) # Bouton "..."


    def selectValues(self):
        """Values selector
            return item (duck typing)
        """
        # Get initial value
        text = self.leText.text()
        values = ""

        parameters = {}
       # p = self.dialog.mainWidget().wrappers[self.rasterLayerParamName].value()
        listElem = []
        if (self.inputMatrix!=None):
            listLayer = self.dialog.mainWidget().wrappers[ self.alg.INPUTS_MATRIX].value()
            i=1
            for l in listLayer:
                listElem.append(('m'+str(i),  ChloeUtils.deduceLayerName(l) + '(' + l.dataProvider().dataSourceUri() + ')'))
                i = i + 1
        
        # Dialog list check box
        dial = FactorInputDialog(self.tr("Test factor expression"), listElem)
        result = dial.run(text)
    
        # result
        if result:
            self.leText.setText(result)

    def getValue(self):
        return unicode(self.leText.text())

    def text(self):
        return self.leText

    def setValue(self, value):
        self.leText.setText(value)

    def setText(self, value):
        pass