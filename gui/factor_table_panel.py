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
from qgis.PyQt.QtWidgets import QMessageBox

from qgis.core import QgsApplication, QgsProject

from .components.FactorInputDialog import FactorInputDialog

import re

from ..ChloeUtils import *

pluginPath = str(QgsApplication.pkgDataPath())
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'python', 'plugins', 'processing', 'ui', 'widgetBaseSelector.ui'))


class FactorTablePanel(BASE, WIDGET):

    # standardGui => Flag used when in modeler or batch mode
    def __init__(self, dialog, alg, default=None, inputMatrix=None):
        super(FactorTablePanel, self).__init__(None)
        self.setupUi(self)
        self.dialog = dialog
        self.alg = alg
        self.inputMatrix = inputMatrix
        self.resultCombination = ''
        self.resultMatrix = ''
        if hasattr(self.leText, 'setPlaceholderText'):
            self.leText.setPlaceholderText(self.tr('Combination Formula'))
        self.leText.setReadOnly(True)
        self.btnSelect.clicked.connect(self.selectValues)  # Bouton "...

    def selectValues(self):
        """Values selector
            return item (duck typing)
        """
        # Get initial value
        FormulaText = self.leText.text()

        listElement = []
        # create an array to fill the factor table widget

        if self.inputMatrix is not None:

            listLayers = self.dialog.mainWidget(
            ).wrappers[self.alg.INPUTS_MATRIX].widgetValue()

            if listLayers is None:
                return

            if len(listLayers) == 0:
                QMessageBox.critical(self, self.tr(
                    'Select rasters'), self.tr('No rasters selected'))
                return
            else:
                i = 1
                for l in listLayers:
                    # check if listLayers items are strings
                    if type(l) is str:
                        # if raster loaded in QgsProject.instance()
                        if re.match(r"^[a-zA-Z0-9_]+$", l):
                            # get raster layer object
                            selectedLayer = QgsProject.instance().mapLayer(l)

                            path = selectedLayer.dataProvider().dataSourceUri()
                            lyrName = ChloeUtils.deduceLayerName(selectedLayer)

                        else:
                            path = str(l)
                            lyrName = ChloeUtils.deduceLayerName(l)

                    listElement.append(('m'+str(i), lyrName, path))
                    i += 1
        # Dialog list check box
        dial = FactorInputDialog(self.tr("Combine"), listElement)
        # Returns two strings
        self.resultMatrix, self.resultCombination = dial.run(FormulaText)
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

    def resetFormula(self):
        self.leText.setText('')
