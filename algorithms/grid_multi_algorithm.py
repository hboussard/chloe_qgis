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
import glob

from qgis.core import (
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
    QgsProcessingParameterFolderDestination,
    QgsProcessingParameterRasterDestination,
    QgsProcessingOutputFolder,
    QgsProcessingFeedback
)

from processing.tools.system import getTempFilename, isWindows, isMac
from time import gmtime, strftime
from ..ChloeUtils import ChloeUtils


# Mother class
from ..chloe_algorithm import ChloeAlgorithm
from ..chloe_algorithm_dialog import ChloeParameterFolderDestination

class GridMultiAlgorithm(ChloeAlgorithm):
    """Algorithm generate ascii grid from csv."""

    def __init__(self):
        super().__init__()

    # def getCustomParametersDialog(self):
    #     """Define Dialog associed with this algorithm."""
    #     return GridMultiAlgorithmDialog(self)

    def initAlgorithm(self, config=None):
        # === INPUT PARAMETERS ===
        # === INPUT PARAMETERS ===
        inputAscParam = QgsProcessingParameterRasterLayer(
            name=self.INPUT_LAYER_ASC,
            description=self.tr('Input layer asc'))

        inputAscParam.setMetadata({
            'widget_wrapper': {
                'class': 'Chloe.chloe_algorithm_dialog.ChloeAscRasterWidgetWrapper'
            }
        })
        self.addParameter(inputAscParam)

        gridSizeParam = QgsProcessingParameterString(
            name=self.GRID_SIZES,
            description=self.tr('Grid sizes (pixels)')) # [constraint V2.0: "select only one"]
        
        gridSizeParam.setMetadata({
            'widget_wrapper': {
                'class': 'Chloe.chloe_algorithm_dialog.ChloeIntListWidgetWrapper',
                'initialValue': 2,
                'maxValue' : 100001,
                'minValue' : 1,
                'oddNum' : None
            }
        })
        self.addParameter(gridSizeParam)

        metricsParam = QgsProcessingParameterString(
            name=self.METRICS,
            description=self.tr('Select metrics'))

        metricsParam.setMetadata({
            'widget_wrapper': {
                'class': 'Chloe.chloe_algorithm_dialog.ChloeMultipleMetricsSelectorWidgetWrapper',
                'dictValues': self.types_of_metrics,
                'initialValue': 'value metrics',
                'rasterLayerParamName': self.INPUT_LAYER_ASC,
                'parentWidgetConfig': { 'paramName': self.INPUT_LAYER_ASC, 'refreshMethod': 'refreshMetrics'}
            }
        })
        
        self.addParameter(metricsParam)

        self.addParameter(QgsProcessingParameterNumber(
            name=self.MAXIMUM_RATE_MISSING_VALUES,
            description=self.tr('Maximum rate of mising values'),
            minValue=0,
            maxValue=100,
            defaultValue=100))
            
        # === OUTPUT PARAMETERS ===
        self.addParameter(ChloeParameterFolderDestination(
            name=self.OUTPUT_DIR,
            description=self.tr('Output directory')))

        self.addParameter(QgsProcessingParameterFileDestination(
            name=self.SAVE_PROPERTIES,
            description=self.tr('Properties file'),
            fileFilter='Properties (*.properties)'))

    def name(self):
        return 'grid multi'

    def displayName(self):
        return self.tr('grid multi')

    def group(self):
        return self.tr('landscape metrics')

    def groupId(self):
        return 'landscapemetrics'

    def commandName(self):
        return 'grid multi'

    def PreRun(self, parameters, context, feedback, executing=True):
        """Here is where the processing itself takes place."""

        # === INPUT
        self.input_layer_asc = self.parameterRasterAsFilePath(
            parameters, self.INPUT_LAYER_ASC, context)
        self.grid_sizes = self.parameterAsString(
            parameters, self.GRID_SIZES, context)
        self.maximum_rate_missing_values = self.parameterAsInt(
            parameters, self.MAXIMUM_RATE_MISSING_VALUES, context)
        self.metrics = self.parameterAsString(
            parameters, self.METRICS, context)

        # === OUTPUT_LAYER
        self.output_dir = self.parameterAsString(
            parameters, self.OUTPUT_DIR, context)
        ChloeUtils.adjustTempDirectory(self.output_dir)

        base_in = os.path.basename(self.input_layer_asc)
        name_in = os.path.splitext(base_in)[0]
        ext_in = os.path.splitext(base_in)[1]

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

        # === output filenames
        self.deduceOutputFilenames()

    def createPropertiesTempFile(self):
        """Create Properties File."""

        s_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        with open(self.f_path, "w") as fd:
            fd.write("#"+s_time+"\n")
            fd.write("treatment=grid\n")
            fd.write(ChloeUtils.formatString(
                'input_ascii=' + self.input_layer_asc+"\n", isWindows()))
            fd.write(ChloeUtils.formatString(
                'output_folder=' + self.output_dir + "\n", isWindows()))

            fd.write("grid_sizes={" + self.grid_sizes + "}\n")
            fd.write("maximum_nodata_value_rate="
                     + str(self.maximum_rate_missing_values) + "\n")
            fd.write("metrics={" + self.metrics + "}\n")

            fd.write("visualize_ascii=false\n")

            fd.write("export_csv=true\n")
            fd.write("export_ascii=true\n")

    def deduceOutputFilenames(self):
        self.outputFilenames = []
        baseOutAsc = os.path.basename(self.input_layer_asc)
        radical = os.path.splitext(baseOutAsc)[0]
        for ws in self.grid_sizes:
            for m  in self.metrics.split(';'):
                fName = radical + "_g" + str(ws) + "_" + str(m) + ".asc"
                fFullName = self.output_dir + os.sep + fName
                self.outputFilenames.append(fFullName)