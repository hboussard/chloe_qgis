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
from processing.core.outputs import OutputVector,OutputRaster, OutputFile, OutputDirectory, OutputTable
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
from ..gui.ClusterAlgorithmDialog import ClusterAlgorithmDialog
from ..ChloeUtils import ASCOutputRaster


class ClusterAlgorithm(CholeAlgorithm):
    """
    Algorithm using distance calculation
    """

    # Parameter specified
    INPUT_ASC        = 'INPUT_ASC'
    CLUSTER          = 'CLUSTER'
    CLUSTER_DISTANCE = 'CLUSTER_DISTANCE'
    CLUSTER_TYPE     = 'CLUSTER_TYPE'
    CLUSTER_FRICTION = 'CLUSTER_FRICTION'
    
    SAVE_PROPERTIES  = 'SAVE_PROPERTIES'
    OUTPUT_CSV       = 'OUTPUT_CSV'
    OUTPUT_ASC       = 'OUTPUT_ASC'

    clusterTypes = ['rook neighbourhood', 'queen neighbourhood', 'euclidian distance', 'functional distance']

    def getCustomParametersDialog(self):
        """Define Dialog associed with this algorithm"""
        return ClusterAlgorithmDialog(self)


    def defineCharacteristics(self):
        """
        Algorithme variable and parameters parameters
        """
        CholeAlgorithm.defineCharacteristics(self)

        # The name/group that the user will see in the toolbox
        self.group      = 'util'
        self.i18n_group = self.tr('util')
        self.name       = 'cluster'
        self.i18n_name  = self.tr('cluster')

        # === INPUT PARAMETERS ===
        self.addParameter(ParameterRaster(
            name=self.INPUT_ASC,
            description=self.tr('Input layer')))

        self.addParameter(ParameterString(
            name = self.CLUSTER, 
            description = self.tr('Clusters from value(s)'), 
            default=''
        ))
        
        #name='', description='', options=[], default=None, isSource=False, optional=False):        
        self.addParameter(ParameterSelection(
            name = self.CLUSTER_TYPE, 
            description = self.tr('Cluster type'), 
            options = ';'.join(self.clusterTypes)
        ))

        self.addParameter(ParameterNumber(
            name = self.CLUSTER_DISTANCE, 
            description = self.tr('Distance in meters (only for euclidean and functional distance)'),
            optional = True
        ))

        self.addParameter(ParameterFile(
            name=self.CLUSTER_FRICTION,
            description=self.tr('Friction file'),
            isFolder=False,
            optional=True,
            ext='txt'))

        # === OUTPUT PARAMETERS ===
        self.addOutput(OutputFile(
            name=self.SAVE_PROPERTIES,
            description=self.tr('Properties file'),
            ext='properties'))

        self.addOutput(OutputTable(
            name=self.OUTPUT_CSV,
            description=self.tr('Output csv (*.csv)')))

        self.addOutput(ASCOutputRaster(
            name=self.OUTPUT_ASC,
            description=self.tr('Ouput Raster ascii')))
        

    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place"""

        # === INPUT_ASC
        # @inprogress test utf8 encoding strategy
        self.input_asc = self.getParameterValue(self.INPUT_ASC).encode('utf-8')
        
        # === VALUES_RANGES
        self.cluster = self.getParameterValue(self.CLUSTER)
        # retrieving cluster type as the first name of the cluster type name
        clusterTypeValue  = self.getParameterValue(self.CLUSTER_TYPE)
        self.cluster_type = self.clusterTypes[clusterTypeValue].split(' ')[0]
        
        self.cluster_distance = self.getParameterValue(self.CLUSTER_DISTANCE) if clusterTypeValue in [2,3] else None
        self.cluster_friction = self.getParameterValue(self.CLUSTER_FRICTION) if clusterTypeValue in [3] else None

        # === SAVE_PROPERTIES
        #f_save_properties = self.getParameterValue(self.SAVE_PROPERTIES)
        f_save_properties = self.getOutputValue(self.SAVE_PROPERTIES)
        if f_save_properties:
            self.f_path = f_save_properties
        else:
            if not self.f_path:
                self.f_path = getTempFilename(ext="properties")

        # === OUTPUT
        self.output_asc = self.getOutputValue(self.OUTPUT_ASC)
        self.output_csv = self.getOutputValue(self.OUTPUT_CSV)

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
            fd.write("treatment=cluster\n")
            fd.write("visualize_ascii=false\n")
            fd.write( ChloeUtils.formatString('input_ascii='+self.input_asc +"\n",isWindows()))  
            fd.write( ChloeUtils.formatString('output_asc=' +self.output_asc+"\n",isWindows()))  
            fd.write( ChloeUtils.formatString('output_csv=' +self.output_csv+"\n",isWindows()))
            fd.write("cluster={" + self.cluster +"}\n")
            fd.write("cluster_type=" + self.cluster_type + "\n")
            if not (self.cluster_distance is None):
                fd.write("cluster_distance=" + str(self.cluster_distance) + "\n")
            if not (self.cluster_friction is None):
                fd.write( ChloeUtils.formatString("cluster_friction=" + str(self.cluster_friction) + "\n",isWindows()))
