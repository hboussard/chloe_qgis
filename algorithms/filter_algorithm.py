# -*- coding: utf-8 -*-

"""
/***************************************************************************
 Chole
                                 A QGIS plugin
 description
                              -------------------
        begin                : 2017-10-17
        author : Jean-Charles Naud, Olivier Bedel, Hugues Boussard

        email                : hugues.boussard at inra.fr
 ***************************************************************************/

"""

__author__ = "Jean-Charles Naud/Alkante"
__date__ = "2017-10-17"


# This will get replaced with a git SHA1 when you do a git archive

__revision__ = "$Format:%H$"


import os

from qgis.core import (
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterString,
    QgsProcessingParameterFileDestination,
)

from processing.tools.system import isWindows

from ..ChloeUtils import ChloeUtils

# Mother class
from ..chloe_algorithm import ChloeAlgorithm
from ..chloe_algorithm_dialog import ChloeASCParameterFileDestination


class FilterAlgorithm(ChloeAlgorithm):
    """
    Algorithm filtering ascii grid
    """

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        # === INPUT PARAMETERS ===
        inputAscParam = QgsProcessingParameterRasterLayer(
            name=self.INPUT_ASC, description=self.tr("Input layer asc")
        )
        inputAscParam.setMetadata(
            {
                "widget_wrapper": {
                    "class": "Chloe.chloe_algorithm_dialog.ChloeAscRasterWidgetWrapper"
                }
            }
        )
        self.addParameter(inputAscParam)

        # ASCII FILTER
        ascFilterParam = QgsProcessingParameterRasterLayer(
            name=self.ASCII_FILTER, description=self.tr("Ascii Grid Filter")
        )
        ascFilterParam.setMetadata(
            {
                "widget_wrapper": {
                    "class": "Chloe.chloe_algorithm_dialog.ChloeAscRasterWidgetWrapper"
                }
            }
        )
        self.addParameter(ascFilterParam)

        # FILTER VALUES
        fieldsParam = QgsProcessingParameterString(
            name=self.FILTER_VALUES,
            description=self.tr("Filter value(s)"),
            defaultValue="",
        )
        fieldsParam.setMetadata(
            {
                "widget_wrapper": {
                    "class": "Chloe.chloe_algorithm_dialog.ChloeValuesWidgetWrapper",
                    "input_asc": self.ASCII_FILTER,
                }
            }
        )
        self.addParameter(fieldsParam)

        # === OUTPUT PARAMETERS ===

        fieldsParam = ChloeASCParameterFileDestination(
            name=self.OUTPUT_ASC, description=self.tr("Output Raster ascii")
        )

        self.addParameter(fieldsParam, createOutput=True)

        self.addParameter(
            QgsProcessingParameterFileDestination(
                name=self.SAVE_PROPERTIES,
                description=self.tr("Properties file"),
                fileFilter="Properties (*.properties)",
            )
        )

    def name(self):
        return "filter_chloe"

    def displayName(self):
        return self.tr("filter")

    def group(self):
        return self.tr("util")

    def groupId(self):
        return "util"

    def commandName(self):
        return "filter_chloe"

    def PreRun(self, parameters, context, feedback, executing=True):
        """Here is where the processing itself takes place."""

        # === INPUT
        self.input_asc = self.parameterRasterAsFilePath(
            parameters, self.INPUT_ASC, context
        )
        self.ascii_filter = self.parameterRasterAsFilePath(
            parameters, self.ASCII_FILTER, context
        )
        self.filter_values = self.parameterAsString(
            parameters, self.FILTER_VALUES, context
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

        properties_lines.append(f"treatment=filter\n")
        properties_lines.append(
            ChloeUtils.formatString(f"input_ascii={self.input_asc}\n", isWindows())
        )
        properties_lines.append(
            ChloeUtils.formatString(f"ascii_filter={self.ascii_filter}\n", isWindows())
        )
        properties_lines.append(
            ChloeUtils.formatString(f"output_asc={self.output_asc}\n", isWindows())
        )
        properties_lines.append(f"filter_values={{{self.filter_values}}}\n")

        self.createPropertiesFile(properties_lines)
