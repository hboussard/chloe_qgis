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
from typing import Tuple, Union
from ..helpers.dataclass import CombineFactorElement

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QMessageBox, QHeaderView
from qgis.PyQt.QtGui import QStandardItemModel, QStandardItem
from qgis.PyQt.QtCore import Qt

from qgis.core import (
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterDefinition,
)


from ..ChloeUtils import *

from processing.gui.wrappers import (
    DIALOG_MODELER,
    DIALOG_BATCH,
    DIALOG_STANDARD,
)

pluginPath = os.path.split(os.path.dirname(__file__))[0]
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, "gui", "ui", "WgtCombineSelector.ui")
)


class FactorTableModel(QStandardItemModel):
    """
    A custom `QStandardItemModel` class that represents the data model for factor table of the combine algorithm widget.

    Attributes:
        None

    Methods:
        set_data(self, data: "list[CombineFactorElement]") -> None:
            Sets the data in the model with a list of CombineFactorElement objects.

        has_column_duplicates(self, column_index: int = 0) -> bool:
            Checks if all values in a given column of the model are unique.

        has_empty_layer_names(self, column: int = 0) -> bool:
            Checks if values of a given column are empty or "" and returns a list of layer names that have an empty value.

        get_combine_factor_elements(self, return_string: bool = False) -> "list[CombineFactorElement]":
            Returns a list of CombineFactorElement objects representing each row in the model.
    """

    def __init__(self):
        super().__init__()
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(
            [self.tr("Factor name"), self.tr("Layer name"), self.tr("Layer path")]
        )

    def set_data(self, data: "list[CombineFactorElement]") -> None:
        """
        Sets the data in the model with a list of CombineFactorElement objects.

        Args:
            data (list): The list of CombineFactorElement objects.

        Returns:
            None
        """
        self.setRowCount(0)

        for factor in data:
            if factor:
                # with standard dialog the value used is of type CombineFactorElement
                if isinstance(factor, CombineFactorElement):
                    factor_name_item = QStandardItem(factor.factor_name)
                    layer_name_item = QStandardItem(factor.layer_name)
                    layer_path_item = QStandardItem(factor.layer_path.as_posix())
                    layer_id = QStandardItem(factor.layer_id)
                # in modeler dialog the value used is a list of strings because the values are stored in the model xml file as a list of strings
                elif len(factor) == 4:
                    factor_name_item = QStandardItem(factor[0])
                    layer_name_item = QStandardItem(factor[1])
                    layer_path_item = QStandardItem(factor[2])
                    layer_id = QStandardItem(factor[3])
                else:
                    raise TypeError(
                        f"Expected CombineFactorElement or List[str, str, Path, str], but got {type(factor)}"
                    )

                # add row to model
                self.appendRow(
                    [
                        factor_name_item,
                        layer_name_item,
                        layer_path_item,
                        layer_id,
                    ]
                )

    def has_column_duplicates(self, column_index: int = 0) -> bool:
        """ "
        Checks if all values in a given column of the model are unique.

        Args:
            column_index (int, optional): The index of the column to check. Defaults to 0.

        Returns:
            bool: True if there are duplicates, False otherwise.
        """
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
            return True
        return False

    def has_empty_layer_names(self, column: int = 0) -> bool:
        """Checks if the values of a given column are empty or ""
        and returns a list of layer names that have an empty value.

        Args:
            column (int, optional): The index of the column to check. Defaults to 0.

        Returns:
            bool: True if any layer name is empty, False otherwise.
        """

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
            return True
        return False

    def get_combine_factor_elements(
        self, return_string: bool = False
    ) -> Union["list[CombineFactorElement]", "list[list[str]]"]:
        """Returns a list of CombineFactorElement objects representing each row in the model.

        Args:
            return_string (bool, optional): If True, the returned list is composed of list of strings (in modeler because the values needs to be stored
            in the .model xml file as list of strings).
                If False, the paths will be returned as list of CombineFactorElement objects. Defaults to False.

        Returns:
            list[CombineFactorElement]: A list of CombineFactorElement objects.
        """
        elements = []
        for row in range(self.rowCount()):
            factor_name = self.item(row, 0).text()
            layer_name = self.item(row, 1).text()
            layer_path = Path(self.item(row, 2).text())
            layer_id = self.item(row, 3).text()
            if return_string:
                elements.append([factor_name, layer_name, str(layer_path), layer_id])
            else:
                elements.append(
                    CombineFactorElement(factor_name, layer_name, layer_path, layer_id)
                )
        return elements

    def flags(self, index):
        if index.column() == 0:
            return super().flags(index) | Qt.ItemIsEditable
        else:
            return super().flags(index) & ~Qt.ItemIsEditable


class FactorTablePanel(BASE, WIDGET):
    """
    A widget containing a table view to edit raster combinations.

    Attributes:
        dialog (QgsProcessingAlgorithmDialog): The parent dialog.
        alg (QgsProcessingAlgorithm): The algorithm.
        input_matrix (str): The name of the input matrix parameter.
        dialog_type (int): The dialog type (standard or modeler).
        is_modeler_dialog (bool): Whether the dialog is in modeler mode.
        _table_model (FactorTableModel): The table model.
    """

    def __init__(
        self, dialog, alg, default=None, input_matrix=None, dialog_type=DIALOG_STANDARD
    ):
        """
        Args:
            input_matrix (str): The name of the input matrix parameter.
            dialog_type (int): The dialog type (standard or modeler).
        """

        super(FactorTablePanel, self).__init__(None)
        self.setupUi(self)
        self.dialog = dialog
        self.alg = alg
        self.input_matrix = input_matrix
        self.dialog_type = dialog_type

        # Determine whether the dialog is in modeler mode.
        self.is_modeler_dialog: bool = False
        if dialog_type == DIALOG_MODELER:
            self.is_modeler_dialog = True

        # Create and set the table model.
        self._table_model: FactorTableModel = FactorTableModel()
        self.tableView.setModel(self._table_model)
        self.tableView.setColumnHidden(3, True)

        # Set column sizes.
        # Set column 0 to match header text
        self.tableView.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        # Set column 1 to match column content
        self.tableView.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents
        )
        # Set column 2 to stretch to the remaining space
        self.tableView.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        # Set the placeholder text for the combination formula text box.
        if hasattr(self.LineEditFormula, "setPlaceholderText"):
            self.LineEditFormula.setPlaceholderText(self.tr("Combination Formula"))

        # Connect the populate button to the populateTableModel method.
        self.populate.clicked.connect(self.populate_table_model)  # Bouton "...

    def getModel(self) -> FactorTableModel:
        """Returns the table model."""
        return self._table_model

    def populate_table_model(self):
        """Populates the table model."""
        if self.is_modeler_dialog:
            self.populate_table_model_for_modeler()
        else:
            self.populate_table_model_for_standard_batch()

    def populate_table_model_for_modeler(self):
        """Populates the table model for the modeler dialog."""
        try:
            list_layers = self.get_list_layers_for_modeler()
        except KeyError:
            print("Error: no modeler wrapper found")
            return

        self.populate_table_model_with_data(list_layers)

    def populate_table_model_for_standard_batch(self):
        """Populates the table model for the standard batch dialog."""
        try:
            list_layers = self.get_list_layers_for_standard_batch()
        except KeyError:
            print("Error: no standard wrapper found")
            return

        self.populate_table_model_with_data(list_layers)

    def get_list_layers_for_modeler(self) -> "list[Tuple[str, str]]":
        """
        Get a list of tuples representing the input layers from the INPUTS_MATRIX parameter in modeler dialog.

        Each tuple contains a layer name and a layer ID. The layer ID is generated based on the type of input layer:
        - If the layer is a modeler input, the ID is the name of the input parameter.
        - If the layer is an algorithm output, the ID is a combination of the algorithm display name and the selected output name.

        Returns:
            A list of tuples, where each tuple contains a layer name and a layer ID.
        """
        # Initialize an empty list to hold layer names and IDs
        list_layers: "list[Tuple[str, str]]" = []

        # Iterate over the INPUTS_MATRIX widgets in the dialog
        for val in self.dialog.widget.widget.wrappers["INPUTS_MATRIX"].value():
            # Get the name of the current layer
            layer_name: str = self.dialog.resolveValueDescription(val)
            # Initialize layer_id to an empty string
            layer_id: str = ""
            # Get the algorithm child id of the current layer to check if it is a algorithm output
            childId = val.outputChildId()

            # Check if the current layer is a modeler input
            if isinstance(
                self.dialog.model.parameterDefinition(val.parameterName()),
                QgsProcessingParameterDefinition,
            ):
                # If it is, set layer_id to the name of the input parameter
                layer_id = self.dialog.model.parameterDefinition(
                    val.parameterName()
                ).name()

            # Check if the current layer is an algorithm output
            if childId:
                # If it is, get the algorithm associated with the output and generate a unique layer ID
                alg = self.dialog.model.childAlgorithm(val.outputChildId())
                # the layer ID is a combination of the algorithm display name and the selected output name
                # this string is the same than the one generated by context.expressionContext().indexOfScope("algorithm_inputs") in the algorithm preRun. Allows the matching of the layers in the processAlgorithm
                layer_id = f'{alg.algorithm().displayName().replace(" ", "_")}_{val.outputName()}'
            list_layers.append((layer_name, layer_id))

        return list_layers

    def get_list_layers_for_standard_batch(self) -> "list[Tuple[str, str]]":
        """
        Get a list of tuples representing the input layers from the INPUTS_MATRIX parameter in standard or batch dialog.

        Each tuple contains a layer name and an empty layer ID.

        Returns:
            A list of tuples, where each tuple contains a layer name and an empty layer ID.
        """
        list_layers: "list[Tuple[str, str]]" = []
        for val in (
            self.dialog.mainWidget().wrappers[self.alg.INPUTS_MATRIX].widgetValue()
        ):
            list_layers.append((val, ""))

        return list_layers

    def populate_table_model_with_data(self, list_layers: "list[Tuple[str, str]]"):
        """
        Populates the table model with data based on the given list of layers.

        Args:
            list_layers: A list of tuples, where each tuple contains a layer name (str) and a layer ID (str).

        Returns:
            None.
        """
        factor_elements: "list[CombineFactorElement]" = []

        # If the list of layers is empty, show an error message and return.
        if not list_layers:
            QMessageBox.critical(
                self, self.tr("Select rasters"), self.tr("No rasters selected")
            )
            return
        else:
            # For each layer in the list of layers, create a CombineFactorElement object and append it to the factor_elements list.
            for i, layer in enumerate(list_layers):
                if self.is_modeler_dialog:
                    layer_name = layer[0]
                    layer_path = ""
                else:
                    layer_name = ChloeUtils.deduceLayerName(layer[0])
                    layer_path = layer[0]

                factor_elements.append(
                    CombineFactorElement(
                        factor_name=f"m{i+1}",
                        layer_name=layer_name,
                        layer_path=Path(layer_path),
                        layer_id=layer[1],
                    ),
                )

        self._table_model.set_data(factor_elements)

    def value(self) -> Union["list[list[CombineFactorElement] |str]", None]:
        """
        Returns a list of CombineFactorElements representing the selected rasters, and the combination formula
        entered by the user. Returns None if the input is not valid.

        :return: list of CombineFactorElement and the formula, or None
        """

        # Check if the table model exists
        if self._table_model is None:
            return

        # Check for empty factor names and column duplicates
        empty_names = self._table_model.has_empty_layer_names()
        column_duplicates = self._table_model.has_column_duplicates()
        if empty_names or column_duplicates:
            return

        # Check for a valid formula
        formula = self.LineEditFormula.text()
        if not formula or not self.check_formula(formula):
            return

        # Return the list of factor elements and the formula
        return [
            self._table_model.get_combine_factor_elements(self.is_modeler_dialog),
            formula,
        ]

    def check_formula(self, formula: str) -> bool:
        if formula is None or formula == "":
            return False
        return True

    def setValue(self, value: "list[list[CombineFactorElement] | str]") -> None:
        """
        Set the value of the CombineTable and formula line edit.

        Args:
            value (list[list[CombineFactorElement] |str]): A list of lists, where each inner list is a list of
                CombineFactorElement objects, and a string formula, representing the current value of the widget.

            the first element should always be the list o CombineFactorElement, and the second one the formula
        """
        if value and len(value) > 1:
            self.LineEditFormula.setText(str(value[1]))
            self._table_model.set_data(value[0])
