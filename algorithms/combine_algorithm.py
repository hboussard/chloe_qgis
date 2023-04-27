# -*- coding: utf-8 -*-

"""
/***************************************************************************
 Chole
                                 A QGIS plugin
 description
                              -------------------
        begin                : 2017-10-17
        author : Jean-Charles Naud, Olivier Bedel, Hugues Boussard, Daan Guillerme

        email                : hugues.boussard at inra.fr
 ***************************************************************************/

"""


__author__ = "Jean-Charles Naud/Alkante"
__date__ = "2017-10-17"


# This will get replaced with a git SHA1 when you do a git archive

__revision__ = "$Format:%H$"


import os
from pathlib import Path
from typing import Tuple
from ..helpers.dataclass import CombineFactorElement
from qgis.core import (
    QgsRasterLayer,
    QgsProcessing,
    QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterMatrix,
)

from processing.tools.system import isWindows

from ..ChloeUtils import ChloeUtils

# Mother class
from ..chloe_algorithm import ChloeAlgorithm
from ..chloe_algorithm_dialog import ChloeASCParameterFileDestination


class CombineAlgorithm(ChloeAlgorithm):
    """
    Algorithm combine
    """

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        # === INPUT PARAMETERS ===

        # INPUT MATRIX
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUTS_MATRIX, self.tr("Input rasters"), QgsProcessing.TypeRaster
            )
        )

        # COMBINE EXPRESSION
        combineParam = QgsProcessingParameterMatrix(
            name=self.DOMAINS, description=self.tr("Combination"), defaultValue=""
        )
        combineParam.setMetadata(
            {
                "widget_wrapper": {
                    "class": "Chloe.chloe_algorithm_dialog.ChloeFactorTableWidgetWrapper",
                    "input_matrix": self.INPUTS_MATRIX,
                    "parentWidgetConfig": {
                        "linkedParams": [
                            {
                                "paramName": self.INPUTS_MATRIX,
                                "refreshMethod": "refreshFactorTable",
                            },
                        ]
                    },
                }
            }
        )

        self.addParameter(combineParam)

        # === OUTPUT PARAMETERS ===

        # Output Asc
        fieldsParam = ChloeASCParameterFileDestination(
            name=self.OUTPUT_ASC, description=self.tr("Output Raster ascii")
        )

        self.addParameter(fieldsParam, createOutput=True)

        # Properties file
        self.addParameter(
            QgsProcessingParameterFileDestination(
                name=self.SAVE_PROPERTIES,
                description=self.tr("Properties file"),
                fileFilter="Properties (*.properties)",
            )
        )

    def name(self):
        return "combine"

    def displayName(self):
        return self.tr("Combine")

    def group(self):
        return self.tr("util")

    def groupId(self):
        return "util"

    def commandName(self):
        return "combine"

    def replace_empty_layer_path(
        self,
        factors: "list[CombineFactorElement]",
        scoped_raster_layers: "list[Tuple[QgsRasterLayer,str]]",
    ) -> "list[CombineFactorElement]":
        new_factors = []
        """this method replaces the empty Path provided by the domain parameter in MODELER mode. """
        # Loop through each factor
        for factor in factors:
            # If the factor's layer path is empty, search for the corresponding layer in the scoped raster_layers list
            if factor.layer_path == Path():
                # print(factor.layer_name)
                for raster_layer, input_name in scoped_raster_layers:
                    if factor.layer_id == input_name:
                        factor.layer_path = Path(raster_layer.source())

            new_factors.append(factor)

        return new_factors

    def get_scoped_layer_list(self, context) -> "list[Tuple[QgsRasterLayer,str]]":
        scope_layer_list: "list[Tuple[QgsRasterLayer,str]]" = []

        indexOfScope = context.expressionContext().indexOfScope("algorithm_inputs")
        if indexOfScope >= 0:
            expContextAlgInputsScope = context.expressionContext().scope(indexOfScope)
            for varName in expContextAlgInputsScope.variableNames():
                layerInContext = expContextAlgInputsScope.variable(varName)
                if isinstance(layerInContext, QgsRasterLayer):
                    # print(layerInContext)
                    # print(varName)
                    scope_layer_list.append((layerInContext, varName))

        return scope_layer_list

    def PreRun(self, parameters, context, feedback, executing=True):
        """Here is where the processing itself takes place."""

        # === INPUT

        input_factors: "list[list[CombineFactorElement] | str]" = (
            self.parameterAsMatrix(parameters, self.DOMAINS, context)
        )

        if not input_factors:
            feedback.reportError("Domain values are invalid")
            return False

        # get the layer ids
        scope_layer_list: "list[Tuple[QgsRasterLayer,str]]" = (
            self.get_scoped_layer_list(context=context)
        )

        # in case of MODELER the CombineFactorElement.layer_path is an empty Path().
        # The path of the raster layers are generated during prerun so the empty path values can be replaced by the values from the self.INPUTS_MATRIX parameter. Matching on the raster layers ids

        converted_input_factors: "list[CombineFactorElement]" = [
            CombineFactorElement.from_string(factor)
            if not isinstance(factor, CombineFactorElement)
            else factor
            for factor in input_factors[0]
        ]

        self.combination = input_factors[1]

        # replace the empty path with the actual ones
        self.input_asc: "list[CombineFactorElement]" = self.replace_empty_layer_path(
            converted_input_factors, scope_layer_list
        )
        # === OUTPUT

        self.output_asc = self.parameterAsOutputLayer(
            parameters, self.OUTPUT_ASC, context
        )

        self.setOutputValue(self.OUTPUT_ASC, self.output_asc)

        # Constrution des chemins de sortie des fichiers
        dir_out = os.path.dirname(self.output_asc)
        base_out = os.path.basename(self.output_asc)
        name_out = os.path.splitext(base_out)[0]

        # === SAVE_PROPERTIES
        f_save_properties = self.parameterAsString(
            parameters, self.SAVE_PROPERTIES, context
        )

        self.setOutputValue(self.SAVE_PROPERTIES, f_save_properties)

        # === Properties files
        self.createProperties()

        # === Projection file
        f_prj: str = f"{dir_out}{os.sep}{name_out}.prj"
        self.createProjectionFile(f_prj)

    def createProperties(self):
        """Create Properties File."""
        properties_lines: list[str] = []

        properties_lines.append(f"treatment=combine\n")
        properties_lines.append(f"combination={self.combination}\n")
        properties_lines.append(
            ChloeUtils.formatString(f"output_asc={self.output_asc}\n", isWindows())
        )

        input_asc: str = ";".join(
            [f"({factor.layer_path},{factor.factor_name})" for factor in self.input_asc]
        )

        properties_lines.append(
            ChloeUtils.formatString(f"factors={{{input_asc}}}\n", isWindows())
        )

        self.createPropertiesFile(properties_lines)
