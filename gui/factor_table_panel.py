# -*- coding: utf-8 -*-

"""
*********************************************************************************************
    factor_table_panel.py
    ---------------------
        
        Widget used in the Combine Algorithm. Sets the input rasters names and setup the combination formula.
        Date                 : May 2019

        email                : daan.guillerme at fdc22.com / hugues.boussard at inra.fr
*********************************************************************************************

"""

__author__ = 'Daan Guillerme'
__date__ = 'June 2019'
__copyright__ = '(C) 2019, Daan Guillerme'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QMenu, QAction, QInputDialog, QListWidget, QListWidgetItem, QDialog,QMessageBox
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

    def __init__(self, dialog, alg, default=None, inputMatrix=None): #
        super(FactorTablePanel, self).__init__(None)
        self.setupUi(self) 
        self.dialog = dialog
        self.alg = alg
        self.inputMatrix = inputMatrix
        self.resultCombination = ''
        self.resultMatrix = ''
        if hasattr(self.leText, 'setPlaceholderText'):
            self.leText.setPlaceholderText('Combination Formula')
            self.leText.setReadOnly(True)
        self.btnSelect.clicked.connect(self.selectValues) # Bouton "..."

    def selectValues(self):
        """Values selector
            return item (duck typing)
        """
        # Get initial value
        text = self.leText.text()
        parameters = {}
        listElement = []
        # create array to fill the factor table widget
 
        if (self.inputMatrix!=None):
            listLayers = self.dialog.mainWidget().wrappers[self.alg.INPUTS_MATRIX].value()
            
            if len(listLayers) == 0:
                QMessageBox.critical(self, self.tr('Select rasters'),self.tr('No rasters selected'))
                return
            else:
                i = 1
                for l in listLayers:
                    lyrName = ChloeUtils.deduceLayerName(l)
                    # check if listLayers items are strings or layer objects
                    if type(l) is str:
                        path = str(l)
                    else:
                        path = str(l.dataProvider().dataSourceUri())
                    listElement.append(('m'+str(i), lyrName, path))
                    i+=1
        # Dialog list check box
        dial = FactorInputDialog(self.tr("Combine"),listElement)
        #Returns two strings
        self.resultMatrix, self.resultCombination = dial.run(text)
        # # result
        if self.resultMatrix and self.resultCombination:
            self.leText.setText(self.resultCombination)

    def getValue(self):

        # Return one string combining the raster matrix used and the combination formula (separated by .__.). Split the returned value on .__. to get two values : matrix used and combination formula
        return unicode(self.resultMatrix) + '.__.' + unicode(self.resultCombination)

    def text(self):
        return self.leText

    def setValue(self, value):
        self.leText.setText(value)

    def setText(self, value):
        pass