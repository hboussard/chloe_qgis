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
    QgsProcessing,
    QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterFileDestination,
)

from processing.tools.system import isWindows

from time import gmtime, strftime

from ..ChloeUtils import ChloeUtils

# Mother class
from ..chloe_algorithm import ChloeAlgorithm
from ..chloe_algorithm_dialog import ChloeASCParameterFileDestination


class OverlayAlgorithm(ChloeAlgorithm):
    """
    Algorithm overlay
    """

    def __init__(self):

        super().__init__()

    def initAlgorithm(self, config=None):
        # === INPUT PARAMETERS ===
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUTS_MATRIX,
                self.tr("Matrix to overlay"),
                QgsProcessing.TypeRaster,
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
        return "overlay"

    def displayName(self):
        return self.tr("overlay")

    def group(self):
        return self.tr("util")

    def groupId(self):
        return "util"

    def commandName(self):
        return "overlay"

    def PreRun(self, parameters, context, feedback, executing=True):
        """Here is where the processing itself takes place."""

        # === INPUT
        # self.inputs_matrix = self.parameterAsString(
        #    parameters, self.INPUTS_MATRIX, context)
        layers_str = []
        for l in self.parameterAsLayerList(parameters, self.INPUTS_MATRIX, context):
            layers_str.append(l.source())
        self.inputs_matrix = ";".join(layers_str)

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
        f_save_properties: str = self.parameterAsString(
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

        properties_lines.append(f"treatment=overlay\n")
        properties_lines.append(
            ChloeUtils.formatString(
                f"overlaying_matrix={{{self.inputs_matrix}}}\n", isWindows()
            )
        )
        properties_lines.append(
            ChloeUtils.formatString(f"output_asc={self.output_asc}\n", isWindows())
        )
        self.createPropertiesFile(properties_lines)
