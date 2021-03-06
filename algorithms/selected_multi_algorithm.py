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


class SelectedMultiAlgorithm(ChloeAlgorithm):
    """Algorithm selection multi."""

    def __init__(self):
        super().__init__()

    # def getCustomParametersDialog(self):
    #     """Define Dialog associed with this algorithm"""
    #     return SelectedMultiAlgorithmDialog(self)

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

        # WINDOW SHAPE
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

        # FRICTION FILE
        self.addParameter(QgsProcessingParameterFile(
            name=self.FRICTION_FILE,
            description=self.tr('Friction file'),
            optional=True))

        # WINDOW SIZE
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
        
        # POINT PIXEL
        pointPixelParam = QgsProcessingParameterEnum(
            name=self.PIXELS_POINTS_SELECT,
            description=self.tr('Pixels/points selection'),
            options=self.types_of_pixel_point_select)

        pointPixelParam.setMetadata({
            'widget_wrapper': {
                'class': 'Chloe.chloe_algorithm_dialog.ChloeEnumUpdateStateWidgetWrapper',
                'dependantWidgetConfig': [{ 
                    'paramName': self.PIXELS_FILE, 
                    'enableValue': 0 
                },
                { 
                    'paramName': self.POINTS_FILE, 
                    'enableValue': 1 
                }]
            }
        })
        
        self.addParameter(pointPixelParam)

        # PIXEL FILE
        self.addParameter(QgsProcessingParameterFile(
            name=self.PIXELS_FILE,
            description=self.tr('Pixels file'),
            optional=True))

        # POINT FILE
        self.addParameter(QgsProcessingParameterFile(
            name=self.POINTS_FILE,
            description=self.tr('Points file'),
            optional=True))

        # MAXIMUM RATE MISSING VALUE 
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
        return 'selected multi'

    def displayName(self):
        return self.tr('selected multi')

    def group(self):
        return self.tr('landscape metrics')

    def groupId(self):
        return 'landscapemetrics'

    def commandName(self):
        return 'selected multi'

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

        self.pixels_point_selection = self.parameterAsInt(
            parameters, self.PIXELS_POINTS_SELECT, context)

        self.pixels_file = self.parameterAsString(
            parameters, self.PIXELS_FILE, context)

        self.points_file = self.parameterAsString(
            parameters, self.POINTS_FILE, context)

        self.maximum_rate_missing_values = self.parameterAsString(
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
        """Create Properties File."""

        s_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        with open(self.f_path, "w") as fd:
            fd.write("#"+s_time+"\n")
            fd.write("treatment=selected\n")
            fd.write(ChloeUtils.formatString('input_ascii='
                                             + self.input_layer_asc+"\n", isWindows()))
            fd.write(ChloeUtils.formatString(
                'output_folder=' + self.output_dir + "\n", isWindows()))

            fd.write("window_sizes={" + self.window_sizes + "}\n")
            fd.write("maximum_nodata_value_rate="
                     + str(self.maximum_rate_missing_values) + "\n")
            
            if self.analyze_type == "weighted distance":
                fd.write("distance_function=" + str(self.distance_formula))
                
            fd.write("metrics={" + self.metrics + "}\n")

            fd.write("shape=" + str(self.window_shape) + "\n")
            if self.window_shape == "FUNCTIONAL":
                fd.write("friction_matrix=" + self.friction_file + "\n")
            if self.pixels_point_selection == 0:   # pixel(s) file
                fd.write("pixels=" + str(self.pixels_file) + "\n")
            elif self.pixels_point_selection == 1:  # point(s) file
                fd.write("points=" + str(self.points_file) + "\n")

            fd.write("visualize_ascii=false\n")

            fd.write("export_csv=true\n")
            fd.write("export_ascii=true\n")

    def deduceOutputFilenames(self):
        self.outputFilenames = []
        baseOutAsc = os.path.basename(self.input_layer_asc)
        radical = os.path.splitext(baseOutAsc)[0]
        for ws in self.window_sizes:
            for m  in self.metrics.split(';'):
                fName = radical + "_" + str(self.types_of_shape_abrev[self.window_shape]) + "_w" + str(ws) + "_" + str(m) + ".asc"
                fFullName = self.output_dir + os.sep + fName
                self.outputFilenames.append(fFullName)