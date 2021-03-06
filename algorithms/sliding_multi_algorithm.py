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
    QgsProcessingParameterEnum,
    QgsProcessingOutputVectorLayer,
    QgsProcessingOutputRasterLayer,
    QgsProcessingOutputFolder,
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

class SlidingMultiAlgorithm(ChloeAlgorithm):
    """Algorithm sliding multi."""

    def __init__(self):
        super().__init__()

    # def getCustomParametersDialog(self):
    #     """Define Dialog associed with this algorithm"""
    #     return SlidingMultiAlgorithmDialog(self)

    def initAlgorithm(self, config=None):
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

        # ANALYZE TYPE

        analyzeTypeParam = QgsProcessingParameterEnum(
            name=self.ANALYZE_TYPE,
            description=self.tr('Analyze type'),
            options=self.types_of_analyze)

        analyzeTypeParam.setMetadata({
            'widget_wrapper': {
                'class': 'Chloe.chloe_algorithm_dialog.ChloeEnumUpdateStateWidgetWrapper',
                'dependantWidgetConfig': [{ 
                    'paramName': self.DISTANCE_FUNCTION, 
                    'enableValue': 1
                }]
            }
        })

        self.addParameter(analyzeTypeParam)

        # DISTANCE FUNCTION

        self.addParameter(QgsProcessingParameterString(
            name=self.DISTANCE_FUNCTION,
            description=self.tr('Distance function'),
            optional=True))

        windowShapeParam = QgsProcessingParameterEnum(
            name=self.WINDOW_SHAPE,
            description=self.tr('Window shape'),
            options=self.types_of_shape)

        windowShapeParam.setMetadata({
            'widget_wrapper': {
                'class': 'Chloe.chloe_algorithm_dialog.ChloeEnumUpdateStateWidgetWrapper',
                'dependantWidgetConfig': [{ 
                    'paramName': self.FRICTION_FILE, 
                    'enableValue': 2
                }]
            }
        })

        self.addParameter(windowShapeParam)

        self.addParameter(QgsProcessingParameterFile(
            name=self.FRICTION_FILE,
            description=self.tr('Friction file'),
            optional=True))

        windowSizeParam = QgsProcessingParameterString(
            name=self.WINDOW_SIZES,
            description=self.tr('Windows sizes (pixels)')) # [constraint V2.0: "select only one"]
        
        windowSizeParam.setMetadata({
            'widget_wrapper': {
                'class': 'Chloe.chloe_algorithm_dialog.ChloeIntListWidgetWrapper',
                'initialValue': 3,
                'minValue' : 3,
                'maxValue' : 100001,
                'oddNum' : True
            }
        })
        
        self.addParameter(windowSizeParam)
        
        self.addParameter(QgsProcessingParameterNumber(
            name=self.DELTA_DISPLACEMENT,
            description=self.tr('Delta displacement (pixels)'),
            defaultValue=1,
            minValue=1))

        self.addParameter(QgsProcessingParameterBoolean(
            name=self.INTERPOLATE_VALUES_BOOL,
            description=self.tr('Interpolate Values'),
            defaultValue=False))

        fieldsParam = QgsProcessingParameterString(
            name=self.FILTER,
            description=self.tr('Filters - Analyse only'),
            defaultValue='',
            optional=True)
        fieldsParam.setMetadata({
            'widget_wrapper': {
                'class': 'Chloe.chloe_algorithm_dialog.ChloeValuesWidgetWrapper'
            }
        })
        self.addParameter(fieldsParam)

        fieldsParam = QgsProcessingParameterString(
            name=self.UNFILTER,
            description=self.tr('Filters - Do not analyse'),
            defaultValue='',
            optional=True)
        fieldsParam.setMetadata({
            'widget_wrapper': {
                'class': 'Chloe.chloe_algorithm_dialog.ChloeValuesWidgetWrapper'
            }
        })
        self.addParameter(fieldsParam)

        self.addParameter(QgsProcessingParameterNumber(
            name=self.MAXIMUM_RATE_MISSING_VALUES,
            description=self.tr('Maximum rate of missing values'),
            minValue=0,
            maxValue=100,
            defaultValue=100))

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

        # === OUTPUT PARAMETERS ===
        
        self.addParameter(ChloeParameterFolderDestination(
            name=self.OUTPUT_DIR,
            description=self.tr('Output directory')))

        self.addParameter(QgsProcessingParameterFileDestination(
            name=self.SAVE_PROPERTIES,
            description=self.tr('Properties file'),
            fileFilter='Properties (*.properties)'))

    def name(self):
        return 'sliding multi'

    def displayName(self):
        return self.tr('sliding multi')

    def group(self):
        return self.tr('landscape metrics')

    def groupId(self):
        return 'landscapemetrics'

    def commandName(self):
        return 'sliding multi'

    def PreRun(self, parameters, context, feedback, executing=True):
        """Here is where the processing itself takes place."""

        # === INPUT
        self.input_layer_asc = self.parameterRasterAsFilePath(
            parameters, self.INPUT_LAYER_ASC, context)

        self.window_shape = self.types_of_shape[
            self.parameterAsInt(parameters, self.WINDOW_SHAPE, context)]
        self.friction_file = self.parameterAsString(
            parameters, self.FRICTION_FILE, context)
        self.window_sizes = self.parameterAsString(
            parameters, self.WINDOW_SIZES, context)

        self.analyze_type = self.types_of_analyze[
            self.parameterAsInt(parameters, self.ANALYZE_TYPE, context)]

        self.distance_formula = self.parameterAsString(parameters, self.DISTANCE_FUNCTION, context)

        self.delta_displacement = self.parameterAsInt(
            parameters, self.DELTA_DISPLACEMENT, context)
        self.b_interpolate_values = self.parameterAsBool(
            parameters, self.INTERPOLATE_VALUES_BOOL, context)

        self.filter = self.parameterAsString(
            parameters, self.FILTER, context)
        self.unfilter = self.parameterAsString(
            parameters, self.UNFILTER, context)

        self.maximum_rate_missing_values = self.parameterAsInt(
            parameters, self.MAXIMUM_RATE_MISSING_VALUES, context)
        self.metrics = self.parameterAsString(
            parameters, self.METRICS, context)

        # === OUTPUT
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
        """Create Properties File"""

        s_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        with open(self.f_path, "w") as fd:
            fd.write("#"+s_time+"\n")

            fd.write("treatment=sliding\n")
            fd.write(ChloeUtils.formatString(
                'input_ascii=' + self.input_layer_asc+"\n", isWindows()))

            fd.write(ChloeUtils.formatString(
                'output_folder=' + self.output_dir + "\n", isWindows()))

            fd.write("window_sizes={" + self.window_sizes + "}\n")
            fd.write("maximum_nodata_value_rate="
                     + str(self.maximum_rate_missing_values) + "\n")
                         
            if self.analyze_type == "weighted distance":
                fd.write("distance_function=" + str(self.distance_formula))

            fd.write("metrics={" + self.metrics + "}\n")
            fd.write("delta_displacement="
                     + str(self.delta_displacement) + "\n")
            fd.write("shape=" + str(self.window_shape) + "\n")
            if self.window_shape == "FUNCTIONAL":
                fd.write("friction_map=" + self.friction_file + "\n")

            if self.b_interpolate_values:
                fd.write("interpolation=true\n")
            else:
                fd.write("interpolation=false\n")

            if self.filter:
                fd.write("filters={" + self.filter + "}\n")
            if self.unfilter:
                fd.write("unfilters={" + self.unfilter + "}\n")

            fd.write("visualize_ascii=false\n")

            fd.write("export_csv=true\n")
            fd.write("export_ascii=true\n")

    def deduceOutputFilenames(self):
        self.outputFilenames = []
        baseOutAsc = os.path.basename(self.input_layer_asc)
        radical = os.path.splitext(baseOutAsc)[0]
        for ws in self.window_sizes:
            for m  in self.metrics.split(';'):
                fName = radical + "_" + str(self.types_of_shape_abrev[self.window_shape]) + "_w" + str(ws) + "_" + str(m) + "_d_" + str(self.delta_displacement) + ".asc"
                fFullName = self.output_dir + os.sep + fName
                self.outputFilenames.append(fFullName)