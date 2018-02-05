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
from processing.core.parameters import ParameterMultipleInput, ParameterVector, ParameterRaster, ParameterTableField, ParameterNumber, ParameterBoolean, ParameterSelection, ParameterString, ParameterFile, ParameterTable
from processing.core.outputs import OutputVector,OutputRaster, OutputFile, OutputDirectory
from processing.tools import dataobjects, vector

from processing.core.ProcessingConfig import ProcessingConfig
from processing.core.SilentProgress import SilentProgress
from processing.tools.system import getTempFilename, isWindows, isMac

from osgeo import osr
from time import gmtime, strftime

from ast import literal_eval

# Tooling
from PyQt4.QtGui import QIcon
from ..ChloeUtils import ChloeUtils
import tempfile
from processing.tools.system import isWindows


from .chloe_algorithm         import CholeAlgorithm        # Mother(inheritance)
from ..gui.OverlayAlgorithmDialog import OverlayAlgorithmDialog    # Dialog
from ..ChloeUtils import ASCOutputRaster

class OverlayAlgorithm(CholeAlgorithm):
    """Algorithm generate ascii grid from csv"""

    # Paramaters
    INPUTS_MATRIX    = 'INPUTS_MATRIX'
    SAVE_PROPERTIES  = 'SAVE_PROPERTIES'
    OUTPUT_ASC       = 'OUTPUT_ASC'


    def getCustomParametersDialog(self):
        """Define Dialog associed with this algorithm"""
        return OverlayAlgorithmDialog(self)

    def defineCharacteristics(self):
        """Algorithme variable and parameters parameters"""

        CholeAlgorithm.defineCharacteristics(self)

        # The name/group that the user will see in the toolbox
        self.group      = 'util'
        self.i18n_group = self.tr('util')
        self.name       = 'overlay'
        self.i18n_name  = self.tr('overlay')

        # === INPUT PARAMETERS ===
        self.addParameter(ParameterMultipleInput(
            name=self.INPUTS_MATRIX,
            description=self.tr('Matrix to overlay'),
            datatype=3))

        # === OUTPUT PARAMETERS ===                                  
        self.addOutput(OutputFile(
            name=self.SAVE_PROPERTIES,
            description=self.tr('Properties file'),
            ext='properties'))
                                  
        self.addOutput(ASCOutputRaster(
            name=self.OUTPUT_ASC,
            description=self.tr('Output ascii (*.asc)')))

    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place"""

        # === INPUT_LAYER
        # @inprogress test utf8 encoding strategy
        self.inputs_matrix = self.getParameterValue(self.INPUTS_MATRIX).encode('utf-8')




        # === SAVE_PROPERTIES
        #f_save_properties = self.getParameterValue(self.SAVE_PROPERTIES)
        f_save_properties = self.getOutputValue(self.SAVE_PROPERTIES)
        if f_save_properties:
            self.f_path = f_save_properties
        else:
            if not self.f_path:
                self.f_path = getTempFilename(ext="properties")

        # === OUTPUT_LAYER
        self.output_asc      = self.getOutputValue(self.OUTPUT_ASC)

        ## Constrution des chemin de sortie des fiàchiers    
        dir_out_asc     = os.path.dirname(self.output_asc)
        base_out_asc    = os.path.basename(self.output_asc)
        name_out_asc    = os.path.splitext(base_out_asc)[0]
        #ext_out_asc     = os.path.splitext(base_out_asc)[1] 

        # === Properties file
        self.createPropertiesTempFile() # Create Properties file (temp or chosed)

        # === CORE
        commands = self.getConsoleCommands()            # Get args command
        ChloeUtils.runChole(commands, progress)         # RUN

        # === Projection file
        f_prj = dir_out_asc+os.sep+name_out_asc+".prj"
        self.createProjectionFile(f_prj)


    def createPropertiesTempFile(self):
        """Create Properties File"""

        s_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        with open(self.f_path,"w") as fd:
            fd.write("#"+s_time+"\n")
            fd.write("treatment=overlay\n")
            fd.write( ChloeUtils.formatString('overlaying_matrix={'+self.inputs_matrix+"}\n",isWindows()))
            fd.write( ChloeUtils.formatString('output_asc=' +self.output_asc +"\n",isWindows()))

            fd.write("visualize_ascii=false\n")
