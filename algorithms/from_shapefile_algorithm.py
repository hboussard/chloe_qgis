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
    QgsProcessingParameterField,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterExtent,
)

from processing.tools.system import isWindows

from ..ChloeUtils import ChloeUtils

# Mother class
from ..chloe_algorithm import ChloeAlgorithm
from ..chloe_algorithm_dialog import ChloeASCParameterFileDestination


class FromShapefileAlgorithm(ChloeAlgorithm):
    """
    Algorithm generate ascii grid from shapefile
    """

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        # === INPUT PARAMETERS ===
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                name=self.INPUT_SHAPEFILE,
                description=self.tr("Input vector layer"),
                optional=False,
            )
        )

        # FIELD
        self.addParameter(
            QgsProcessingParameterField(
                name=self.FIELD,
                description=self.tr("Field selection"),
                parentLayerParameterName=self.INPUT_SHAPEFILE,
                type=QgsProcessingParameterField.Any,
                optional=False,
            )
        )

        # LOOKUP TABLE
        self.addParameter(
            QgsProcessingParameterFile(
                name=self.LOOKUP_TABLE,
                description=self.tr("Lookup table"),
                optional=True,
            )
        )

        # CELL SIZE
        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.CELL_SIZE,
                description=self.tr("Cell size"),
                type=QgsProcessingParameterNumber.Double,
                minValue=0,
                defaultValue=1.0,
            )
        )

        # EXTENT
        self.addParameter(
            QgsProcessingParameterExtent(
                name=self.EXTENT, description=self.tr("Region extent"), optional=True
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
        return "from shapefile"

    def displayName(self):
        return self.tr("from shapefile")

    def group(self):
        return self.tr("generate ascii grid")

    def groupId(self):
        return "generateasciigrid"

    def commandName(self):
        return "fromshapefile"

    def PreRun(self, parameters, context, feedback, executing=True):
        """Here is where the processing itself takes place."""

        # === INPUT
        self.input_shp = self.parameterAsString(
            parameters, self.INPUT_SHAPEFILE, context
        )
        if (
            self.input_shp is None
            or self.input_shp == ""
            or not self.input_shp.endswith(".shp")
        ):
            shp_layer = self.parameterAsVectorLayer(
                parameters, self.INPUT_SHAPEFILE, context
            )
            self.input_shp = shp_layer.dataProvider().dataSourceUri().split("|")[0]

        self.field = self.parameterAsString(parameters, self.FIELD, context)
        self.lookup_table = self.parameterAsString(
            parameters, self.LOOKUP_TABLE, context
        )
        self.cellsize = self.parameterAsDouble(parameters, self.CELL_SIZE, context)
        self.extent = self.parameterAsExtent(parameters, self.EXTENT, context)

        # === OUTPUT
        self.output_asc = self.parameterAsOutputLayer(
            parameters, self.OUTPUT_ASC, context
        )

        self.setOutputValue(self.OUTPUT_ASC, self.output_asc)

        # Constrution des chemins de sortie des fichiers
        dir_out = os.path.dirname(self.output_asc)
        base_out = os.path.basename(self.output_asc)
        name_out = os.path.splitext(base_out)[0]
        # ext_out = os.path.splitext(base_out)[1]

        # === SAVE_PROPERTIES
        # f_save_properties = self.getParameterValue(self.SAVE_PROPERTIES)
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

        properties_lines.append("treatment=from shapefile\n")
        properties_lines.append(
            ChloeUtils.formatString(f"input_shapefile={self.input_shp}\n", isWindows())
        )
        properties_lines.append(
            ChloeUtils.formatString(f"output_asc={self.output_asc}\n", isWindows())
        )

        if self.lookup_table:
            properties_lines.append(f"lookup_table={self.lookup_table}\n")
        properties_lines.append(f"attribute={self.field}\n")
        properties_lines.append(f"cellsizes={{{str(self.cellsize)}}}\n")
        if not self.extent.isNull():
            properties_lines.append(f"minx={str(self.extent.xMinimum())}\n")
            properties_lines.append(f"maxx={str(self.extent.xMaximum())}\n")
            properties_lines.append(f"miny={str(self.extent.yMinimum())}\n")
            properties_lines.append(f"maxy={str(self.extent.yMaximum())}\n")

        self.createPropertiesFile(properties_lines)
