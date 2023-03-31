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
    QgsProcessingParameterEnum,
    QgsProcessingParameterString,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
)


from processing.tools.system import isWindows


from ..ChloeUtils import ChloeUtils

# Mother class
from ..chloe_algorithm import ChloeAlgorithm
from ..chloe_algorithm_dialog import ChloeASCParameterFileDestination


class DistanceAlgorithm(ChloeAlgorithm):
    """
    Distance Algorithm
    """

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        # === INPUT PARAMETERS ===

        # Asc
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

        # VALUE RANGES
        fieldsParam = QgsProcessingParameterString(
            name=self.VALUES_RANGES, description=self.tr("Values"), defaultValue=""
        )
        fieldsParam.setMetadata(
            {
                "widget_wrapper": {
                    "class": "Chloe.chloe_algorithm_dialog.ChloeValuesWidgetWrapper"
                }
            }
        )
        self.addParameter(fieldsParam)

        # DISTANCE TYPE
        distanceTypeParam = QgsProcessingParameterEnum(
            name=self.DISTANCE_TYPE,
            description=self.tr("Distance type"),
            options=self.types_of_distance,
        )

        distanceTypeParam.setMetadata(
            {
                "widget_wrapper": {
                    "class": "Chloe.chloe_algorithm_dialog.ChloeEnumUpdateStateWidgetWrapper",
                    "dependantWidgetConfig": [
                        {"paramName": self.DISTANCE_FRICTION, "enableValue": 1}
                    ],
                }
            }
        )

        self.addParameter(distanceTypeParam)

        # FRICTION FILE

        distanceFrictionParam = QgsProcessingParameterFile(
            name=self.DISTANCE_FRICTION,
            description=self.tr("Friction file"),
            optional=True,
        )

        self.addParameter(distanceFrictionParam)
        # Max distance
        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.DISTANCE_MAX,
                description=self.tr("Maximum distance (in meters)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=None,
                minValue=1,
                optional=True,
            )
        )

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
        return "distance"

    def displayName(self):
        return self.tr("distance")

    def group(self):
        return self.tr("util")

    def groupId(self):
        return "util"

    def commandName(self):
        return "java"

    def PreRun(self, parameters, context, feedback, executing=True):
        """Here is where the processing itself takes place."""

        # === INPUT
        self.input_asc = self.parameterRasterAsFilePath(
            parameters, self.INPUT_ASC, context
        )
        self.values_ranges = self.parameterAsString(
            parameters, self.VALUES_RANGES, context
        )

        distanceTypeValue = self.parameterAsInt(parameters, self.DISTANCE_TYPE, context)
        self.distance_type = self.types_of_distance[distanceTypeValue].split(" ")[0]

        self.distance_friction = (
            self.parameterAsString(parameters, self.DISTANCE_FRICTION, context)
            if distanceTypeValue in [1]
            else None
        )

        self.distance_max = self.parameterAsInt(parameters, self.DISTANCE_MAX, context)
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

        # === Properties file
        self.createProperties()

        # === Projection file
        f_prj: str = f"{dir_out}{os.sep}{name_out}.prj"
        self.createProjectionFile(f_prj)

    def createProperties(self):
        """Create Properties File."""
        properties_lines: list[str] = []

        properties_lines.append("treatment=distance\n")
        properties_lines.append("distance_from={" + self.values_ranges + "}\n")
        properties_lines.append(
            ChloeUtils.formatString(f"input_ascii={self.input_asc}\n", isWindows())
        )
        properties_lines.append(
            ChloeUtils.formatString(f"output_asc={self.output_asc}\n", isWindows())
        )
        properties_lines.append(f"distance_type={self.distance_type}\n")
        if self.distance_max >= 1:
            properties_lines.append(f"max_distance={str(self.distance_max)}\n")
        if not (self.distance_friction is None):
            properties_lines.append(
                ChloeUtils.formatString(
                    f"distance_friction={str(self.distance_friction)}\n",
                    isWindows(),
                )
            )
        self.createPropertiesFile(properties_lines)
