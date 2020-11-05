# -*- coding: utf-8 -*-

"""
***************************************************************************
    ValuesSelectionPanel.py
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
import warnings

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
from processing.core.ProcessingConfig import ProcessingConfig
from processing.tools import dataobjects
from processing.tools.dataobjects import createContext

from processing.gui.ListMultiselectWidget import ListMultiSelectWidget



from .components.DialListCheckBox import DialListCheckBox

from osgeo import gdal
import numpy as np
import math

#from PyQt4.QtGui import

pluginPath = str(QgsApplication.pkgDataPath())
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    WIDGET, BASE = uic.loadUiType(
        os.path.join(pluginPath, 'python','plugins','processing','ui', 'widgetBaseSelector.ui'))


class ValuesSelectionPanel(BASE, WIDGET):

    def __init__(self, dialog, alg, default=None, rasterLayerParamName='INPUT_ASC', batchGui=False):
        super(ValuesSelectionPanel, self).__init__(None)
        self.setupUi(self) 
        self.dialog = dialog
        self.alg = alg
        self.batchGui = batchGui
        # getting rasterLayer param from its name
        self.rasterLayerParamName = rasterLayerParamName
        
        if hasattr(self.leText, 'setPlaceholderText'):
            self.leText.setPlaceholderText('1;2;5;6')
        

        self.btnSelect.clicked.connect(self.selectRangeValues) # Bouton "..."


    def selectRangeValues(self):
        """Ranges Values selector
            return item (duck typing)
        """
        # Get initial value
        previous_text = self.leText.text()
        try:
            int_checked_values =list(map(int, previous_text.split(';')))
        except:
            int_checked_values = []
        values = ""

        try:
            parameters = {}
            if self.batchGui:
                p = self.dialog.mainWidget().wrappers[0][0].value()
            else:
                p = self.dialog.mainWidget().wrappers[self.rasterLayerParamName].value()

            if p is None:
                return
            elif isinstance(p, QgsRasterLayer): 
                f_input = p.dataProvider().dataSourceUri()
            elif isinstance(p,str):
                f_input = p
            else:
                f_input = str(p)   
            #print(f_input)
            
            # === Test algorithm
            ds = gdal.Open(f_input)                 # DataSet
            band =  ds.GetRasterBand(1)             # -> band
            array = np.array(band.ReadAsArray())    # -> matrice values
            values = np.unique(array)   
            values_and_nodata = np.insert(values, 0, band.GetNoDataValue()) # Add nodata values in numpy array
            int_values_and_nodata = np.unique([int(math.floor(x)) for x in values_and_nodata ])

            # Dialog list check box
            dial = DialListCheckBox(int_values_and_nodata,int_checked_values)
            result = dial.run()
        except:
            result=""
            raise
        # result
        self.leText.setText(result)

    def getValue(self):
        return str(self.leText.text())

    def text(self):
        return self.leText

    def setValue(self, value):
        self.leText.setText(value)

    def setText(self, value):
        pass
