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
from ...helpers.dataclass import CombineFactorElement, CombineFactorTableResult
from collections import Counter

from qgis.PyQt import uic, QtCore
from qgis.PyQt.QtWidgets import QDialog, QMessageBox, QTableWidgetItem, QTableWidget

pluginPath = os.path.split(os.path.dirname(__file__))[0]
WIDGET, BASE = uic.loadUiType(os.path.join(pluginPath, "ui", "DlgFactorInput.ui"))


class FactorInputDialog(BASE, WIDGET):
    def __init__(
        self,
        table_data: "list[CombineFactorElement]",
        title: str = "Enter values",
    ):
        super(FactorInputDialog, self).__init__(None)
        self.setupUi(self)
        self.title: str = title
        self.combination_formula: str = ""  # Combine formula
        self.raster_matrix_value: str = ""  # Rasters involved

        self.factor_table_result: CombineFactorTableResult
        self.table_data: "list[CombineFactorElement]" = (
            table_data  # data to populate the selected raster table
        )

        self.setup_factor_table()

    def setup_factor_table(self) -> None:
        # table widget Setup
        if self.table_data:
            # table widget Setup
            row_count: int = len(self.table_data)
            self.tableWidget.setRowCount(row_count)
            self.tableWidget.setColumnCount(3)

            # Populate the widget table with the selected rasters
            for row, factor in enumerate(self.table_data):
                self.tableWidget.setItem(row, 0, QTableWidgetItem(factor.factor_name))
                self.tableWidget.setItem(row, 1, QTableWidgetItem(factor.layer_name))
                cellinfo = QTableWidgetItem(factor.layer_path.as_posix())
                self.tableWidget.setItem(row, 2, cellinfo)

                for col in range(3):
                    if col == 1 or col == 2:
                        self.tableWidget.item(row, col).setFlags(
                            QtCore.Qt.ItemIsEnabled
                        )

    def check_table_values(self, table: QTableWidget) -> bool:
        """checks if all the values of the data table are ok"""
        data = [table.item(row, 0).text() for row in range(table.rowCount())]
        duplicates = [item for item, count in Counter(data).items() if count > 1]
        if duplicates:
            QMessageBox.critical(
                self,
                self.tr("Duplicated raster names"),
                self.tr(f"Duplicated raster names ({', '.join(duplicates)})"),
            )
            return False
        return True

    def setFormulaValue(self, formula: str) -> None:
        self.formula_plainTextEdit.setPlainText(formula)

    def accept(self):
        if self.check_table_values(self.tableWidget):
            # export formula expression
            self.combination_formula = self.formula_plainTextEdit.toPlainText()
            # export raster list
            list_rasters: "list[str]" = []
            for i in range(self.tableWidget.rowCount()):
                # append raster : layer_path, factor_name
                list_rasters.append(
                    f"({str(self.tableWidget.item(i, 2).text())},{str(self.tableWidget.item(i, 0).text())})"
                )

            self.raster_matrix_value = ";".join(list_rasters)

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
