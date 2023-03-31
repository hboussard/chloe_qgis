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

import os

from qgis.core import (
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingParameterFileDestination,
)

from processing.tools.system import isWindows

from ..ChloeUtils import ChloeUtils


# Mother class
from ..chloe_algorithm import ChloeAlgorithm
from ..chloe_algorithm_dialog import ChloeParameterFolderDestination


class GridMultiAlgorithm(ChloeAlgorithm):
    """Algorithm generate ascii grid from csv."""

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

        # GRID SIZES
        gridSizeParam = QgsProcessingParameterString(
            name=self.GRID_SIZES, description=self.tr("Grid sizes (pixels)")
        )  # [constraint V2.0: "select only one"]

        gridSizeParam.setMetadata(
            {
                "widget_wrapper": {
                    "class": "Chloe.chloe_algorithm_dialog.ChloeIntListWidgetWrapper",
                    "initialValue": 2,
                    "maxValue": 100001,
                    "minValue": 2,
                }
            }
        )
        self.addParameter(gridSizeParam)

        # MAXIMUM RATE MISSING VALUES
        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.MAXIMUM_RATE_MISSING_VALUES,
                description=self.tr("Maximum rate of missing values"),
                minValue=0,
                maxValue=100,
                defaultValue=100,
            )
        )

        # === OUTPUT PARAMETERS ===
        self.addParameter(
            ChloeParameterFolderDestination(
                name=self.OUTPUT_DIR, description=self.tr("Output directory")
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
        return "grid multi"

    def displayName(self):
        return self.tr("grid multi")

    def group(self):
        return self.tr("landscape metrics")

    def groupId(self):
        return "landscapemetrics"

    def commandName(self):
        return "grid multi"

    def PreRun(self, parameters, context, feedback, executing=True):
        """Here is where the processing itself takes place."""

        # === INPUT
        self.input_layer_asc = self.parameterRasterAsFilePath(
            parameters, self.INPUT_LAYER_ASC, context
        )
        self.grid_sizes = self.parameterAsString(parameters, self.GRID_SIZES, context)
        self.maximum_rate_missing_values = self.parameterAsInt(
            parameters, self.MAXIMUM_RATE_MISSING_VALUES, context
        )
        self.metrics = self.parameterAsString(parameters, self.METRICS, context)

        # === OUTPUT_LAYER
        self.output_dir = self.parameterAsString(parameters, self.OUTPUT_DIR, context)
        ChloeUtils.adjustTempDirectory(self.output_dir)

        # === SAVE_PROPERTIES
        f_save_properties = self.parameterAsString(
            parameters, self.SAVE_PROPERTIES, context
        )

        self.setOutputValue(self.SAVE_PROPERTIES, f_save_properties)

        # === Properties files
        self.createProperties()

        # === output filenames
        self.deduceOutputFilenames()

    def createProperties(self):
        """Create Properties File."""
        properties_lines: list[str] = []

        properties_lines.append("treatment=grid\n")
        properties_lines.append(
            ChloeUtils.formatString(
                f"input_ascii={self.input_layer_asc}\n", isWindows()
            )
        )
        properties_lines.append(
            ChloeUtils.formatString(f"output_folder={self.output_dir}\n", isWindows())
        )

        properties_lines.append(f"grid_sizes={{{self.grid_sizes}}}\n")
        properties_lines.append(
            f"maximum_nodata_value_rate={str(self.maximum_rate_missing_values)}\n"
        )
        properties_lines.append(f"metrics={{{self.metrics}}}\n")

        properties_lines.append("export_csv=true\n")
        properties_lines.append("export_ascii=true\n")

        self.createPropertiesFile(properties_lines)

    def deduceOutputFilenames(self):
        self.outputFilenames = []
        baseOutAsc = os.path.basename(self.input_layer_asc)
        radical = os.path.splitext(baseOutAsc)[0]
        lst_files = str(self.grid_sizes).split(";")
        for ws in lst_files:
            for m in self.metrics.split(";"):
                fName = f"{radical}_g{str(ws)}_{str(m)}.asc"
                fFullName = self.output_dir + os.sep + fName
                self.outputFilenames.append(fFullName)
