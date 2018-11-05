# -*- coding: utf-8 -*-

#####################################################################################################
# Chloe - landscape metrics
#
# Copyright 2018 URCAUE-Nouvelle Aquitaine
# Author(s) J-C. Naud, O. Bedel - Alkante (http://www.alkante.com) ;
#           H. Boussard - INRA UMR BAGAP (https://www6.rennes.inra.fr/sad)
# 
# Created on Mon Oct 22 2018
# This file is part of Chloe - landscape metrics.
# 
# Chloe - landscape metrics is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Chloe - landscape metrics is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Chloe - landscape metrics.  If not, see <http://www.gnu.org/licenses/>.
#####################################################################################################

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
from ..gui.ClassificationAlgorithmDialog import ClassificationAlgorithmDialog
from ..ChloeUtils import ASCOutputRaster

class ClassificationAlgorithm(CholeAlgorithm):
    """
    Algorithm using distance calculation
    """

    # Parameter specified
    INPUT_LAYER = 'INPUT_LAYER'
    DOMAINS = 'DOMAINS'

    SAVE_PROPERTIES = 'SAVE_PROPERTIES'
    OUTPUT_ASC = 'OUTPUT_ASC'

    def getCustomParametersDialog(self):
        """Define Dialog associed with this algorithm"""
        return ClassificationAlgorithmDialog(self)


    def defineCharacteristics(self):
        """
        Algorithme variable and parameters parameters
        """
        CholeAlgorithm.defineCharacteristics(self)

        # The name/group that the user will see in the toolbox
        self.group      = 'util'
        self.i18n_group = self.tr('util')
        self.name       = 'classification'
        self.i18n_name  = self.tr('classification')

        # === INPUT PARAMETERS ===
        self.addParameter(ParameterRaster(
            name=self.INPUT_LAYER,
            description=self.tr('Input layer')))

        self.addParameter(ParameterString(
            name=self.DOMAINS, 
            description=self.tr('New classification'),
            default=''))

        self.addOutput(OutputFile(
            name=self.SAVE_PROPERTIES,
            description=self.tr('Properties file'),
            ext='properties'))
                                  
        # === OUTPUT PARAMETERS ===
        self.addOutput(ASCOutputRaster(
            name=self.OUTPUT_ASC,
            description=self.tr('Ouput Raster ascii')))
        

    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place"""

        # === INPUT_LAYER
        self.input_asc = self.getParameterValue(self.INPUT_LAYER).encode('utf-8')
        
        # === VALUES_RANGES
        self.domains = self.getParameterValue(self.DOMAINS)

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
            fd.write("treatment=classification\n")
            fd.write("visualize_ascii=false\n")
            fd.write( ChloeUtils.formatString('input_ascii='+self.input_asc +"\n",isWindows()))  
            fd.write( ChloeUtils.formatString('output_asc=' +self.output_asc+"\n",isWindows()))
            fd.write("domains={" + self.domains + "}\n")
