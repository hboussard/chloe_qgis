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

pluginPath = os.path.dirname(__file__)
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'DlgTableReplaceInput.ui'))


class TableReplaceInputPanel(BASE, WIDGET):

    def __init__(self, dialog, alg, default=None):
        super(TableReplaceInputPanel, self).__init__(None)
        self.setupUi(self) 
        self.dialog = dialog
        self.alg = alg
        
        #self.dialog[linked_param].valuechanged.connect(self.test)
        #print(str(self.dialog))
        #parametersPanel = self.dialog.mainWidget()
        #wrapper = parametersPanel.wrappers[linked_param]
        #print(str(wrapper))
            
        self.pbApply.clicked.connect(self.applyCSVMap)
        self.twAssociation.itemChanged.connect(self.updateLeText)
    
   
    def updateMapCSV(self, mapFile):
        self.mapFile = mapFile
        self.cmbBox.clear()
        try:
            # == Get list index
            if mapFile:
                if os.path.exists(mapFile):
                    with open(mapFile, 'r') as f:
                        line = next(f)
                    headers = list(filter(None, re.split('\n|;| |,', line)))
                    #print(str(headers))
                    self.cmbBox.addItems(headers[1:])
        except:
            pass


    #@pyqtSlot(str)
    def applyCSVMap(self):
        #print('applyCSVMap' + str(self.mapFile))
        # Index
        if self.mapFile:
            if os.path.exists(self.mapFile):
                #print('before open header')
                with open(self.mapFile, 'r') as f:
                    line = next(f)
                headers = list(filter(None, re.split('\n|;| |,', line)))
                name_col = self.cmbBox.currentText()
                idex_col = headers[1:].index(name_col) +1


        t_ass =[] # Table d'association
        if self.mapFile:
            if os.path.exists(self.mapFile):
                with open(self.mapFile, 'r') as f:
                    b_header = 1
                    print('before iterating lines')
                    for line in f:
                        print(str(line))
                        if b_header == 1:
                            b_header = 0
                            continue   # Jump the header
                        print(str(line))
                        data = list(filter(None, re.split('\n|;| |,', line)))
                        t_ass.append([data[0],data[idex_col]]) # Table two dimention

        print(str(t_ass))
        if t_ass:   # Update with associtation table
            wt = self.twAssociation
            for t_as in t_ass:
                val_old = t_as[0]
                val_new = t_as[1]
                for row in range(0,wt.rowCount()):
                    r0 = wt.item(row,0)
                    if r0!=None:
                        if r0.text() == str(val_old):
                            # Update value
                            r1 = wt.item(row,1)
                            if isinstance(r1, QTableWidgetItem):        
                                r1.setText(str(val_new))
                            else:
                                wt.setItem(row,1,QTableWidgetItem(str(val_new)))

    def updateLeText(self):
        """Update le text"""
        res = []
        try:
            wt = self.twAssociation
            for row in range(0,wt.rowCount()):
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
            raise

    def text(self):
        return self.leText.text()

    def getValue(self):
        return unicode(self.leText.text())

    def setValue(self, value):
        self.leText.setText(value)

    def setText(self, value):
        pass