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
__author__ = 'Jean-Charles Naud/Alkante'
__date__ = '2017-10-17'


# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'


import os
import io
import subprocess
import time
from qgis.PyQt.QtCore import QSettings
from qgis.core import QgsVectorFileWriter

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterField,
    QgsProcessingParameterNumber,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterString,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFile,
    QgsProcessingOutputVectorLayer,
    QgsProcessingOutputRasterLayer,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterRasterDestination,
    QgsProcessingOutputFolder,
    QgsProcessingFeedback
)

from processing.tools import dataobjects, vector

from processing.core.ProcessingConfig import ProcessingConfig

from processing.tools.system import getTempFilename, isWindows, isMac

from osgeo import osr
from time import gmtime, strftime

from ast import literal_eval


from qgis.PyQt.QtGui import QIcon
from ..ChloeUtils import ChloeUtils
import tempfile


# Mother class
from ..chloe_algorithm import ChloeAlgorithm

# Main dialog
from .from_csv_algorithm_dialog import FromCSVAlgorithmDialog
from ..chloe_algorithm_dialog import ChloeASCParameterFileDestination

class FromCSVAlgorithm(ChloeAlgorithm):
    """
    Algorithm generate ascii grid from csv
    """
    alg_group = 'generate ascii grid'
    alg_name = 'from csv'

    def __init__(self):
        super().__init__()

    # def defineCharacteristics(self):
    #     """
    #     Algorithme variable and parameters parameters
    #     """
    #     ChloeAlgorithm.defineCharacteristics(self)
    #
    #     # The name/group that the user will see in the toolbox
    #     self.i18n_group = self.tr('generate ascii grid')
    #     self.i18n_name = self.tr('from csv')

    def createCustomParametersWidget(self, parent):
        return FromCSVAlgorithmDialog(self)

    def initAlgorithm(self, config=None):
        # === INPUT PARAMETERS ===
        self.addParameter(QgsProcessingParameterFeatureSource(
            name=self.INPUT_FILE_CSV,
            description=self.tr('Input file csv'),
            defaultValue=None,
            optional=False,
            types=[QgsProcessing.TypeVectorPoint]))

        # FIELDS
        fieldsParam = QgsProcessingParameterString(
            name=self.FIELDS,
            description=self.tr('Fields selection'),
            defaultValue='')
        fieldsParam.setMetadata({
            'widget_wrapper': {
                'class': 'Chloe.chloe_algorithm_dialog.ChloeFieldsFromCSVWidgetWrapper'
            },
            'output_asc_checked': True
            }
        )
        self.addParameter(fieldsParam)

        # N COLS
        self.addParameter(QgsProcessingParameterNumber(
            name=self.N_COLS,
            description=self.tr('Columns count'),
            minValue=0,
            defaultValue=100))
        self.addParameter(QgsProcessingParameterNumber(
            name=self.N_ROWS,
            description=self.tr('Rows count'),
            minValue=0,
            defaultValue=100))
        self.addParameter(QgsProcessingParameterNumber(
            name=self.XLL_CORNER,
            description=self.tr('X bottom left corner coordinate'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=0.0))
        self.addParameter(QgsProcessingParameterNumber(
            name=self.YLL_CORNER,
            type=QgsProcessingParameterNumber.Double,
            description=self.tr('Y bottom left corner coordinate'),
            defaultValue=0.0))
        self.addParameter(QgsProcessingParameterNumber(
            name=self.CELL_SIZE,
            type=QgsProcessingParameterNumber.Double,
            description=self.tr('Cell size'),
            defaultValue=1.0,
            minValue = 0.0))
        self.addParameter(QgsProcessingParameterNumber(
            name=self.NODATA_VALUE,
            description=self.tr('Value if no-data'),
            defaultValue=-1))

        # === OUTPUT PARAMETERS ===
        
        
        fieldsParam = ChloeASCParameterFileDestination(
            name=self.OUTPUT_ASC,
            description=self.tr('Output Raster ascii'))
        
        self.addParameter(fieldsParam, createOutput=True)

        self.addParameter(QgsProcessingParameterFileDestination(
            name=self.SAVE_PROPERTIES,
            description=self.tr('Properties file'),
            fileFilter='Properties (*.properties)'))
            
    def name(self):
        return 'from csv'

    def displayName(self):
        return self.tr('from csv')

    def group(self):
        return self.tr('generate ascii grid')

    def groupId(self):
        return 'generateasciigrid'

    def commandName(self):
        return 'from csv'

    def PreRun(self, parameters, context, feedback, executing=True):
        """Here is where the processing itself takes place."""
        print('processAlgorithm')
        # === INPUT
        self.input_csv = self.parameterAsString(
            parameters, self.INPUT_FILE_CSV, context)
        self.variables = self.parameterAsString(
            parameters, self.FIELDS, context)
        self.ncols = self.parameterAsInt(
            parameters, self.N_COLS, context)
        self.nrows = self.parameterAsInt(
            parameters, self.N_ROWS, context)
        self.xllcorner = self.parameterAsDouble(
            parameters, self.XLL_CORNER, context)
        self.yllcorner = self.parameterAsDouble(
            parameters, self.YLL_CORNER, context)
        self.cellsize = self.parameterAsInt(
            parameters, self.CELL_SIZE, context)
        self.nodata_value = self.parameterAsInt(
            parameters, self.NODATA_VALUE, context)

        # === OUTPUT
        self.output_asc = self.parameterAsString(
            parameters, self.OUTPUT_ASC, context)
        #self.output_asc = self.getOutputValue(self.OUTPUT_ASC)
        self.setOutputValue(self.OUTPUT_ASC, self.output_asc)

        # Constrution des chemins de sortie des fichiers
        base_in = os.path.basename(self.input_csv)
        name_in = os.path.splitext(base_in)[0]
        #ext_in  = os.path.splitext(base_in)[1]

        dir_out = os.path.dirname(self.output_asc)
        base_out = os.path.basename(self.output_asc)
        name_out = os.path.splitext(base_out)[0]
        #ext_out = os.path.splitext(base_out)[1]
        #feedback.pushInfo('self.f_path')

        # === SAVE_PROPERTIES
        f_save_properties = self.parameterAsString(
            parameters, self.SAVE_PROPERTIES, context)

        if f_save_properties:
            self.f_path = f_save_properties
        else:
            if not self.f_path:
                self.f_path = getTempFilename(ext="properties")

        # === Properties file
        self.createPropertiesTempFile()
         # Create Properties file (temp or chosed)

        # === CORE
        #commands = self.getConsoleCommandsJava(f_save_properties)

        #commands = self.getConsoleCommands(parameters, context, feedback, executing=True)
        #print('------- before')
        #ChloeUtils.runChole(commands, feedback)
        #print('------- after')
        # === Projection file
        f_prj = dir_out+os.sep+name_out+".prj"
        self.createProjectionFile(f_prj)

    def createPropertiesTempFile(self):
        """Create Properties File."""

        s_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        with open(self.f_path, "w+") as fd:
            fd.write("#"+s_time+"\n")
            fd.write("treatment=from csv\n")
            fd.write("visualize_ascii=false\n")
            fd.write(ChloeUtils.formatString(
                'input_csv='+self.input_csv+"\n", isWindows()))
            fd.write(ChloeUtils.formatString(
                'output_asc='+self.output_asc+"\n", isWindows()))
            fd.write("variables={" + self.variables + "}\n")
            fd.write("ncols=" + str(self.ncols) + "\n")
            fd.write("nrows=" + str(self.nrows) + "\n")
            fd.write("xllcorner=" + str(self.xllcorner) + "\n")
            fd.write("yllcorner=" + str(self.yllcorner) + "\n")
            fd.write("cellsize=" + str(self.cellsize) + "\n")
            fd.write("nodata_value=" + str(self.nodata_value) + "\n")
