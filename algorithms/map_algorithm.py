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

from builtins import str

__author__ = "Jean-Charles Naud/Alkante"
__date__ = "2017-10-17"


# This will get replaced with a git SHA1 when you do a git archive

__revision__ = "$Format:%H$"

from qgis.core import (
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterString,
    QgsProcessingParameterFileDestination,
)

from processing.tools.system import isWindows

from ..ChloeUtils import ChloeUtils


# Mother class
from ..chloe_algorithm import ChloeAlgorithm
from ..chloe_algorithm_dialog import ChloeCSVParameterFileDestination

# Main dialog


class MapAlgorithm(ChloeAlgorithm):
    """Algorithm generate ascii grid from csv"""

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        # === INPUT PARAMETERS ===
        inputAscParam = QgsProcessingParameterRasterLayer(
            name=self.INPUT_LAYER_ASC, description=self.tr("Input layer asc")
        )

        inputAscParam.setMetadata(
            {
                "widget_wrapper": {
                    "class": "Chloe.chloe_algorithm_dialog.ChloeAscRasterWidgetWrapper"
                }
            }
        )
        self.addParameter(inputAscParam)

        # METRICS
        metricsParam = QgsProcessingParameterString(
            name=self.METRICS, description=self.tr("Select metrics")
        )

        metricsParam.setMetadata(
            {
                "widget_wrapper": {
                    "class": "Chloe.chloe_algorithm_dialog.ChloeMultipleMetricsSelectorWidgetWrapper",
                    "dictValues": self.types_of_metrics,
                    "initialValue": "diversity metrics",
                    "rasterLayerParamName": self.INPUT_LAYER_ASC,
                    "parentWidgetConfig": {
                        "linkedParams": [
                            {
                                "paramName": self.INPUT_LAYER_ASC,
                                "refreshMethod": "refreshMetrics",
                            },
                        ]
                    },
                }
            }
        )

        self.addParameter(metricsParam)

        # === OUTPUT PARAMETERS ===

        self.addParameter(
            ChloeCSVParameterFileDestination(
                name=self.OUTPUT_CSV, description=self.tr("Output csv")
            )
        )

        self.addParameter(
            QgsProcessingParameterFileDestination(
                name=self.SAVE_PROPERTIES,
                description=self.tr("Properties file"),
                fileFilter="Properties (*.properties)",
            )
        )

    def name(self):
        return "map"

    def displayName(self):
        return self.tr("map")

    def group(self):
        return self.tr("landscape metrics")

    def groupId(self):
        return "landscapemetrics"

    def commandName(self):
        return "map"

    def PreRun(self, parameters, context, feedback, executing=True):
        """Here is where the processing itself takes place."""

        # === INPUT_LAYER
        self.input_asc = self.parameterRasterAsFilePath(
            parameters, self.INPUT_LAYER_ASC, context
        )
        self.metrics = self.parameterAsString(parameters, self.METRICS, context)

        # === OUTPUT
        self.output_csv = self.parameterAsOutputLayer(
            parameters, self.OUTPUT_CSV, context
        )
        self.setOutputValue(self.OUTPUT_CSV, self.output_csv)

        # === SAVE_PROPERTIES
        f_save_properties = self.parameterAsString(
            parameters, self.SAVE_PROPERTIES, context
        )

        self.setOutputValue(self.SAVE_PROPERTIES, f_save_properties)

        # === Properties files
        self.createProperties()

    def createProperties(self):
        """Create Properties File."""
        properties_lines: list[str] = []

        properties_lines.append("treatment=map\n")
        properties_lines.append(
            ChloeUtils.formatString(f"input_ascii={self.input_asc}\n", isWindows())
        )
        properties_lines.append(
            ChloeUtils.formatString(f"output_csv={self.output_csv}\n", isWindows())
        )
        # Writing the second part of the properties file
        properties_lines.append(f"metrics={{{self.metrics}}}\n")

        self.createPropertiesFile(properties_lines)
