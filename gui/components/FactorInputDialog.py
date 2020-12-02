# -*- coding: utf-8 -*-

"""
***************************************************************************
    NumberInputDialog.py
    ---------------------
    Date                 : January 2017

        email                : hugues.boussard at inra.fr
***************************************************************************

"""

__author__ = 'Daan Guillerme'
__date__ = 'May 2019'


# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import re

from qgis.PyQt import uic, QtCore
from qgis.PyQt.QtWidgets import QDialog, QTreeWidgetItem, QMessageBox, QTableWidgetItem
from qgis.core import QgsRasterLayer

from qgis.utils import iface
from processing.tools import dataobjects

pluginPath = os.path.split(os.path.dirname(__file__))[0]
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'DlgFactorInput.ui'))


class FactorInputDialog(BASE, WIDGET):

    def __init__(self, title=None, data=None):
        super(FactorInputDialog, self).__init__(None)
        self.setupUi(self)
        if not title:
            title = self.tr("Enter values")
        self.title = title
        self.combinationValue = None # Combine formula
        self.rasterMatrixValue = None # Rasters involved
        self.data = data # data to populate the selected raster table
        # table widget Setup
        rNum = len(data)
        self.tableWidget.setRowCount(rNum)

        # Populate the widget table with the selected rasters
        row=0
 
        for tup in self.data:
            col=0
            for item in tup:
                cellinfo=QTableWidgetItem(item)
                if col == 1 or col ==2:
                  cellinfo.setFlags(QtCore.Qt.ItemIsEnabled)
                #cellinfo.setFlags(QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled)  # make cell not editable
                self.tableWidget.setItem(row, col, cellinfo)
                col+=1
            row += 1

    def accept(self):
      if self.checkValues(self.tableWidget):
        # export formula expression
        self.combinationValue = self.leText.toPlainText() #self.exportValues(self.leText) 
        # export raster list
        lstRaster = []  
        for i in range(self.tableWidget.rowCount()):
          lstRaster.append('(' + str(self.tableWidget.item(i,2).text()) + ',' + str(self.tableWidget.item(i,0).text()) + ')')
        self.rasterMatrixValue = ';'.join(lstRaster)

        QDialog.accept(self)


    def reject(self):
        QDialog.reject(self)

    def run(self, strInitValue):
        self.setWindowTitle(self.title)
        self.importValues(self.tableWidget, strInitValue)
        self.exec_()
        return self.rasterMatrixValue, self.combinationValue

    def checkValues(self, table):
      state = True
      lstData = []

      for row in range(table.rowCount()):
        lstData.append(table.item(row,0).text())

      res = {}

      for obj in lstData:
          if obj not in res:
              res[obj] = 0
          res[obj] += 1

      lstDuplicate = []

      for key,value in res.items():
        if value > 1:
          lstDuplicate.append(key)
      
      if len(lstDuplicate) > 0:
        QMessageBox.critical(self, self.tr('Duplicated raster names'),
                                 self.tr('Duplicated raster names (' + ','.join(lstDuplicate) + ')'))
        state = False

      return state
      
    def exportValues(self, lineEdit):
      result = lineEdit.text()
      return result

    def importValues(self, table, strValue):
      """rowValues = strValue.split(";")
      for r in range(len(rowValues)):
        row = rowValues[r]
        if len(row)>2:
          colValues = (row[1:len(row)-1]).split("-")
          for c in range(len(colValues)):
            col = colValues[c]
            item = QTableWidgetItem()
            item.setText(col)
            self.tableWidget.setItem(r, c, item)"""
      self.leText.setPlainText(strValue)
    def checkFormatClass(self, str):
      res = True
      try:
        val = float(str)
        if val < 0:  
          res = False
      except ValueError:
        res = False
        return res
      return res

    def checkFormatDomain(self, str):
      p = re.compile("[\[\]]-?[0-9\.]*,-?[0-9\.]*[\[\]]")
      res = not (p.match(str) is None)
      return res