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
from qgis.PyQt.QtWidgets import QMessageBox, QTableWidgetItem
from qgis.core import QgsRasterLayer, QgsProject

from osgeo import gdal
import numpy as np
import math

from ..ChloeUtils import ChloeUtils

pluginPath = os.path.dirname(__file__)
WIDGET, BASE = uic.loadUiType(os.path.join(pluginPath, "ui", "DlgTableReplaceInput.ui"))


class TableReplaceInputPanel(BASE, WIDGET):
    def __init__(self, dialog, alg, default=None, batchGui=False):
        super(TableReplaceInputPanel, self).__init__(None)
        self.setupUi(self)
        self.dialog = dialog
        self.alg = alg
        self.batchGui = batchGui
        # self.dialog[linked_param].valuechanged.connect(self.test)
        # print(str(self.dialog))
        # parametersPanel = self.dialog.mainWidget()
        # wrapper = parametersPanel.wrappers[linked_param]
        # print(str(wrapper))

        self.pbFromAsc.clicked.connect(self.updateMapASC)
        self.pbApply.clicked.connect(self.applyCSVMap)
        self.twAssociation.itemChanged.connect(self.updateLeText)
        self.twAssociation.itemChanged.connect(self.checkCellValue)

    def updateTable(self):

        if self.batchGui:
            rasterLayerParam = self.dialog.mainWidget().wrappers[0][0].value()
        else:
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

    def updateMapASC(self):

        if self.batchGui:
            p = self.dialog.mainWidget().wrappers[0][0].value()
        else:
            p = self.dialog.mainWidget().wrappers["INPUT_ASC"].value()

        if p is None:
            return
        elif isinstance(p, QgsRasterLayer):
            f_input = p.dataProvider().dataSourceUri().value()
        elif isinstance(p, str):
            # if p is not a correct path then it is already loaded in QgsProject instance, get the QgsRasterLayer object and the file's full path
            if re.match(r"^[a-zA-Z0-9_]+$", p):
                selectedLayer = QgsProject.instance().mapLayer(p)
                f_input = selectedLayer.dataProvider().dataSourceUri()
            else:
                f_input = p
        else:
            f_input = str(p)

            # === Test algorithm
        ds = gdal.Open(f_input)  # DataSet
        band = ds.GetRasterBand(1)  # -> band
        array = np.array(band.ReadAsArray())  # -> matrice values
        values = np.unique(array)
        # Add nodata values in numpy array
        values_and_nodata = np.insert(values, 0, band.GetNoDataValue())
        # int_values_and_nodata = np.unique(
        #     [int(math.floor(x)) for x in values_and_nodata]
        # )
        real_values_and_nodata = np.unique([x for x in values_and_nodata])

        if len(real_values_and_nodata) > 64:
            QMessageBox.critical(
                self,
                self.tr("Input values error"),
                self.tr(
                    f"to much input values ({len(real_values_and_nodata)}). Maximum allowed : 64"
                ),
            )
            return

        # Dialog list check box
        row = 0
        for tup in real_values_and_nodata:
            item = QTableWidgetItem()
            item.setText(str(tup))
            self.twAssociation.setItem(row, 0, item)
            row += 1

    def emptyMappingAsc(self):

        rows = range(self.twAssociation.rowCount())
        cols = range(self.twAssociation.columnCount())
        for r in rows:
            for c in cols:
                if self.twAssociation.item(r, c) is not None:
                    self.twAssociation.setItem(r, c, None)

    def updateMapCSV(self, mapFile):
        self.mapFile = mapFile
        self.cmbBox.clear()
        try:
            # == Get list index
            if mapFile:
                if os.path.exists(mapFile):
                    with open(mapFile, "r") as f:
                        line = next(f)
                    headers = list(filter(None, re.split("\n|;| |,", line)))
                    # print(str(headers))
                    self.cmbBox.addItems(headers[1:])
        except:
            pass

    def applyCSVMap(self):
        try:
            if self.mapFile:
                if os.path.exists(self.mapFile):
                    # print('before open header')
                    with open(self.mapFile, "r") as f:
                        line = next(f)
                    headers = list(filter(None, re.split("\n|;| |,", line)))
                    name_col = self.cmbBox.currentText()
                    idex_col = headers[1:].index(name_col) + 1
        except:
            return

        t_ass = []  # Table d'association
        if self.mapFile:
            if os.path.exists(self.mapFile):
                with open(self.mapFile, "r") as f:
                    b_header = 1
                    # print('before iterating lines')
                    for line in f:
                        # print(str(line))
                        if b_header == 1:
                            b_header = 0
                            continue  # Jump the header
                        # print(str(line))
                        data = list(filter(None, re.split("\n|;| |,", line)))
                        # Table two dimention
                        t_ass.append([data[0], data[idex_col]])

        # Match with existing values in twAssociation
        if t_ass:
            lstCsv = []
            lstTw = []
            wt = self.twAssociation

            # create list of existing values in twAssociation table
            for t_as in t_ass:
                try:
                    lstCsv.append((float(t_as[0]), float(t_as[1])))
                except:
                    pass

            # create list of csv values
            for row in range(0, wt.rowCount()):
                r0 = wt.item(row, 0)
                r1 = wt.item(row, 1)
                if r0 != None and r0 != "":
                    try:
                        r1 = float(wt.item(row, 1).text())
                    except:
                        r1 = None
                    try:
                        lstTw.append((float(r0.text()), r1))
                    except:
                        pass

            # if a number to replace in association table exists in csv file, then replace it with csv's row
            # if csv row does not exists in association table then add it
            for csvItem in lstCsv:
                for twItem in lstTw:
                    if csvItem[0] == twItem[0]:
                        lstTw.remove(twItem)
                        lstTw.append(csvItem)
                if csvItem not in lstTw:
                    lstTw.append(csvItem)

            # sorted export list
            lstExport = sorted(lstTw, key=lambda x: x[0])

            # clear association table
            self.emptyMappingAsc()

            # fill association table
            rowLst = 0
            for new_value in lstExport:
                itemCol1 = QTableWidgetItem()
                itemCol2 = QTableWidgetItem()
                itemCol1.setText(ChloeUtils.displayFloatToInt(new_value[0]))
                itemCol2.setText(ChloeUtils.displayFloatToInt(new_value[1]))
                self.twAssociation.setItem(rowLst, 0, itemCol1)
                self.twAssociation.setItem(rowLst, 1, itemCol2)
                rowLst += 1

    def updateLeText(self):
        """Update le text"""
        res = []
        try:
            wt = self.twAssociation
            for row in range(0, wt.rowCount()):
                r0 = wt.item(row, 0)
                r1 = wt.item(row, 1)
                if r0 is not None and r1 is not None:
                    try:
                        res.append((r0.text(), r1.text()))
                    except:
                        pass
            s_res = []
            for r in res:
                s_res.append("(" + str(r[0]) + "," + str(r[1]) + ")")
            final_res = ";".join(s_res)
            self.leText.setText(final_res)
        except:
            self.leText.setText("")
            raise

    def checkCellValue(self, item):

        if self.twAssociation.currentItem() is None:
            return

        currentItemRow = self.twAssociation.currentItem().row()
        currentValue = self.twAssociation.currentItem().text()

        if currentValue is None or currentValue == "":
            return

        # check if cellValue allready exists in tablewidget
        if self.twAssociation.currentItem().column() == 0:

            for row in range(0, self.twAssociation.rowCount()):

                if (
                    self.twAssociation.item(row, 0) is not None
                    and currentValue == self.twAssociation.item(row, 0).text()
                    and row != currentItemRow
                ):
                    QMessageBox.critical(
                        self,
                        self.tr("Cell value error"),
                        self.tr('"{}" is already used'.format(currentValue)),
                    )
                    self.twAssociation.currentItem().setText(None)
                    return

        # check if cellValue is numeric

        try:
            float(currentValue)
        except:
            QMessageBox.critical(
                self,
                self.tr("Cell value error"),
                self.tr('"{}" is not a numeric value'.format(currentValue)),
            )
            self.twAssociation.currentItem().setText(None)

    def text(self):
        return self.leText.text()

    def getValue(self):
        return unicode(self.leText.text())

    def setValue(self, value):
        self.leText.setText(value)

    def setText(self, value):
        pass
