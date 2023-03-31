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
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
)

from processing.tools.system import isWindows

from ..ChloeUtils import ChloeUtils

# Mother class
from ..chloe_algorithm import ChloeAlgorithm

# Main dialog
from .from_csv_algorithm_dialog import FromCSVAlgorithmDialog
from ..chloe_algorithm_dialog import ChloeParameterFolderDestination


class FromCSVAlgorithm(ChloeAlgorithm):
    """
    Algorithm generate ascii grid from csv
    """

    alg_group = "generate ascii grid"
    alg_name = "from csv"

    def __init__(self):
        super().__init__()

    def createCustomParametersWidget(self, parent):
        return FromCSVAlgorithmDialog(self)

    def initAlgorithm(self, config=None):

        # === INPUT PARAMETERS ===
        self.addParameter(
            QgsProcessingParameterFile(
                name=self.INPUT_FILE_CSV,
                description=self.tr("Input file csv"),
                extension="csv",
                defaultValue=None,
                optional=False,
            )
        )

        # FIELDS
        fieldsParam = QgsProcessingParameterString(
            name=self.FIELDS, description=self.tr("Fields selection"), defaultValue=""
        )
        fieldsParam.setMetadata(
            {
                "widget_wrapper": {
                    "class": "Chloe.chloe_algorithm_dialog.ChloeFieldsFromCSVWidgetWrapper"
                },
                "output_asc_checked": True,
            }
        )
        self.addParameter(fieldsParam)

        # N COLS
        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.N_COLS,
                description=self.tr("Columns count"),
                minValue=0,
                defaultValue=100,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.N_ROWS,
                description=self.tr("Rows count"),
                minValue=0,
                defaultValue=100,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.XLL_CORNER,
                description=self.tr("X bottom left corner coordinate"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.YLL_CORNER,
                type=QgsProcessingParameterNumber.Double,
                description=self.tr("Y bottom left corner coordinate"),
                defaultValue=0.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.CELL_SIZE,
                type=QgsProcessingParameterNumber.Double,
                description=self.tr("Cell size"),
                defaultValue=1.0,
                minValue=0.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.NODATA_VALUE,
                description=self.tr("Value if no-data"),
                defaultValue=-1,
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
        return "from csv"

    def displayName(self):
        return self.tr("from csv")

    def group(self):
        return self.tr("generate ascii grid")

    def groupId(self):
        return "generateasciigrid"

    def commandName(self):
        return "from csv"

    def PreRun(self, parameters, context, feedback, executing=True):
        """Here is where the processing itself takes place."""

        # === INPUT
        self.input_csv = self.parameterAsString(
            parameters, self.INPUT_FILE_CSV, context
        )
        self.variables = self.parameterAsString(parameters, self.FIELDS, context)
        self.ncols = self.parameterAsInt(parameters, self.N_COLS, context)
        self.nrows = self.parameterAsInt(parameters, self.N_ROWS, context)
        self.xllcorner = self.parameterAsDouble(parameters, self.XLL_CORNER, context)
        self.yllcorner = self.parameterAsDouble(parameters, self.YLL_CORNER, context)
        self.cellsize = self.parameterAsInt(parameters, self.CELL_SIZE, context)
        self.nodata_value = self.parameterAsInt(parameters, self.NODATA_VALUE, context)

        # === OUTPUT

        self.output_dir = self.parameterAsString(parameters, self.OUTPUT_DIR, context)
        ChloeUtils.adjustTempDirectory(self.output_dir)

        # Constrution des chemins de sortie des fichiers

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

        properties_lines.append("treatment=from csv\n")
        properties_lines.append(
            ChloeUtils.formatString(f"input_csv={self.input_csv}\n", isWindows())
        )
        properties_lines.append(
            ChloeUtils.formatString(f"output_folder={self.output_dir}\n", isWindows())
        )

        properties_lines.append(f"variables={{{self.variables}}}\n")
        properties_lines.append(f"ncols={str(self.ncols)}\n")
        properties_lines.append(f"nrows={str(self.nrows)}\n")
        properties_lines.append(f"xllcorner={str(self.xllcorner)}\n")
        properties_lines.append(f"yllcorner={str(self.yllcorner)}\n")
        properties_lines.append(f"cellsize={str(self.cellsize)}\n")
        properties_lines.append(f"nodata_value={str(self.nodata_value)}\n")
        # if multiple fields are selected set output_folder instead of output_asc
        # """if len(self.variables.split(';')) > 1:
        #     fd.write(ChloeUtils.formatString(
        #     'output_folder='+ re.sub('[^\/]+(?=\.).asc','',self.output_asc) + "\n", isWindows()))
        # else:
        #     fd.write(ChloeUtils.formatString(
        #     'output_asc='+self.output_asc+"\n", isWindows()))"""

        self.createPropertiesFile(properties_lines)

    def deduceOutputFilenames(self):
        self.outputFilenames = []
        baseOutAsc = os.path.basename(self.input_csv)
        radical = os.path.splitext(baseOutAsc)[0]
        lst_files = str(self.variables).split(";")
        for ws in lst_files:
            fName = radical + "_" + str(ws) + ".asc"
            fFullName = self.output_dir + os.sep + fName
            self.outputFilenames.append(fFullName)
