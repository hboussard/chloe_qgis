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

class SearchAndReplaceAlgorithm(ChloeAlgorithm):
    """
    Algorithm search and replace
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

        # MAP CSV
        fieldsParam = QgsProcessingParameterFile(
            name=self.MAP_CSV,
            description=self.tr('CSV Map'),
            optional=True)
        fieldsParam.setMetadata({
            'widget_wrapper': {
                'class': 'Chloe.chloe_algorithm_dialog.ChloeCsvTxtFileWidgetWrapper',
                'fileExtensions': ['csv','txt']
            }
        })
        self.addParameter(fieldsParam)

        # CHANGES
        fieldsParam = QgsProcessingParameterString(
            name= self.CHANGES,
            description=self.tr('Values to search and replace'),
            defaultValue='')
        fieldsParam.setIsDynamic(True)
        fieldsParam.setDynamicLayerParameterName('INPUT_ASC')
        #m_param.setDynamicPropertyDefinition(QgsPropertyDefinition(self.M_VALUE, self.tr("M Value"), QgsPropertyDefinition.Double))

        fieldsParam.setMetadata({
            'widget_wrapper': {
                'class': 'Chloe.chloe_algorithm_dialog.ChloeMappingTableWidgetWrapper',
                'parentWidgetConfig': { 'paramName': self.MAP_CSV, 'refreshMethod': 'refreshMappingCombobox', 'paramName2': self.INPUT_ASC, 'refreshMethod2':'emptyMappingAsc'}
            }
        })
        self.addParameter(fieldsParam)

        # NO DATA VALUE
        self.addParameter(QgsProcessingParameterNumber(
            name=self.NODATA_VALUE, 
            description=self.tr('Nodata value'),
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
        return 'search and replace'

    def displayName(self):
        return self.tr('search and replace')

    def group(self):
        return self.tr('util')

    def groupId(self):
        return 'util'

    def commandName(self):
        return 'search and replace'

    def PreRun(self, parameters, context, feedback, executing=True):
        """Here is where the processing itself takes place."""
        print('processAlgorithm')
        # === INPUT
        self.input_asc = self.parameterRasterAsFilePath(
            parameters, self.INPUT_ASC, context)
        self.map_csv = self.parameterAsString(
            parameters, self.MAP_CSV, context)
        self.changes = self.parameterAsString(
            parameters, self.CHANGES, context)
        self.nodata_value = self.parameterAsString(
            parameters, self.NODATA_VALUE, context)

        # === OUTPUT
        self.output_asc = self.parameterAsString(
            parameters, self.OUTPUT_ASC, context)
        
        self.setOutputValue(self.OUTPUT_ASC, self.output_asc)

        # Constrution des chemins de sortie des fichiers
        base_in = os.path.basename(self.input_asc)
        name_in = os.path.splitext(base_in)[0]

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

        # === Properties file
        self.createPropertiesTempFile()
    
        # === Projection file
        f_prj = dir_out+os.sep+name_out+".prj"
        self.createProjectionFile(f_prj)

    def createPropertiesTempFile(self):
        """Create Properties File."""
        s_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        with open(self.f_path, "w+") as fd:
            fd.write("#"+s_time+"\n")
            fd.write('treatment=search and replace'+"\n")
            fd.write( ChloeUtils.formatString('input_ascii='+self.input_asc +"\n",isWindows()))
            fd.write( ChloeUtils.formatString('output_asc=' +self.output_asc+"\n",isWindows()))
            fd.write('changes={'+self.changes+"}\n")
            fd.write('nodata_value='+str(self.nodata_value)+"\n")
            fd.write("visualize_ascii=false\n")
