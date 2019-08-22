# -*- coding: utf-8 -*-

"""
*********************************************************************************************
    odd_even_number_spinbox.py
    ---------------------
        A spinbox of odd or even numbers 
        
        Date                 : June 2019

        email                : daan.guillerme at fdc22.com / hugues.boussard at inra.fr
*********************************************************************************************

"""

import os

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QMenu, QAction, QInputDialog, QListWidget, QListWidgetItem, QDialog, QAbstractItemView
from processing.gui.ListMultiselectWidget import ListMultiSelectWidget
import math


pluginPath = os.path.split(os.path.dirname(__file__))[0]
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'gui', 'ui', 'IntSpinbox.ui'))


class IntSpinbox(BASE, WIDGET):

    """ Integer Spinbox with odd or even numbers """
    def __init__(self, dialog, alg, initialValue=None, minValue=None, maxValue=None, oddNum=False):
        super(IntSpinbox, self).__init__(None)
        self.setupUi(self) 
        self.dialog = dialog
        self.alg = alg
        self.initialValue = initialValue
        self.minValue = minValue
        self.maxValue = maxValue
        self.oddNum = oddNum # specifies wether spinbox value should be odd (True) or even (False)
        self.window_sizes_selected = set()
        self.sbInt.valueChanged.connect(lambda x: self.updateSb()) # update value if wrong one
        self.initGui()

    def initGui(self):
        self.sbInt.setValue(self.initialValue)
        if self.minValue:
            self.sbInt.setMinimum(self.minValue)
        if self.maxValue:
            self.sbInt.setMaximum(self.maxValue)
        self.sbInt.setSingleStep(2)

    def checkValue(self, value): # return correct number
        if (self.oddNum and value % 2 == 0) or (self.oddNum is False and value % 2 > 0):
            return value + 1
        else:
            return value

    def updateSb(self):
        self.sbInt.setValue(self.checkValue(self.sbInt.value()))

    def setValue(self, value):
        self.sbInt.setValue(value)

    def getValue(self):
        return self.sbInt.value()
