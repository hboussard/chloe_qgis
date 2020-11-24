# -*- coding: utf-8 -*-

"""
***************************************************************************
    CSVFieldSelectionPanel.py
    ---------------------
    Date                 : August 2017

        email                : hugues.boussard at inra.fr
***************************************************************************

"""

from builtins import str
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
#from processing.core.parameters import ParameterRaster
#from processing.core.parameters import ParameterVector
#from processing.core.parameters import ParameterMultipleInput
from qgis.core import (
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterMultipleLayers
)
from processing.core.ProcessingConfig import ProcessingConfig
from processing.tools import dataobjects

from processing.gui.ListMultiselectWidget import ListMultiSelectWidget



from .components.DialListCheckBox import DialListCheckBox
import math
import re
from processing.tools.dataobjects import createContext
#from qgis.PyQt.QtGui import

pluginPath = str(QgsApplication.pkgDataPath())
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'python','plugins','processing','ui', 'widgetBaseSelector.ui'))


class CSVFieldSelectionPanel(BASE, WIDGET):

    def __init__(self, dialog, alg, default=None):
        super(CSVFieldSelectionPanel, self).__init__(None)
        self.setupUi(self)
        self.dialog = dialog
        #self.params = alg.parameters
        self.alg = alg
        if hasattr(self.leText, 'setPlaceholderText'):
            self.leText.setPlaceholderText('Field 1;Field 2')

        self.btnSelect.clicked.connect(self.selectValues) # Bouton "..."


    def selectValues(self):
        """Values selector
            return item (duck typing)
        """

        # Get initial value
        text = self.leText.text()
        texts = text.split(';')
        values = ""
        #p = self.alg.getParameterValue("INPUT_FILE_CSV")
        parameters = {}
        
        #parameters[self.alg.INPUT_FILE_CSV] = self.dialog.mainWidget().wrappers[self.alg.INPUT_FILE_CSV].value() --> if Qgs
        parameters[self.alg.INPUT_FILE_CSV] = self.dialog.mainWidget().wrappers[self.alg.INPUT_FILE_CSV].parameterValue() 
        p = self.dialog.mainWidget().wrappers[ self.alg.INPUT_FILE_CSV].parameterValue()
        
        # p is a QgsProcessingFeatureSourceDefinition
        #print(str(self.dialog.mainWidget().wrappers[ self.alg.INPUT_FILE_CSV]))
        #context = createContext()
        #p = self.alg.parameterAsString(parameters, self.alg.INPUT_FILE_CSV, context)

        #f_input = p.source.asExpression().strip("'")
        if p:
            f_input = p.strip("'")
        else:
            f_input = None
        #print(f_input)
        if f_input:
            with open(f_input,'r') as f:
                line = f.readline()
                line = line.rstrip('\n') # Delete \n
                line = line.replace('"','') # Delete "
                line = line.replace("'",'') # Delete '
                fields = line.split(';')
                fields.remove('X')       # remove "X" field
                fields.remove('Y')       # remove "Y" field


            # Dialog list check box
            dial = DialListCheckBox(values=fields,checked_values=texts)
            result = dial.run()
        else:
            result = ""
        # result
        self.leText.setText(result)


    def getValue(self):
        return str(self.leText.text())

    def setExtentFromString(self, s):
        self.leText.setText(s)

    def text(self):
        return self.leText

    def setValue(self, value):
        self.leText.setText(value)

    def setText(self, value):
        pass
