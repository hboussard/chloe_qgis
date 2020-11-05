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

#from processing.core.GeoAlgorithm import GeoAlgorithm
#from processing.core.parameters import ParameterMultipleInput,
#  ParameterVector, ParameterRaster, ParameterTableField,
# ParameterNumber, ParameterBoolean, ParameterSelection,
# ParameterString, ParameterFile, ParameterTable
#from processing.core.outputs import OutputVector,OutputRaster,
#  OutputFile, OutputDirectory
#from processing.core.SilentProgress import SilentProgress

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterField,
    QgsProcessingParameterNumber,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
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
from ..chloe_algorithm_dialog import ChloeCSVParameterFileDestination
from ..chloe_algorithm_dialog import ChloeASCParameterFileDestination

class ClusterAlgorithm(ChloeAlgorithm):
    """
    Cluster Algorithm
    """

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):

        # === INPUT PARAMETERS ===

        inputAscParam = QgsProcessingParameterRasterLayer(
            name=self.INPUT_ASC,
            description=self.tr('Input layer asc'))

        inputAscParam.setMetadata({
            'widget_wrapper': {
                'class': 'Chloe.chloe_algorithm_dialog.ChloeAscRasterWidgetWrapper'
            }
        })
        self.addParameter(inputAscParam)

        # CLUSTER
        fieldsParam = QgsProcessingParameterString(
            name= self.CLUSTER,
            description=self.tr('Clusters from value(s)'),
            defaultValue='')
        fieldsParam.setMetadata({
            'widget_wrapper': {
                'class': 'Chloe.chloe_algorithm_dialog.ChloeValuesWidgetWrapper'
            }
        })
        self.addParameter(fieldsParam)

        # CLUSTER TYPE
        clusterTypeParam = QgsProcessingParameterEnum(
            self.CLUSTER_TYPE,
            self.tr('Cluster type'),
            self.types_of_cluster)

        self.addParameter(clusterTypeParam)

        clusterTypeParam.setMetadata({
            'widget_wrapper': {
                'class': 'Chloe.chloe_algorithm_dialog.ChloeMultiEnumUpdateStateWidgetWrapper',
                'dependantWidgetConfig': [{ 
                    'paramName': self.CLUSTER_DISTANCE, 
                    'enableValue': '2,3'
                }
                ,
                { 
                    'paramName': self.CLUSTER_FRICTION, 
                    'enableValue': '3'
                }]
            }
        })

        # CLUSTER DISTANCE
        self.addParameter(QgsProcessingParameterNumber(
            name=self.CLUSTER_DISTANCE,
            description=self.tr('Distance in meters (only for euclidean and functional distance)'),
            type=QgsProcessingParameterNumber.Double,
            optional=True,
            minValue = 0))

        # CLUSTER FRICTION
        self.addParameter(QgsProcessingParameterFile(
            name=self.CLUSTER_FRICTION,
            description=self.tr('Friction file'),
            optional=True))
        
        # CLUSTER MIN AREA
        self.addParameter(QgsProcessingParameterNumber(
            name = self.CLUSTER_MIN_AREA,
            description = self.tr('Minimal area (Ha)'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue = 0.0,
            minValue = 0.0))

            
        # === OUTPUT PARAMETERS ===     
        
        self.addParameter(ChloeCSVParameterFileDestination(
            name=self.OUTPUT_CSV,
            description=self.tr('Output csv (*.csv)')))
        
        
        fieldsParam = ChloeASCParameterFileDestination(
            name=self.OUTPUT_ASC,
            description=self.tr('Output Raster ascii'))

        self.addParameter(fieldsParam, createOutput=True)

        self.addParameter(QgsProcessingParameterFileDestination(
            name=self.SAVE_PROPERTIES,
            description=self.tr('Properties file'),
            fileFilter='Properties (*.properties)'))
            
    # ,fileFilter='ASCIIs (*.asc)'
    # def createCustomParametersWidget(self, parent):
    #     """Define Dialog associed with this algorithm"""
    #     return FromCSVAlgorithmDialog(self, parent=parent)

    def name(self):
        return 'cluster'

    def displayName(self):
        return self.tr('cluster')

    def group(self):
        return self.tr('util')

    def groupId(self):
        return 'util'

    def commandName(self):
        return 'java'

    def PreRun(self, parameters, context, feedback, executing=True):
        """Here is where the processing itself takes place."""
        print('processAlgorithm')
        # === INPUT
        self.input_asc = self.parameterRasterAsFilePath(
            parameters, self.INPUT_ASC, context)
        self.cluster = self.parameterAsString(
            parameters, self.CLUSTER, context)

        clusterTypeValue = self.parameterAsInt(
            parameters, self.CLUSTER_TYPE, context)
        self.cluster_type = self.types_of_cluster[clusterTypeValue].split(' ')[0]
        
        self.cluster_min_area = self.parameterAsString(
            parameters, self.CLUSTER_MIN_AREA, context)

        self.cluster_distance = self.parameterAsString(
            parameters, self.CLUSTER_DISTANCE, context)  if clusterTypeValue in [2,3] else None

        self.cluster_friction = self.parameterAsString(
            parameters, self.CLUSTER_FRICTION, context) if clusterTypeValue in [3] else None

        # === OUTPUT
        self.output_asc = self.parameterAsString(
            parameters, self.OUTPUT_ASC, context)
        
        self.output_csv = self.parameterAsString(
            parameters, self.OUTPUT_CSV, context)
        
        self.output_csv = ChloeUtils.adjustExtension(self.output_csv, self.output_asc)

        self.setOutputValue(self.OUTPUT_ASC, self.output_asc)
        self.setOutputValue(self.OUTPUT_CSV, self.output_csv)

        # Constrution des chemins de sortie des fichiers
        base_in = os.path.basename(self.input_asc)
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
            fd.write("treatment=cluster\n")
            fd.write("visualize_ascii=false\n")
            fd.write( ChloeUtils.formatString('input_ascii='+self.input_asc +"\n",isWindows()))  
            fd.write( ChloeUtils.formatString('output_asc=' +self.output_asc+"\n",isWindows()))  
            fd.write( ChloeUtils.formatString('output_csv=' +self.output_csv+"\n",isWindows()))
            fd.write( ChloeUtils.formatString('minimum_total_area=' +self.cluster_min_area+"\n",isWindows()))
            fd.write("cluster={" + self.cluster +"}\n")
            fd.write("cluster_type=" + self.cluster_type + "\n")
            if not (self.cluster_distance is None):
                fd.write("cluster_distance=" + str(self.cluster_distance) + "\n")
            if not (self.cluster_friction is None):
                fd.write(ChloeUtils.formatString("cluster_friction=" + str(self.cluster_friction) + "\n",isWindows()))
            fd.write("minimum_total_area=" + self.cluster_min_area + "\n")