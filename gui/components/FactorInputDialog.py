# -*- coding: utf-8 -*-

"""
***************************************************************************
    NumberInputDialog.py
    ---------------------
    Date                 : January 2017

        email                : hugues.boussard at inra.fr
***************************************************************************

"""

__author__ = "Daan Guillerme"
__date__ = "May 2019"


# This will get replaced with a git SHA1 when you do a git archive

__revision__ = "$Format:%H$"

import os
from pathlib import Path
from ...helpers.dataclass import CombineFactorElement, CombineFactorTableResult

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import (
    QDialog,
    QMessageBox,
)

from qgis.PyQt.QtGui import QStandardItemModel
from qgis.PyQt.QtCore import Qt

pluginPath = os.path.split(os.path.dirname(__file__))[0]
WIDGET, BASE = uic.loadUiType(os.path.join(pluginPath, "ui", "DlgFactorInput.ui"))


class FactorTableModel(QStandardItemModel):
    def __init__(self):
        super().__init__()
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(
            [self.tr("Factor Name"), self.tr("Layer Name"), self.tr("Layer Path")]
        )

    def get_column_duplicates(self, column_index: int = 0) -> bool:
        """checks if all values in a given column of the model are unique."""
        values = []
        duplicates: "list[str]" = []
        for row in range(self.rowCount()):
            item = self.item(row, column_index)
            if item is not None and item.text() != "":
                value = item.text()
                if value in values:
                    duplicates.append(value)
                else:
                    values.append(value)

        if duplicates:
            QMessageBox.critical(
                None,
                self.tr("Duplicated factor names"),
                self.tr(f"Duplicated factor names ({', '.join(duplicates)})"),
            )
            return False
        return True

    def get_empty_layer_names(self, column: int = 0) -> bool:
        """checks if values of a given column are empty or ""
        and returns a list of layer names that have an empty value"""

        empty_layer_names: "list[str]" = []
        for row_index in range(self.rowCount()):
            item = self.item(row_index, column)
            if item is None or item.text().strip() == "":
                layer_name_item = self.item(row_index, 1)
                if layer_name_item is not None:
                    empty_layer_names.append(layer_name_item.text())

        if empty_layer_names:
            QMessageBox.critical(
                None,
                self.tr("Rasters with an empty factor name"),
                self.tr(
                    f"Rasters with an empty factor name ({', '.join(empty_layer_names)})"
                ),
            )
            return False
        return True

    def get_combine_factor_elements(self) -> "list[CombineFactorElement]":
        """Returns a list of CombineFactorElement objects representing each row in the model"""
        elements = []
        for row in range(self.rowCount()):
            factor_name = self.item(row, 0).text()
            layer_name = self.item(row, 1).text()
            layer_path = Path(self.item(row, 2).text())
            elements.append(CombineFactorElement(factor_name, layer_name, layer_path))
        return elements

    def flags(self, index):
        if index.column() == 0:
            return super().flags(index) | Qt.ItemIsEditable
        else:
            return super().flags(index) & ~Qt.ItemIsEditable


class FactorInputDialog(BASE, WIDGET):
    def __init__(
        self,
        # table_data: "list[CombineFactorElement]",
        table_model: FactorTableModel,
        title: str = "Enter values",
    ):
        super(FactorInputDialog, self).__init__(None)

        self.setupUi(self)
        self._table_model: FactorTableModel = table_model

        self.tableView.setModel(self._table_model)

        self.title: str = title

        self.combination_formula: str = ""  # Combine formula
        self.raster_matrix_value: "list[CombineFactorElement]" = []  # Rasters involved

    def setModel(self, model) -> None:
        self._table_model = model

    def setFormulaValue(self, formula: str) -> None:
        self.formula_plainTextEdit.setPlainText(formula)

    def accept(self):
        # check if model exists, if there are empty factor names, and if there are factor names duplicates
        if (
            self._table_model
            and self._table_model.get_empty_layer_names()
            and self._table_model.get_column_duplicates()
        ):
            # export formula expression
            self.combination_formula = self.formula_plainTextEdit.toPlainText()
            # export raster factor mapping
            self.raster_matrix_value = self._table_model.get_combine_factor_elements()
            QDialog.accept(self)

    def reject(self) -> None:
        QDialog.reject(self)

    def run(self, initial_formula: str) -> CombineFactorTableResult:
        self.setWindowTitle(self.title)
        self.setFormulaValue(formula=initial_formula)
        self.exec_()
        return CombineFactorTableResult(
            result_matrix=self.raster_matrix_value,
            combination_formula=self.combination_formula,
        )
