# -*- coding: utf-8 -*-

"""
***************************************************************************
    MultipleInputDialog.py
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
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QDialog, QAbstractItemView, QPushButton, QDialogButtonBox
from qgis.PyQt.QtGui import QStandardItemModel, QStandardItem


from qgis.core import QgsApplication

pluginPath = os.path.split(os.path.dirname(__file__))[0]
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'DlgAbout.ui'))

class AboutDialog(BASE, WIDGET):

    def __init__(self):
        super(AboutDialog, self).__init__(None)
        self.setupUi(self)
        self.title = self.tr("About")
        
    #@pyqtSlot(str)
    def run(self):
        self.setWindowTitle(self.title)
        self.exec_()
        return True
