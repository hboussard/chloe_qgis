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
    QgsProcessingFeedback,
    QgsProcessingParameterExtent
)

from processing.tools.system import getTempFilename, isWindows, isMac
from time import gmtime, strftime
from ..ChloeUtils import ChloeUtils

# Mother class
from ..chloe_algorithm import ChloeAlgorithm
from ..chloe_algorithm_dialog import ChloeASCParameterFileDestination

class FromShapefileAlgorithm(ChloeAlgorithm):
    """
    Algorithm generate ascii grid from shapefile
    """

    def __init__(self):
        super().__init__()

    # def createCustomParametersWidget(self, parent):
    #     return FromShapefileAlgorithmDialog(self, parent=parent)

    def initAlgorithm(self, config=None):
        # === INPUT PARAMETERS ===
        self.addParameter(QgsProcessingParameterFeatureSource ( #QgsProcessingParameterFeatureSource
            name=self.INPUT_SHAPEFILE,
            description=self.tr('Input vector layer'),
            optional=False))

        # FIELD
        self.addParameter(QgsProcessingParameterField(
            name=self.FIELD,
            description=self.tr('Field selection'),
            parentLayerParameterName=self.INPUT_SHAPEFILE,
            type=QgsProcessingParameterField.Any,
            optional=False))

        # LOOKUP TABLE
        self.addParameter(QgsProcessingParameterFile(
            name=self.LOOKUP_TABLE,
            description=self.tr('Lookup table'),
            optional=True))

        # CELL SIZE
        self.addParameter(QgsProcessingParameterNumber(
            name=self.CELL_SIZE,
            description=self.tr('Cell size'),
            type=QgsProcessingParameterNumber.Double,
            minValue=0,
            defaultValue=1.0))

        # EXTENT
        self.addParameter(QgsProcessingParameterExtent(
            name=self.EXTENT,
            description=self.tr('Region extent'),
            optional=True))

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
        return 'from shapefile'

    def displayName(self):
        return self.tr('from shapefile')

    def group(self):
        return self.tr('generate ascii grid')

    def groupId(self):
        return 'generateasciigrid'

    def commandName(self):
        return 'fromshapefile'

    def PreRun(self, parameters, context, feedback, executing=True):
        """Here is where the processing itself takes place."""

        # === INPUT
        self.input_shp = self.parameterAsString(
            parameters, self.INPUT_SHAPEFILE, context)
        if self.input_shp==None or self.input_shp=='' or not self.input_shp.endswith('.shp'):
            shp_layer = self.parameterAsVectorLayer(
                parameters, self.INPUT_SHAPEFILE, context)
            self.input_shp = shp_layer.dataProvider().dataSourceUri().split('|')[0]
        #print(self.parameterAsVectorLayer(
                #parameters, self.INPUT_SHAPEFILE, context).dataProvider().dataSourceUri().split('|')[0])

        self.field = self.parameterAsString(parameters, self.FIELD, context)
        self.lookup_table = self.parameterAsString(
            parameters, self.LOOKUP_TABLE, context)
        self.cellsize = self.parameterAsDouble(
            parameters, self.CELL_SIZE, context)
        self.extent = self.parameterAsExtent(parameters, self.EXTENT, context)

        # === OUTPUT
        self.output_asc = self.parameterAsString(
            parameters, self.OUTPUT_ASC, context)
        #self.output_asc = self.getOutputValue(self.OUTPUT_ASC)
        self.setOutputValue(self.OUTPUT_ASC, self.output_asc)

        # Constrution des chemins de sortie des fichiers
        base_in = os.path.basename(self.input_shp)
        name_in = os.path.splitext(base_in)[0]
        #ext_in  = os.path.splitext(base_in)[1]

        dir_out = os.path.dirname(self.output_asc)
        base_out = os.path.basename(self.output_asc)
        name_out = os.path.splitext(base_out)[0]
        #ext_out = os.path.splitext(base_out)[1]

        # === SAVE_PROPERTIES
        #f_save_properties = self.getParameterValue(self.SAVE_PROPERTIES)
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

        with open(self.f_path,"w") as fd:
            fd.write("#"+s_time+"\n")
            fd.write("treatment=from shapefile\n")
            fd.write("visualize_ascii=false\n")
            fd.write( ChloeUtils.formatString('input_shapefile='+self.input_shp+"\n",isWindows()))
            fd.write( ChloeUtils.formatString('output_asc='+self.output_asc+"\n",isWindows()))

            if self.lookup_table:
                fd.write("lookup_table="+self.lookup_table+"\n")
            fd.write("attribute="+self.field+"\n")
            fd.write("cellsizes={"+ str(self.cellsize)+"}\n")
            if not self.extent.isNull():
                fd.write("minx="    + str(self.extent.xMinimum()) + "\n")
                fd.write("maxx="    + str(self.extent.xMaximum()) + "\n")
                fd.write("miny="    + str(self.extent.yMinimum()) + "\n")
                fd.write("maxy="    + str(self.extent.yMaximum()) + "\n")
