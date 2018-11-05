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
    os.path.join(pluginPath, 'ui', 'DlgTableInput.ui'))


class TableInputDialog(BASE, WIDGET):

    def __init__(self, title=None):
        super(TableInputDialog, self).__init__(None)
        self.setupUi(self)
        if not title:
            title = self.tr("Enter values")
        self.title = title
        self.value = None

    def accept(self):
      if self.checkValues(self.tableWidget):
        self.value = self.exportValues(self.tableWidget)
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
      for row in xrange(table.rowCount()):
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

    def exportValues(self, table):
      values = []
      for row in xrange(table.rowCount()):
        rowValues = []
        for col in xrange(table.columnCount()):
          item = table.item(row, col)
          if not (item is None):
            rowValues.append(str(item.text()))
        if len(rowValues)>0:
          values.append('(' + '-'.join(rowValues) + ')')
      result = ';'.join(values)
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