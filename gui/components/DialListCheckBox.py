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

from PyQt4.QtCore import Qt, QCoreApplication
from PyQt4.QtGui import QDialog, QApplication, QListView, QMainWindow, QWidget, QStandardItem, QVBoxLayout, QHBoxLayout, QStandardItemModel, QPushButton
import sys
from random import randint


class DialListCheckBox(object):
    """
    Dialog with list check box
    example : 1,2,4,6,8
    """
    def __init__(self, values, checked_values=[]):
        self.dial = QDialog()
        self.result = ""

        # Layout Principal
        m_vbl = QVBoxLayout(self.dial)

        # List item checkable  
        view = QListView()
        m_vbl.addWidget(view)

        self.m_sim = QStandardItemModel() 
        view.setModel(self.m_sim)

        self._load_item(values,checked_values)

        # List buttons
        bt_all = QPushButton(self.tr("All"))
        bt_all.clicked.connect(lambda: self._check_all())

        bt_nothing = QPushButton(self.tr("Nothing"))
        bt_nothing.clicked.connect(lambda: self._check_nothing())

        bt_print = QPushButton(self.tr("Ok"))
        bt_print.clicked.connect(lambda: self._check_ok())

        # Sub layout for buttons
        m_vbh = QHBoxLayout()
        m_vbl.addLayout(m_vbh)

        m_vbh.addWidget(bt_all)
        m_vbh.addWidget(bt_nothing)
        m_vbh.addWidget(bt_print)

    def _load_item(self,values,checked_values):

        """Load item list"""
        for v in values:                   
            item = QStandardItem(str(v))
            if v in checked_values:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            item.setCheckable(True)
            self.m_sim.appendRow(item)
    
    def _check_all(self):
        """Check all item"""
        for index in range(self.m_sim.rowCount()): ## Iteration sur le model (contient la list des items)
            item = self.m_sim.item(index)
            if item.isCheckable() and item.checkState() == Qt.Unchecked: # Si Unchecked 
                item.setCheckState(Qt.Checked)

    def _check_nothing(self):
        """Uncheck all item"""
        for index in range(self.m_sim.rowCount()): ## Iteration sur le model (contient la list des items)
            item = self.m_sim.item(index)
            if item.isCheckable() and item.checkState() == Qt.Checked: # Si Checked 
                item.setCheckState(Qt.Unchecked)

    def _check_ok(self):
        """Get value of checked items and exit"""
        l_value=[]
        for index in range(self.m_sim.rowCount()): ## Iteration sur le model (contient la list des items)
            item = self.m_sim.item(index)
            if item.isCheckable() and item.checkState() == Qt.Checked: # Si Checked 
                l_value.append(str(item.text()))

        if l_value:
            s_value = ";".join(l_value)
        else:
            s_value = ""


        self.result = s_value
        self.dial.close()
 
        
    def run(self):

        self.dial.setWindowTitle(self.tr("Select values"))

        self.dial.exec_()
        return self.result

    def tr(self, string, context=''):
        if context == '' or context==None:
            context = self.__class__.__name__
        return QCoreApplication.translate(context, string)
