# -*- coding: utf-8 -*-

"""
***************************************************************************
    NumberInputDialog.py
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
import re

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QTreeWidgetItem, QMessageBox, QTableWidgetItem
from qgis.core import QgsRasterLayer

from qgis.utils import iface
from processing.tools import dataobjects

pluginPath = os.path.split(os.path.dirname(__file__))[0]
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'DlgTableReplaceInput.ui'))


class TableReplaceInputDialog(BASE, WIDGET):

    def __init__(self, param, title=None):
        super(TableReplaceInputDialog, self).__init__(None)
        self.setupUi(self)
        if not title:
            title = self.tr("Value to search and replace")
        self.title = title
        self.pbApply.clicked.connect(self.updateTable)
        self.twAssociation.itemChanged.connect(self.updateLeText)
    
    def updateTable(self):
        pass


    def updateLeText(self):
        """Update le text"""
        res = []
        try:
            wt = self.twAssociation
            for row in xrange(0,wt.rowCount()):
                r0 = wt.item(row,0)
                r1 = wt.item(row,1)
                if r0 is not None and r1 is not None:
                    try:
                        res.append((int(r0.text()),int(r1.text())))
                    except:
                        pass
            s_res = []             
            for r in res:
                s_res.append("("+str(r[0])+","+str(r[1])+")")
            final_res = ';'.join(s_res)
            self.leText.setText(final_res)
        except:
            self.leText.setText("")

    def getValue(self):
        return unicode(self.leText.text())

    def setExtentFromString(self, s):
        self.leText.setText(s)


    def text(self):
        return self.leText.text()


    