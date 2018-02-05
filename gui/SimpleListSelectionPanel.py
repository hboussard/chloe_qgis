# -*- coding: utf-8 -*-

"""
***************************************************************************
    ListSelectionPanel.py
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
from processing.core.parameters import ParameterRaster
from processing.core.parameters import ParameterVector
from processing.core.parameters import ParameterMultipleInput
from processing.core.ProcessingConfig import ProcessingConfig
from processing.tools import dataobjects

from processing.gui.ListMultiselectWidget import ListMultiSelectWidget



from .components.DialListCheckBox import DialListCheckBox
import math

from PyQt4 import QtGui

pluginPath = os.path.split(os.path.dirname(__file__))[0]
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'gui', 'ui', 'WgtListSelector.ui'))


class SimpleListSelectionPanel(BASE, WIDGET):

    def __init__(self, dialog, alg, default=None):
        super(SimpleListSelectionPanel, self).__init__(None)
        self.setupUi(self) 
        self.dialog = dialog
        self.params = alg.parameters
        self.listSrc.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection) # Activer la multi selection
        self.listDest.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection) # Activer la multi selection



    def getValue(self):
        return unicode(self.lineEdit.text())

    def setExtentFromString(self, s):
        self.lineEdit.setText(s)


    def text(self):
        return self.lineEdit.text()

