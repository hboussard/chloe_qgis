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
from processing.core.parameters import ParameterMultipleInput, ParameterExtent, ParameterVector, ParameterRaster, ParameterTableField, ParameterNumber, ParameterBoolean, ParameterSelection, ParameterString, ParameterFile, ParameterTable
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
from ..gui.FromShapefileAlgorithmDialog import FromShapefileAlgorithmDialog
from ..ChloeUtils import ASCOutputRaster


class FromShapefileAlgorithm(CholeAlgorithm):
    """
    Algorithm generate ascii grid from shapefile
    """

    # Paramaters
    INPUT_SHAPEFILE = 'INPUT_SHAPEFILE'
    FIELD           = 'FIELD'
    LOOKUP_TABLE    = 'LOOKUP_TABLE'
    CELL_SIZE       = 'CELL_SIZE'
    EXTENT          = 'EXTENT'

    SAVE_PROPERTIES = 'SAVE_PROPERTIES'
    OUTPUT_LAYER    = 'OUTPUT_LAYER'


    def getCustomParametersDialog(self):
        """Define Dialog associed with this algorithm"""
        return FromShapefileAlgorithmDialog(self)


    def defineCharacteristics(self):
        """
        Algorithme variable and parameters parameters
        """
        CholeAlgorithm.defineCharacteristics(self)

        # The name/group that the user will see in the toolbox
        self.group      = 'generate ascii grid'
        self.i18n_group = self.tr('generate ascii grid')
        self.name       = 'from shapefile'
        self.i18n_name  = self.tr('from shapefile')

        self.allowOnlyOpenedLayers = True

        # === INPUT PARAMETERS ===
        self.addParameter(ParameterVector(
            name=self.INPUT_SHAPEFILE,
            description=self.tr('Input vector layer'),
            #shapetype=[-1],
            optional=False))

        self.addParameter(ParameterFile(
            name=self.LOOKUP_TABLE,
            description=self.tr('Lookup table'),
            optional=True))

        self.addParameter(ParameterTableField(
            name=self.FIELD, 
            description=self.tr('Field selection'),
            parent=self.INPUT_SHAPEFILE,
            datatype=-1,
            optional=False))

        self.addParameter(ParameterNumber(
            name=self.CELL_SIZE,
            description=self.tr('Cell size'),
            minValue=0,
            default=1.0))

        self.addParameter(ParameterExtent(
            name=self.EXTENT,
            description=self.tr('Region extent'),
            optional=True))

        # === OUTPUT PARAMETERS === 
        self.addOutput(OutputFile(
            name=self.SAVE_PROPERTIES,
            description=self.tr('Properties file'), 
            ext='properties'))
        
        #self.addOutput(OutputRaster(self.OUTPUT_LAYER, self.tr('Result')))
        self.addOutput(ASCOutputRaster(
            name=self.OUTPUT_LAYER,
            description=self.tr('Ouput Raster ascii')))


    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place"""

        # === INPUT_LAYER
        # @inprogress test utf8 encoding strategy
        self.input_shp = self.getParameterValue(self.INPUT_SHAPEFILE.encode('utf-8')).encode('utf-8')

        self.field        = self.getParameterValue(self.FIELD.encode('utf-8'))
        self.lookup_table = self.getParameterValue(self.LOOKUP_TABLE.encode('utf-8')).encode('utf-8')
        self.cellsize     = self.getParameterValue(self.CELL_SIZE)
        self.extent       = self.getParameterValue(self.EXTENT)


        # === SAVE_PROPERTIES
        #f_save_properties = self.getParameterValue(self.SAVE_PROPERTIES)
        f_save_properties = self.getOutputValue(self.SAVE_PROPERTIES)
        if f_save_properties:
            self.f_path = f_save_properties
        else:
            if not self.f_path:
                self.f_path = getTempFilename(ext="properties")


        # === OUTPUT_LAYER
        self.output_asc = self.getOutputValue(self.OUTPUT_LAYER)
        
        # Constrution des chemins de sortie des fichiers
        base_in  = os.path.basename(self.input_shp)
        name_in  = os.path.splitext(base_in)[0]
        #ext_in  = os.path.splitext(base_in)[1]

        dir_out  = os.path.dirname(self.output_asc)
        base_out = os.path.basename(self.output_asc)
        name_out = os.path.splitext(base_out)[0]
        #ext_out = os.path.splitext(base_out)[1]
        
        f_prj = dir_out+os.sep+name_out+".prj"


        # === Properties file
        self.createPropertiesTempFile() # Create Properties file (temp or chosed)

        # === CORE
        commands = self.getConsoleCommands()            # Get args command
        ChloeUtils.runChole(commands, progress)         # RUN

        # === Projection file
        self.createProjectionFile(f_prj)


    def createPropertiesTempFile(self):
        """Create Properties File"""
        s_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())

        with open(self.f_path,"w") as fd:
            fd.write("#"+s_time+"\n")
            fd.write("treatment=from shapefile\n")
            fd.write("visualize_ascii=false\n")
            fd.write( ChloeUtils.formatString('input_shapefile='+self.input_shp+"\n",isWindows()))  
            fd.write( ChloeUtils.formatString('output_asc='+self.output_asc+"\n",isWindows()))

            if self.lookup_table:
                fd.write("lookup_table="+     self.lookup_table  + "\n")
            fd.write("attribute="   +     self.field         + "\n")
            fd.write("cellsizes={"  + str(self.cellsize)     +"}\n")
            if self.extent:
                tokens = unicode(self.extent).split(',')
                fd.write("minx="    + str(tokens[0]) + "\n")
                fd.write("maxx="    + str(tokens[1]) + "\n")
                fd.write("miny="    + str(tokens[2]) + "\n")
                fd.write("maxy="    + str(tokens[3]) + "\n")

