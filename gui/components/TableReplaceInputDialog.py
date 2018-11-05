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


    