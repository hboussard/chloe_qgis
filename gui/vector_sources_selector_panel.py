# -*- coding: utf-8 -*-
"""
Created on Mon Dec  7 17:48:01 2020

@author: pmeurice
"""
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

from qgis.PyQt import uic



from processing.gui.wrappers import (WidgetWrapper, DIALOG_BATCH, DIALOG_STANDARD) # DIALOG_MODELER
from qgis.core import QgsProcessingParameterDefinition,QgsVectorLayer
from qgis.PyQt.QtWidgets import QAbstractItemView,QTableWidgetItem,QListWidgetItem,QTableWidgetSelectionRange,QFileDialog
import math
from re import fullmatch

pluginPath = os.path.dirname(__file__)
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'WgtVectorSourcesSelector.ui'))


class VectorSourcesSelectorPanel(BASE, WIDGET):

    def __init__(self, dialog, alg, default=None, batchGui=False): # standardGui => Flag used when in modeler or batch mode
        super(VectorSourcesSelectorPanel, self).__init__(None)
        self.setupUi(self) 
        self.dialog = dialog
        self.alg = alg
        self.batchGui = batchGui
        
        self.initGui()
        

    def initGui(self):
        # init components
        self.tableWidget.setSelectionMode(QAbstractItemView.ExtendedSelection) # Activer la multi selection
        self.fileListWidget.setSelectionMode(QAbstractItemView.ExtendedSelection) # Activer la multi selection

        
        # connecting signals
        self.pbUp.clicked.connect(self.upSelected)
        self.pbDown.clicked.connect(self.downSelected)
        self.pbInsertLayer.clicked.connect(self.insertLayer)
        self.pbDeleteLayer.clicked.connect(self.deleteLayer)
        self.pbDeleteFile.clicked.connect(self.removeSelectedFile)
        self.pbAddFile.clicked.connect(self.addFileToList)
        self.leBurnValue.textChanged.connect(self.updateTable)
        self.radioQueen.clicked.connect(self.updateTable)
        self.radioRook.clicked.connect(self.updateTable)
        self.filterExpression.fieldChanged.connect(self.updateTable)
        self.vectorFile = ""
        
        self.tableWidget.clear()
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setRowCount(1)
        self.tableWidget.setHorizontalHeaderLabels(["Files","Value","Filter","Neighbors"])
        self.tableWidget.itemSelectionChanged.connect(self.tableSelectionChanged)


    #@pyqtSlot(str)
    def updateTable(self):
        if len(self.tableWidget.selectedRanges())==0:
            self.tableWidget.setRangeSelected(QTableWidgetSelectionRange(0, 0, 0, 3),True)
        row = self.tableWidget.selectedRanges()[0].topRow()
        filesList=""
        for i in range(self.fileListWidget.count()):
            filesList=filesList+','+self.fileListWidget.item(i).text()
        self.tableWidget.setItem(row,0,QTableWidgetItem(filesList))
        self.tableWidget.setItem(row,1,QTableWidgetItem(self.leBurnValue.text()))
        self.tableWidget.setItem(row,2,QTableWidgetItem(self.filterExpression.currentText()))
        self.tableWidget.setItem(row,3,QTableWidgetItem("4" if self.radioRook.isChecked() else "8"))
    
    #@pyqtSlot(str)
    def tableSelectionChanged(self):
        if len(self.tableWidget.selectedRanges())==0:
            self.tableWidget.setRangeSelected(QTableWidgetSelectionRange(0, 0, 0, 3),True)
        rows = self.tableWidget.selectedRanges()[0]
        self.fileListWidget.clear()
        files = self.tableWidget.item(rows.topRow(),0)
        if files is not None:
            filesList = files.text().split(',')
            for file in filesList:
                QListWidgetItem(file,self.fileListWidget)
        bv = self.tableWidget.item(rows.topRow(),1)
        if bv is not None:
            self.leBurnValue.setText(bv.text())
        expr = self.tableWidget.item(rows.topRow(),2)
        if expr is not None:
            self.filterExpression.setExpression(expr.text())
        self.updateFilter()
        nghbrhd = self.tableWidget.item(rows.topRow(),3)
        if nghbrhd is not None:
            self.radioRook.setChecked(nghbrhd.text()=="4")
        else:
            self.radioRook.setChecked(True)


    def setValue(self,value):
        #TODO
        return 
    
    def getValue(self):
        datas=[]
        for i in range(self.tableWidget.rowCount()):
            if self.tableWidget.item(i,0) is None:
                continue
            bv_item = self.tableWidget.item(i,1)
            if bv_item is None:
                bv = ""
            else:
                bv=bv_item.text()
            if fullmatch("[-+]?\d+",bv) is not None:
                bv=int(bv)
            filter_item = self.tableWidget.item(i,2)
            if filter_item is None:
                f=''
            else:
                f=filter_item.text()
            datas.append({'type':'vector',
                          'filenames':self.tableWidget.item(i,0).text().split(','),
                          'burnvalue':bv,
                          'filter':f,
                          '8c':self.tableWidget.item(i,3).text()=="8"
                })
        print(datas)
        return datas



    def update(self):
        """ Called to refresh the ui according to a layer datasource change """
        pass

    #@pyqtSlot(str)
    def upSelected(self):
        #TODO
        pass
        

    #@pyqtSlot(str)
    def downSelected(self):
        #TODO
        pass
    
    def updateFilter(self):
        first = self.fileListWidget.item(0)
        if first is not None:
            if self.vectorFile != first.text():
                self.vectorFile = first.text()
                self.filterExpression.setLayer(QgsVectorLayer(path=self.vectorFile))

    #@pyqtSlot(str)
    def insertLayer(self):
        self.tableWidget.insertRow(self.tableWidget.rowCount())
        self.tableWidget.selectRow(self.tableWidget.rowCount()-1)
        self.tableSelectionChanged()
        
    def deleteLayer(self):
        nr = self.tableWidget.selectedRanges()[0].rowCount()
        for i in range(nr):
            self.tableWidget.removeRow(self.tableWidget.selectedRanges()[0].topRow())
        self.tableSelectionChanged()


    #@pyqtSlot(str)
    def removeSelectedFile(self):
        for item in self.fileListWidget.selectedItems():
            self.fileListWidget.takeItem(self.fileListWidget.currentRow())
        self.updateFilter()
        self.updateTable()

    def addFileToList(self):
        listFiles,ext = QFileDialog.getOpenFileNames(parent = self, caption = self.dialog.tr("Select vector files"),directory = "", filter = "ShapeFiles (*.shp);; All files (*)", initialFilter = "ShapeFiles (*.shp)")
        for file in listFiles:
            QListWidgetItem(file,self.fileListWidget)
        self.updateFilter()
        self.updateTable()
