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
    QgsProcessingParameterDefinition,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingParameterFile,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFileDestination,
)

from processing.tools.system import isWindows

from ..ChloeUtils import ChloeUtils


# Mother class
from ..chloe_algorithm import ChloeAlgorithm
from ..chloe_algorithm_dialog import ChloeCSVParameterFileDestination
from ..chloe_algorithm_dialog import ChloeASCParameterFileDestination

# Main dialog


class SelectedAlgorithm(ChloeAlgorithm):
    """Algorithm selection."""

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
                    "class": "Chloe.chloe_algorithm_dialog.ChloeDoubleComboboxWidgetWrapper",
                    "dictValues": self.types_of_metrics,
                    "initialValue": "diversity metrics",
                    "rasterLayerParamName": self.INPUT_LAYER_ASC,
                    "parentWidgetConfig": {
                        "linkedParams": [
                            {
                                "paramName": self.INPUT_LAYER_ASC,
                                "refreshMethod": "refreshMappingCombobox",
                            },
                        ]
                    },
                }
            }
        )

        self.addParameter(metricsParam)

        # WINDOWS SIZE

        windowSizeParam = QgsProcessingParameterNumber(
            name=self.WINDOW_SIZES,
            description=self.tr("Windows sizes (pixels)"),
            defaultValue=3,
            minValue=3,
        )
        self.addParameter(windowSizeParam)

        # PIXELS POINTS SELECT

        pointPixelParam = QgsProcessingParameterEnum(
            name=self.PIXELS_POINTS_SELECT,
            description=self.tr("Pixels/points selection"),
            options=self.types_of_pixel_point_select,
        )

        self.addParameter(pointPixelParam)

        # PIXELS_POINTS FILE
        self.addParameter(
            QgsProcessingParameterFile(
                name=self.PIXELS_POINTS_FILE,
                description=self.tr("Pixels/points file"),
                optional=False,
            )
        )

        # === ADVANCED PARAMETERS ===

        # WINDOWS SHAPE

        windowShapeParam = QgsProcessingParameterEnum(
            name=self.WINDOW_SHAPE,
            description=self.tr("Window shape"),
            options=self.types_of_shape,
        )

        windowShapeParam.setMetadata(
            {
                "widget_wrapper": {
                    "class": "Chloe.chloe_algorithm_dialog.ChloeEnumUpdateStateWidgetWrapper",
                    "dependantWidgetConfig": [
                        {"paramName": self.FRICTION_FILE, "enableValue": 2}
                    ],
                }
            }
        )
        windowShapeParam.setFlags(
            windowShapeParam.flags() | QgsProcessingParameterDefinition.FlagAdvanced
        )
        self.addParameter(windowShapeParam)

        # FRICTION FILE
        frictionFile = QgsProcessingParameterFile(
            name=self.FRICTION_FILE, description=self.tr("Friction file"), optional=True
        )

        frictionFile.setFlags(
            frictionFile.flags() | QgsProcessingParameterDefinition.FlagAdvanced
        )

        self.addParameter(frictionFile)
        # ANALYZE TYPE

        analyzeTypeParam = QgsProcessingParameterEnum(
            name=self.ANALYZE_TYPE,
            description=self.tr("Analyze type"),
            options=self.types_of_analyze,
        )

        analyzeTypeParam.setMetadata(
            {
                "widget_wrapper": {
                    "class": "Chloe.chloe_algorithm_dialog.ChloeEnumUpdateStateWidgetWrapper",
                    "dependantWidgetConfig": [
                        {"paramName": self.DISTANCE_FUNCTION, "enableValue": 1}
                    ],
                }
            }
        )

        analyzeTypeParam.setFlags(
            analyzeTypeParam.flags() | QgsProcessingParameterDefinition.FlagAdvanced
        )
        self.addParameter(analyzeTypeParam)

        # DISTANCE FUNCTION

        distanceFunction = QgsProcessingParameterString(
            name=self.DISTANCE_FUNCTION,
            description=self.tr("Distance function"),
            defaultValue="exp(-pow(distance, 2)/pow(dmax/2, 2))",
            optional=True,
        )

        distanceFunction.setFlags(
            distanceFunction.flags() | QgsProcessingParameterDefinition.FlagAdvanced
        )

        self.addParameter(distanceFunction)

        # MAXIMUM RATE MISSING VALUES

        maxRateMissingValues = QgsProcessingParameterNumber(
            name=self.MAXIMUM_RATE_MISSING_VALUES,
            description=self.tr("Maximum rate of missing values"),
            minValue=0,
            maxValue=100,
            defaultValue=100,
        )
        maxRateMissingValues.setFlags(
            maxRateMissingValues.flags() | QgsProcessingParameterDefinition.FlagAdvanced
        )

        self.addParameter(maxRateMissingValues)

        # === OUTPUT PARAMETERS ===

        self.addParameter(
            ChloeCSVParameterFileDestination(
                name=self.OUTPUT_CSV, description=self.tr("Output csv")
            )
        )

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
        return "selected"

    def displayName(self):
        return self.tr("selected")

    def group(self):
        return self.tr("landscape metrics")

    def groupId(self):
        return "landscapemetrics"

    def commandName(self):
        return "selected"

    def PreRun(self, parameters, context, feedback, executing=True):
        """Here is where the processing itself takes place."""

        # === INPUT

        self.input_layer_asc = self.parameterRasterAsFilePath(
            parameters, self.INPUT_LAYER_ASC, context
        )

        self.window_shape = self.types_of_shape[
            self.parameterAsInt(parameters, self.WINDOW_SHAPE, context)
        ]

        self.friction_file = self.parameterAsString(
            parameters, self.FRICTION_FILE, context
        )

        self.window_sizes = self.parameterAsInt(parameters, self.WINDOW_SIZES, context)

        self.analyze_type = self.types_of_analyze[
            self.parameterAsInt(parameters, self.ANALYZE_TYPE, context)
        ]

        self.distance_formula = self.parameterAsString(
            parameters, self.DISTANCE_FUNCTION, context
        )

        self.pixels_point_selection = self.parameterAsInt(
            parameters, self.PIXELS_POINTS_SELECT, context
        )

        self.pixels_points_file = self.parameterAsString(
            parameters, self.PIXELS_POINTS_FILE, context
        )

        self.maximum_rate_missing_values = self.parameterAsInt(
            parameters, self.MAXIMUM_RATE_MISSING_VALUES, context
        )

        self.metrics = self.parameterAsString(parameters, self.METRICS, context)

        # === OUTPUT
        self.output_csv = self.parameterAsOutputLayer(
            parameters, self.OUTPUT_CSV, context
        )
        self.output_asc = self.parameterAsOutputLayer(
            parameters, self.OUTPUT_ASC, context
        )
        self.setOutputValue(self.OUTPUT_CSV, self.output_csv)
        self.setOutputValue(self.OUTPUT_ASC, self.output_asc)

        dir_out_asc = os.path.dirname(self.output_asc)
        base_out_asc = os.path.basename(self.output_asc)
        name_out_asc = os.path.splitext(base_out_asc)[0]
        # ext_out_asc     = os.path.splitext(base_out_asc)[1]

        # === SAVE_PROPERTIES
        f_save_properties = self.parameterAsString(
            parameters, self.SAVE_PROPERTIES, context
        )

        self.setOutputValue(self.SAVE_PROPERTIES, f_save_properties)

        # === Properties files
        self.createProperties()

        # === Projection file
        f_prj: str = f"{dir_out_asc}{os.sep}{name_out_asc}.prj"
        self.createProjectionFile(f_prj)

    def createProperties(self):
        """Create Properties File."""
        properties_lines: list[str] = []

        properties_lines.append(f"treatment={self.name()}\n")
        properties_lines.append(
            ChloeUtils.formatString(
                f"input_ascii={self.input_layer_asc}\n", isWindows()
            )
        )
        properties_lines.append(
            ChloeUtils.formatString(f"output_csv={self.output_csv}\n", isWindows())
        )
        properties_lines.append(
            ChloeUtils.formatString(f"output_asc={self.output_asc}\n", isWindows())
        )

        properties_lines.append(
            f"window_sizes={{{str(ChloeUtils.toOddNumber(self.window_sizes))}}}\n"
        )
        properties_lines.append(
            f"maximum_nodata_value_rate={str(self.maximum_rate_missing_values)}\n"
        )
        properties_lines.append(f"metrics={{{self.metrics}}}\n")

        if self.analyze_type == "weighted distance":
            properties_lines.append(f"distance_function={str(self.distance_formula)}\n")
        properties_lines.append(f"shape={str(self.window_shape)}\n")
        if self.window_shape == "FUNCTIONAL":
            properties_lines.append(f"friction={self.friction_file}\n")

        pixels_points_files = ChloeUtils.formatString(
            self.pixels_points_file, isWindows()
        )

        if self.pixels_point_selection == 0:  # pixel(s) file
            properties_lines.append(f"pixels={pixels_points_files}\n")
        elif self.pixels_point_selection == 1:  # point(s) file
            properties_lines.append(f"points={pixels_points_files}\n")

        # Writing the second part of the properties file
        if self.output_csv:
            properties_lines.append("export_csv=true\n")
        else:
            properties_lines.append("export_csv=false\n")

        if self.output_asc:
            properties_lines.append("export_ascii=true\n")
        else:
            properties_lines.append("export_ascii=false\n")

        self.createPropertiesFile(properties_lines)
