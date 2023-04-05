# -*- coding: utf-8 -*-

"""
*********************************************************************************************
    factor_table_panel.py
    ---------------------

        Widget used in the Combine Algorithm. Sets the input rasters names and setup the combination formula.
        Date                 : May 2019

        email                : daan.guillerme at fdc22.com / hugues.boussard at inra.fr
*********************************************************************************************

"""

__author__ = "Daan Guillerme"
__date__ = "June 2019"
__copyright__ = "(C) 2019, Daan Guillerme"

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = "$Format:%H$"

import os
from pathlib import Path
from ..helpers.dataclass import CombineFactorTableResult, CombineFactorElement

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QMessageBox

from qgis.core import QgsApplication, QgsProject, QgsProcessingOutputLayerDefinition

from .components.FactorInputDialog import FactorInputDialog

import re

from ..ChloeUtils import *

pluginPath = str(QgsApplication.pkgDataPath())
WIDGET, BASE = uic.loadUiType(
    os.path.join(
        pluginPath, "python", "plugins", "processing", "ui", "widgetBaseSelector.ui"
    )
)


class FactorTablePanel(BASE, WIDGET):

    # standardGui => Flag used when in modeler or batch mode
    def __init__(self, dialog, alg, default=None, input_matrix=None):
        super(FactorTablePanel, self).__init__(None)
        self.setupUi(self)
        self.dialog = dialog
        self.alg = alg
        self.input_matrix = input_matrix
        self.factor_table_result: CombineFactorTableResult = CombineFactorTableResult(
            result_matrix="", combination_formula=""
        )
        if hasattr(self.leText, "setPlaceholderText"):
            self.leText.setPlaceholderText(self.tr("Combination Formula"))
        self.leText.setReadOnly(True)
        self.btnSelect.clicked.connect(self.selectValues)  # Bouton "...

    def selectValues(self):
        """Values selector"""
        # Get initial value
        formula_text: str = self.leText.text()

        list_factor_elements: "list[CombineFactorElement]" = []
        # create a list to fill the factor table widget

        if not self.input_matrix:
            return

        list_layers = (
            self.dialog.mainWidget().wrappers[self.alg.INPUTS_MATRIX].widgetValue()
        )

        if len(list_layers) == 0:
            QMessageBox.critical(
                self, self.tr("Select rasters"), self.tr("No rasters selected")
            )
            return

        for i, layer in enumerate(list_layers):
            if isinstance(layer, QgsProcessingOutputLayerDefinition):
                layer = layer.name()
            # if raster loaded in QgsProject.instance()
            if re.match(r"^[a-zA-Z0-9_]+$", layer):
                # get raster layer object
                selectedLayer = QgsProject.instance().mapLayer(layer)
                path = selectedLayer.dataProvider().dataSourceUri()
                lyrName: str = ChloeUtils.deduceLayerName(selectedLayer)
            else:
                path = str(layer)
                lyrName: str = ChloeUtils.deduceLayerName(layer)

            list_factor_elements.append(
                CombineFactorElement(
                    factor_name=f"m{i+1}",
                    layer_name=lyrName,
                    layer_path=Path(path),
                )
            )

        # Dialog list check box
        dial = FactorInputDialog(list_factor_elements, self.tr("Combine"))
        self.factor_table_result = dial.run(formula_text)

        # # result
        if self.factor_table_result:
            self.leText.setText(self.factor_table_result.combination_formula)

    def getValue(self) -> "list[str]":
        # Return a list of string combining the raster matrix used and the combination formula
        return [
            self.factor_table_result.result_matrix,
            self.factor_table_result.combination_formula,
        ]

    def text(self) -> str:
        return self.leText

    def setValue(self, value) -> None:
        self.leText.setText(value)

    def setText(self, value) -> None:
        pass

    def resetFormula(self) -> None:
        self.leText.setText("")
