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
from qgis.PyQt.QtWidgets import QMenu, QAction, QInputDialog, QListWidget, QListWidgetItem, QDialog, QAbstractItemView
from qgis.PyQt.QtGui import QCursor

from qgis.gui import QgsMessageBar, QgsExpressionBuilderDialog, QgsFileWidget
from qgis.core import QgsRasterLayer, QgsVectorLayer, QgsApplication
from qgis.utils import iface

from processing.core.ProcessingConfig import ProcessingConfig
from processing.tools import dataobjects

from processing.gui.ListMultiselectWidget import ListMultiSelectWidget

import math

from ..ChloeUtils import *

pluginPath = os.path.split(os.path.dirname(__file__))[0]
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'gui', 'ui', 'WgtListSelector.ui'))


class ListSelectionPanel(BASE, WIDGET):

    def __init__(self, dialog, alg, typesOfMetrics={}, initialValue=None, rasterLayerParamName='INPUT_ASC'):
        super(ListSelectionPanel, self).__init__(None)
        self.setupUi(self) 
        self.dialog = dialog
        self.alg = alg
        self.typesOfMetrics = typesOfMetrics
        self.initialValue = initialValue
        self.rasterLayerParamName = rasterLayerParamName
        
        self.metrics_selected = set()

        self.initGui()
        

    def initGui(self):
        # init components
        self.listSrc.setSelectionMode(QAbstractItemView.ExtendedSelection) # Activer la multi selection
        self.listDest.setSelectionMode(QAbstractItemView.ExtendedSelection) # Activer la multi selection

        self.cbFilter.addItems(self.typesOfMetrics.keys())
        self.listSrc.clear()
        self.listDest.clear()
        self.lineEdit.setReadOnly(True)
        
        # connecting signals
        self.pbRight.clicked.connect(self.addInListDst)
        self.listSrc.itemDoubleClicked.connect(self.addInListDst)
        self.pbLeft.clicked.connect(self.removeInListDst)
        self.pbAll.clicked.connect(self.addAllInListDst)
        self.pbClear.clicked.connect(self.removeAllListDst)
        #self.lineEdit.textChanged.connect(self.parametersHaveChanged)
        self.cbFilter.currentIndexChanged.connect(self.changeMetricDependent)

        # list init
        self.changeMetricDependent()
        self.cbFilter.setCurrentText(self.initialValue)

    def getValue(self):
        return unicode(self.lineEdit.text())

    def text(self):
        return self.lineEdit.text()


    def update(self):
        """ Called to refresh the ui according to a layer datasource change """
        self.initCalculateMetric()
        self.removeAllListDst()
        self.changeMetricDependent()

    #@pyqtSlot(str)
    def initCalculateMetric(self):
        rasterLayerParam = self.dialog.mainWidget().wrappers[self.rasterLayerParamName].value()
        if rasterLayerParam is None:
            return
        elif isinstance(rasterLayerParam, QgsRasterLayer): 
            rasterLayerParam = rasterLayerParam.dataProvider().dataSourceUri()
        elif not isinstance(rasterLayerParam,str):
            rasterLayerParam = str(rasterLayerParam)

        try:
            
            int_values_and_nodata = ChloeUtils.extractValueNotNull(rasterLayerParam)

            self.typesOfMetrics = ChloeUtils.calculateMetric(
                self.alg.types_of_metrics,
                self.alg.types_of_metrics_simple,
                self.alg.types_of_metrics_cross,
                int_values_and_nodata
            )
        except:
            self.typesOfMetrics = []
            raise

    @staticmethod
    def iterAllItems(lws):
        for i in range(lws.count()):
            yield lws.item(i)

    #@pyqtSlot(str)
    def addAllInListDst(self):
        self.addInListDst(all=True)


    #@pyqtSlot(str)
    def addInListDst(self,item=None,all=False):
        """Add metrics selected in listSrc to ListDst"""
        if not all:
            selected = self.listSrc.selectedItems()
        else:
            selected = self.iterAllItems(self.listSrc)
        for lw in selected:
            self.metrics_selected.add(lw.text())

        listDest = self.listDest
        listDest.clear()
        listDest.addItems(list(self.metrics_selected))
        self.updateMetricsLigneEdit()

    #@pyqtSlot()
    def removeAllListDst(self):
        listDest = self.listDest
        listDest.clear()
        self.metrics_selected = set()
        self.updateMetricsLigneEdit()

    #@pyqtSlot(str)
    def removeInListDst(self):
        """Remove metrics selected in listDest"""
        selected = self.listDest.selectedItems()
        for lw in selected:
            self.metrics_selected.remove(lw.text())

        listDest = self.listDest
        listDest.clear()
        listDest.addItems(list(self.metrics_selected))
        self.updateMetricsLigneEdit()

 
    def updateMetricsLigneEdit(self):
        """update Metrics (QLineEdit in readOnly mode)"""
        lineEdit = self.lineEdit
        metrics = list(self.metrics_selected)
        if metrics:
            lineEdit.setText(";".join(metrics))
        else:
            lineEdit.setText("")

    #@pyqtSlot(str)
    def changeMetricDependent(self):
        """
        Update metric source list when the filter of metric change
        """
        cbFilter = self.cbFilter
        
        # === Init list metric
        value = cbFilter.currentText()
        listSrc = self.listSrc
        listSrc.clear()
        if self.typesOfMetrics:
            if value in self.typesOfMetrics.keys():
                listSrc.addItems(self.typesOfMetrics[value])