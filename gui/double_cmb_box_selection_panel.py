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
from qgis.core import QgsRasterLayer, QgsProject

import math

from ..ChloeUtils import *

pluginPath = os.path.dirname(__file__)
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, "ui", "WgtDoubleCmbBoxSelector.ui")
)


class DoubleCmbBoxSelectionPanel(BASE, WIDGET):
    def __init__(
        self,
        dialog,
        alg,
        dictValues={},
        initialValue=None,
        rasterLayerParamName=None,
        standardGui=True,
    ):
        super(DoubleCmbBoxSelectionPanel, self).__init__(None)
        self.setupUi(self)
        self.dialog = dialog
        self.alg = alg
        self.dictValues = dictValues
        self.initialValue = initialValue
        self.standardGui = standardGui
        self.rasterLayerParamName = rasterLayerParamName
        self.cbFilter.currentIndexChanged.connect(self.updateMetric)

        self.cbFilter.addItems(self.dictValues.keys())
        self.updateMetric()
        self.cbFilter.setCurrentText(self.initialValue)

        if self.standardGui:
            self.lineEdit.setVisible(False)
        else:
            self.lineEdit.setVisible(True)
            self.cbValue.currentIndexChanged.connect(self.updateMetricLineEdit)

    def updateMetricLineEdit(self):
        metric = self.cbValue.currentText()
        if metric:
            self.lineEdit.setText(metric)
        else:
            self.lineEdit.setText("")

    def updateMetric(self):
        filter_txt = self.cbFilter.currentText()
        w_value = self.cbValue
        w_value.clear()
        if self.dictValues:
            if filter_txt in self.dictValues.keys():
                w_value.addItems(self.dictValues[filter_txt])

    def initCalculateMetric(self):

        rasterLayerParam = (
            self.dialog.mainWidget().wrappers[self.rasterLayerParamName].value()
        )

        # 3.10 fix
        if re.match(r"^[a-zA-Z0-9_]+$", rasterLayerParam):
            selectedLayer = QgsProject.instance().mapLayer(rasterLayerParam)
            rasterLayerParam = selectedLayer.dataProvider().dataSourceUri()

        if rasterLayerParam is None:
            return
        elif isinstance(rasterLayerParam, QgsRasterLayer):
            rasterLayerParam = rasterLayerParam.dataProvider().dataSourceUri()
        elif not isinstance(rasterLayerParam, str):
            rasterLayerParam = str(rasterLayerParam)
        try:
            int_values_and_nodata = ChloeUtils.extractValueNotNull(rasterLayerParam)
            self.dictValues = ChloeUtils.calculateMetric(
                self.alg.types_of_metrics,
                self.alg.types_of_metrics_simple,
                self.alg.types_of_metrics_cross,
                int_values_and_nodata,
            )
        except:
            self.dictValues = []

    def getValue(self):
        if self.standardGui:
            return unicode(self.cbValue.currentText())
        else:
            return unicode(self.lineEdit.text())

    def text(self):
        if self.standardGui:
            return self.cbValue.currentText()
        else:
            return self.lineEdit.text()

    def setValue(self, value):
        self.updateMetric()
