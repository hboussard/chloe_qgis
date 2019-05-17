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
        self.value = None
        self.data = data
        # table widget Setup
        rNum = len(data)
        self.tableWidget.setRowCount(rNum)

        # Populate the widget table with the selected rasters
        row=0
 
        for tup in data:
 
            col=0
 
            for item in tup:
 
                cellinfo=QTableWidgetItem(item)
                
                cellinfo.setFlags(QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled)  # make cell not editable
 
                self.tableWidget.setItem(row, col, cellinfo)
 
                col+=1
 
            row += 1


    def accept(self):
      if self.checkValues(self.tableWidget):
        self.value = self.exportValues(self.leText)
        QDialog.accept(self)
  
    def reject(self):
        QDialog.reject(self)

    def run(self, strInitValue):
        self.setWindowTitle(self.title)
        self.importValues(self.tableWidget, strInitValue)
        self.exec_()
        return self.value

    def checkValues(self, table):
      values = []
      res = True
      for row in range(table.rowCount()):
        itemDomain = table.item(row, 0)
        if not (itemDomain is None):
          if not self.checkFormatDomain(str(itemDomain.text())):
            QMessageBox.critical(self, self.tr('Wrong domain expression'),
                                 self.tr('The expression entered is not correct. A domain should follow the interval syntax. Examples: [0,1[ or ],-1] or [2,['))
            res = False
          else:
            itemClass = table.item(row, 1)
            if (not (itemDomain is None)) and (not self.checkFormatClass(str(itemClass.text()))):
              QMessageBox.critical(self, self.tr('Wrong class expression'),
                                  self.tr('The expression entered is not correct. A class value should be a positive integer'))
              res = False
      return res

    def exportValues(self, lineEdit):
      result = lineEdit.text()
      return result


    def importValues(self, table, strValue):
      rowValues = strValue.split(";")
      for r in range(len(rowValues)):
        row = rowValues[r]
        if len(row)>2:
          colValues = (row[1:len(row)-1]).split("-")
          for c in range(len(colValues)):
            col = colValues[c]
            item = QTableWidgetItem()
            item.setText(col)
            self.tableWidget.setItem(r, c, item)

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