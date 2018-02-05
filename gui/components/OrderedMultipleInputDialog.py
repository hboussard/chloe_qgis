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

pluginPath = str(QgsApplication.pkgDataPath())
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'python','plugins','processing', 'ui', 'DlgMultipleSelection.ui'))


class OrderedMultipleInputDialog(BASE, WIDGET):

    def __init__(self, options, selectedoptions=None):
        super(OrderedMultipleInputDialog, self).__init__(None)
        self.setupUi(self)


        self.options = options
        self.selectedoptions = selectedoptions or []

        # Additional buttons
        self.btnUp = QPushButton(self.tr('Up'))
        self.buttonBox.addButton(self.btnUp,
                                 QDialogButtonBox.ActionRole)
        self.btnDown = QPushButton(self.tr('Down'))
        self.buttonBox.addButton(self.btnDown,
                                 QDialogButtonBox.ActionRole)

        self.btnSelectAll = QPushButton(self.tr('Select all'))
        self.buttonBox.addButton(self.btnSelectAll,
                                 QDialogButtonBox.ActionRole)
        self.btnClearSelection = QPushButton(self.tr('Clear selection'))
        self.buttonBox.addButton(self.btnClearSelection,
                                 QDialogButtonBox.ActionRole)
        self.btnToggleSelection = QPushButton(self.tr('Toggle selection'))
        self.buttonBox.addButton(self.btnToggleSelection,
                                 QDialogButtonBox.ActionRole)

        self.btnUp.clicked.connect(self.up)
        self.btnDown.clicked.connect(self.down)
        self.btnSelectAll.clicked.connect(lambda: self.selectAll(True))
        self.btnClearSelection.clicked.connect(lambda: self.selectAll(False))
        self.btnToggleSelection.clicked.connect(self.toggleSelection)

        self.populateList()
        # Keep a trace of initial list order to 
        model = self.lstLayers.model()
        self.order = list(xrange(model.rowCount()))


    def populateList(self):
        model = QStandardItemModel()
        for i, option in enumerate(self.options):
            item = QStandardItem(option)
            item.setCheckState(Qt.Checked if i in self.selectedoptions else Qt.Unchecked)
            item.setCheckable(True)
            model.appendRow(item)

        self.lstLayers.setModel(model)

    def accept(self):
        self.selectedoptions = []
        model = self.lstLayers.model()
        for i in xrange(model.rowCount()):
            item = model.item(i)
            if item.checkState() == Qt.Checked:
                self.selectedoptions.append(self.order[i])
        QDialog.accept(self)

    def reject(self):
        self.selectedoptions = None
        QDialog.reject(self)

        
    def up(self):
        selected_items = self.lstLayers.selectedIndexes()
        if len(selected_items) == 1:
            item_index = selected_items[0].row()
            model = self.lstLayers.model()
            if item_index > 0:
                item = model.takeItem(item_index)
                model.removeRows(item_index,1)
                model.insertRow(item_index-1, item)
                qindex = model.index(item_index-1,0)
                self.lstLayers.setCurrentIndex(qindex)
                # Switch order
                self.order[item_index],  self.order[item_index-1] = self.order[item_index-1],  self.order[item_index]



    def down(self):
        selected_items = self.lstLayers.selectedIndexes()
        if len(selected_items) == 1:
            item_index = selected_items[0].row()

            model = self.lstLayers.model()
            if item_index < model.rowCount()-1:
                item = model.takeItem(item_index)
                model.removeRows(item_index,1)
                model.insertRow(item_index+1, item)
                qindex = model.index(item_index+1,0)
                self.lstLayers.setCurrentIndex(qindex)
                # Switch order
                self.order[item_index],  self.order[item_index+1] = self.order[item_index+1],  self.order[item_index]



    def selectAll(self, value):
        model = self.lstLayers.model()
        for i in xrange(model.rowCount()):
            item = model.item(i)
            item.setCheckState(Qt.Checked if value else Qt.Unchecked)

    def toggleSelection(self):
        model = self.lstLayers.model()
        for i in xrange(model.rowCount()):
            item = model.item(i)
            checked = item.checkState() == Qt.Checked
            item.setCheckState(Qt.Unchecked if checked else Qt.Checked)

