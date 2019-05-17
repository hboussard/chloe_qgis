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
from ..chloe_algorithm_dialog import ChloeASCParameterFileDestination

class CombineAlgorithm(ChloeAlgorithm):
    """
    Algorithm combine
    """

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        # === INPUT PARAMETERS ===
        self.addParameter(QgsProcessingParameterMultipleLayers(
            self.INPUTS_MATRIX,
            self.tr('Matrix to combine'),
            QgsProcessing.TypeRaster))

        # dummyData = []

        # for l in self.parameterAsLayerList(parameters, self.INPUTS_MATRIX, context):
        #     dummyData.append(l.source())

        # dummyData.append(('Populating', 'QtableWidget'))
 
        # dummyData.append(('With data', 'test'))
        
        # dummyData.append(('Is easy', 'test'))


        fieldsParam = QgsProcessingParameterString(
            name= self.DOMAINS,
            description=self.tr('New Factor'),
            defaultValue='')
        fieldsParam.setMetadata({
            'widget_wrapper': {
                'class': 'Chloe.chloe_algorithm_dialog.ChloeFactorTableWidgetWrapper',
                'input_matrix' : self.INPUTS_MATRIX
            }
        })
        self.addParameter(fieldsParam)
            

        # === OUTPUT PARAMETERS ===
        self.addParameter(QgsProcessingParameterFileDestination(
            name=self.SAVE_PROPERTIES,
            description=self.tr('Properties file'),
            fileFilter='Properties (*.properties)'))
        
        fieldsParam = ChloeASCParameterFileDestination(
            name=self.OUTPUT_ASC,
            description=self.tr('Ouput Raster ascii'))

        self.addParameter(fieldsParam, createOutput=True)

    def name(self):
        return 'combine'

    def displayName(self):
        return self.tr('combine')

    def group(self):
        return self.tr('util')

    def groupId(self):
        return 'util'

    def commandName(self):
        return 'combine'

    def PreRun(self, parameters, context, feedback, executing=True):
        """Here is where the processing itself takes place."""
        print('processAlgorithm')
        # === INPUT
        #self.inputs_matrix = self.parameterAsString(
        #    parameters, self.INPUTS_MATRIX, context)
        layers_str = []
        for l in self.parameterAsLayerList(parameters, self.INPUTS_MATRIX, context):
            layers_str.append(l.source())
        self.inputs_matrix = ';'.join(layers_str)
        
        # === OUTPUT
        self.output_asc = self.parameterAsString(
            parameters, self.OUTPUT_ASC, context)
        
        self.setOutputValue(self.OUTPUT_ASC, self.output_asc)

        # Constrution des chemins de sortie des fichiers
        dir_out = os.path.dirname(self.output_asc)
        base_out = os.path.basename(self.output_asc)
        name_out = os.path.splitext(base_out)[0]
        
        # === SAVE_PROPERTIES
        f_save_properties = self.parameterAsString(
            parameters, self.SAVE_PROPERTIES, context)

        if f_save_properties:
            self.f_path = f_save_properties
        else:
            if not self.f_path:
                self.f_path = getTempFilename(ext="properties")

        # === Properties files
        self.createPropertiesTempFile()
        
        # === Projection file
        f_prj = dir_out+os.sep+name_out+".prj"
        self.createProjectionFile(f_prj)

    def createPropertiesTempFile(self):
        """Create Properties File."""
        s_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        with open(self.f_path, "w+") as fd:
            fd.write("#"+s_time+"\n")
            fd.write('treatment=combine'+"\n")
            fd.write( ChloeUtils.formatString('factor={'+self.inputs_matrix+"}\n",isWindows()))  
            fd.write( ChloeUtils.formatString('output_asc=' +self.output_asc+"\n",isWindows()))
            fd.write("visualize_ascii=false\n")
