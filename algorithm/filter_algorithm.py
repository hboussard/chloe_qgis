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

__author__ = 'Jean-Charles Naud/Alkante'
__date__ = '2017-10-17'


# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'


import os
import io
import subprocess
import time
from PyQt4.QtCore import QSettings
from qgis.core import QgsVectorFileWriter

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterMultipleInput, ParameterVector, ParameterRaster, ParameterTableField, ParameterNumber, ParameterBoolean, ParameterSelection, ParameterString, ParameterFile
from processing.core.outputs import OutputVector,OutputRaster, OutputFile, OutputDirectory
from processing.tools import dataobjects, vector

from processing.core.ProcessingConfig import ProcessingConfig
from processing.core.SilentProgress import SilentProgress
from processing.tools.system import getTempFilename, isWindows, isMac

from osgeo import osr
from time import gmtime, strftime

from ast import literal_eval


from PyQt4.QtGui import QIcon
from ..ChloeUtils import ChloeUtils
import tempfile
from processing.tools.system import isWindows


# Mother class
from .chloe_algorithm import CholeAlgorithm

# Master Dialog
from ..gui.FilterAlgorithmDialog import FilterAlgorithmDialog
from ..ChloeUtils import ASCOutputRaster


class FilterAlgorithm(CholeAlgorithm):
    """
    Algorithm using distance calculation
    """

    # Parameter specified
    INPUT_ASC     = 'INPUT_ASC'
    ASCII_FILTER  = 'ASCII_FILTER'
    FILTER_VALUES = 'FILTER_VALUES'

    SAVE_PROPERTIES = 'SAVE_PROPERTIES'
    OUTPUT_ASC      = 'OUTPUT_ASC'

    def getCustomParametersDialog(self):
        """Define Dialog associed with this algorithm"""
        return FilterAlgorithmDialog(self)

    def defineCharacteristics(self):
        """
        Algorithme variable and parameters parameters
        """
        CholeAlgorithm.defineCharacteristics(self)

        # The name that the user will see in the toolbox
        self.group      = 'util'
        self.i18n_group = self.tr('util')
        self.name       = 'filter'
        self.i18n_name  = self.tr('filter')

        # === INPUT PARAMETERS ===
        self.addParameter(ParameterRaster(
            name=self.INPUT_ASC,
            description=self.tr('Input layer')))

        self.addParameter(ParameterRaster(
            name=self.ASCII_FILTER,
            description=self.tr('Ascii Grid Filter')))
        
        self.addParameter(ParameterString(
            name=self.FILTER_VALUES, 
            description=self.tr('Filter value(s)'), 
            default=''
        ))

        # === OUTPUT PARAMETERS ===
        self.addOutput(OutputFile(
            name=self.SAVE_PROPERTIES,
            description=self.tr('Properties file'),
            ext='properties'))

        self.addOutput(ASCOutputRaster(
            name=self.OUTPUT_ASC,
            description=self.tr('Ouput Raster ascii')))
        

    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place"""

        # === INPUT
        self.input_asc = self.getParameterValue(self.INPUT_ASC).encode('utf-8')
        self.ascii_filter = self.getParameterValue(self.ASCII_FILTER).encode('utf-8')
        self.filter_values = self.getParameterValue(self.FILTER_VALUES)


        # === SAVE_PROPERTIES
        f_save_properties = self.getOutputValue(self.SAVE_PROPERTIES)
        if f_save_properties:
            self.f_path = f_save_properties
        else:
            if not self.f_path:
                self.f_path = getTempFilename(ext="properties")

        # === OUTPUT_ASC
        self.output_asc = self.getOutputValue(self.OUTPUT_ASC)

        # Constrution des chemins de sortie des fichiers
        base_in  = os.path.basename(self.input_asc)
        name_in  = os.path.splitext(base_in)[0]
        #ext_in  = os.path.splitext(base_in)[1]

        dir_out  = os.path.dirname(self.output_asc)
        base_out = os.path.basename(self.output_asc)
        name_out = os.path.splitext(base_out)[0]
        #ext_out = os.path.splitext(base_out)[1]

  
        # === Properties file
        self.createPropertiesTempFile() # Create Properties file (temp or chosed)

        # === CORE
        commands = self.getConsoleCommands()            # Get args command
        ChloeUtils.runChole(commands, progress)         # RUN

        # === Projection file
        f_prj = dir_out+os.sep+name_out+".prj"
        self.createProjectionFile(f_prj)

    def createPropertiesTempFile(self):
        """Create Properties File"""

        s_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        with open(self.f_path,"w") as fd:
            fd.write("#"+s_time+"\n")
            fd.write("treatment=filter\n")
            fd.write("visualize_ascii=false\n")
            fd.write( ChloeUtils.formatString('input_ascii='+self.input_asc +"\n",isWindows())) 
            fd.write( ChloeUtils.formatString('ascii_filter='+self.ascii_filter +"\n",isWindows())) 
            fd.write( ChloeUtils.formatString('output_asc=' +self.output_asc+"\n",isWindows())) 
            fd.write("filter_values={" + self.filter_values +"}\n")
