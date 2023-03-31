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
    QgsProcessingParameterBoolean,
    QgsProcessingParameterString,
    QgsProcessingParameterFile,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFileDestination,
)

from processing.tools.system import isWindows
from ..ChloeUtils import ChloeUtils


# Mother class
from ..chloe_algorithm import ChloeAlgorithm
from ..chloe_algorithm_dialog import ChloeParameterFolderDestination


class SlidingMultiAlgorithm(ChloeAlgorithm):
    """Algorithm sliding multi."""

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

        # WINDOWS SIZE
        windowSizeParam = QgsProcessingParameterString(
            name=self.WINDOW_SIZES, description=self.tr("Windows sizes (pixels)")
        )  # [constraint V2.0: "select only one"]

        windowSizeParam.setMetadata(
            {
                "widget_wrapper": {
                    "class": "Chloe.chloe_algorithm_dialog.ChloeIntListWidgetWrapper",
                    "initialValue": 3,
                    "minValue": 3,
                    "maxValue": 100001,
                    "oddNum": True,
                }
            }
        )

        self.addParameter(windowSizeParam)

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

        distanceFunctionParam = QgsProcessingParameterString(
            name=self.DISTANCE_FUNCTION,
            description=self.tr("Distance function"),
            defaultValue="exp(-pow(distance, 2)/pow(dmax/2, 2))",
            optional=True,
        )
        distanceFunctionParam.setFlags(
            distanceFunctionParam.flags()
            | QgsProcessingParameterDefinition.FlagAdvanced
        )
        self.addParameter(distanceFunctionParam)

        # DELTA DISPLACEMENT
        deltaDisplacement = QgsProcessingParameterNumber(
            name=self.DELTA_DISPLACEMENT,
            description=self.tr("Delta displacement (pixels)"),
            defaultValue=1,
            minValue=1,
        )
        deltaDisplacement.setFlags(
            deltaDisplacement.flags() | QgsProcessingParameterDefinition.FlagAdvanced
        )

        self.addParameter(deltaDisplacement)

        # INTERPOLATE VALUES BOOL
        interpolateValues = QgsProcessingParameterBoolean(
            name=self.INTERPOLATE_VALUES_BOOL,
            description=self.tr("Interpolate Values"),
            defaultValue=False,
        )
        interpolateValues.setFlags(
            interpolateValues.flags() | QgsProcessingParameterDefinition.FlagAdvanced
        )

        self.addParameter(interpolateValues)

        # FILTER PARAM
        # FILTER
        fieldsParamFilter = QgsProcessingParameterString(
            name=self.FILTER,
            description=self.tr("Filters - Analyse only"),
            defaultValue="",
            optional=True,
        )
        fieldsParamFilter.setMetadata(
            {
                "widget_wrapper": {
                    "class": "Chloe.chloe_algorithm_dialog.ChloeValuesWidgetWrapper",
                    "input_asc": self.INPUT_LAYER_ASC,
                }
            }
        )
        fieldsParamFilter.setFlags(
            fieldsParamFilter.flags() | QgsProcessingParameterDefinition.FlagAdvanced
        )
        self.addParameter(fieldsParamFilter)

        # UNFILTER
        fieldsParamUnfilter = QgsProcessingParameterString(
            name=self.UNFILTER,
            description=self.tr("Filters - Do not analyse"),
            defaultValue="",
            optional=True,
        )
        fieldsParamUnfilter.setMetadata(
            {
                "widget_wrapper": {
                    "class": "Chloe.chloe_algorithm_dialog.ChloeValuesWidgetWrapper",
                    "input_asc": self.INPUT_LAYER_ASC,
                }
            }
        )

        fieldsParamUnfilter.setFlags(
            fieldsParamUnfilter.flags() | QgsProcessingParameterDefinition.FlagAdvanced
        )
        self.addParameter(fieldsParamUnfilter)

        # MAX RATE MISSING VALUES
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
        return "sliding multi"

    def displayName(self):
        return self.tr("sliding multi")

    def group(self):
        return self.tr("landscape metrics")

    def groupId(self):
        return "landscapemetrics"

    def commandName(self):
        return "sliding multi"

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
        self.window_sizes = self.parameterAsString(
            parameters, self.WINDOW_SIZES, context
        )

        self.analyze_type = self.types_of_analyze[
            self.parameterAsInt(parameters, self.ANALYZE_TYPE, context)
        ]

        self.distance_formula = self.parameterAsString(
            parameters, self.DISTANCE_FUNCTION, context
        )

        self.delta_displacement = self.parameterAsInt(
            parameters, self.DELTA_DISPLACEMENT, context
        )
        self.b_interpolate_values = self.parameterAsBool(
            parameters, self.INTERPOLATE_VALUES_BOOL, context
        )

        self.filter = self.parameterAsString(parameters, self.FILTER, context)
        self.unfilter = self.parameterAsString(parameters, self.UNFILTER, context)

        self.maximum_rate_missing_values = self.parameterAsInt(
            parameters, self.MAXIMUM_RATE_MISSING_VALUES, context
        )
        self.metrics = self.parameterAsString(parameters, self.METRICS, context)

        # === OUTPUT
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
        """Create Properties File"""
        properties_lines: list[str] = []

        properties_lines.append("treatment=sliding\n")
        properties_lines.append(
            ChloeUtils.formatString(
                f"input_ascii={self.input_layer_asc}\n", isWindows()
            )
        )

        properties_lines.append(
            ChloeUtils.formatString(f"output_folder={self.output_dir}\n", isWindows())
        )

        properties_lines.append(f"window_sizes={{{str(self.window_sizes)}}}\n")
        properties_lines.append(
            f"maximum_nodata_value_rate={str(self.maximum_rate_missing_values)}\n"
        )

        if self.analyze_type == "weighted distance":
            properties_lines.append(f"distance_function={str(self.distance_formula)}\n")

        properties_lines.append(f"metrics={{{self.metrics}}}\n")
        properties_lines.append(f"delta_displacement={str(self.delta_displacement)}\n")
        properties_lines.append(f"shape={str(self.window_shape)}\n")
        if self.window_shape == "FUNCTIONAL":
            properties_lines.append(f"friction_map={self.friction_file}\n")

        if self.b_interpolate_values:
            properties_lines.append("interpolation=true\n")
        else:
            properties_lines.append("interpolation=false\n")

        if self.filter:
            properties_lines.append(f"filters={{{self.filter}}}\n")
        if self.unfilter:
            properties_lines.append(f"unfilters={{{self.unfilter}}}\n")

        properties_lines.append("export_csv=true\n")
        properties_lines.append("export_ascii=true\n")

        self.createPropertiesFile(properties_lines)

    def deduceOutputFilenames(self):
        self.outputFilenames = []
        baseOutAsc = os.path.basename(self.input_layer_asc)
        radical = os.path.splitext(baseOutAsc)[0]
        lst_files = str(self.window_sizes).split(";")
        for ws in lst_files:
            for m in self.metrics.split(";"):
                fName = f"{radical}_{str(self.types_of_shape_abrev[self.window_shape])}_w{str(ws)}_{str(m)}_d_{str(self.delta_displacement)}.asc"
                fFullName = self.output_dir + os.sep + fName
                self.outputFilenames.append(fFullName)
