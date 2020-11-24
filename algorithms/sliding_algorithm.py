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
    QgsProcessingParameterDefinition,
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
    QgsProcessingParameterRasterDestination,
    QgsProcessingOutputFolder,
    QgsProcessingFeedback
)

from processing.tools.system import getTempFilename, isWindows, isMac
from time import gmtime, strftime
from ..ChloeUtils import ChloeUtils


# Mother class
from ..chloe_algorithm import ChloeAlgorithm
from ..chloe_algorithm_dialog import ChloeCSVParameterFileDestination
from ..chloe_algorithm_dialog import ChloeASCParameterFileDestination
# Main dialog
#from .sliding_algorithm_dialog import SlidingAlgorithmDialog


class SlidingAlgorithm(ChloeAlgorithm):
    """Algorithm sliding."""

    def __init__(self):
        super().__init__()

    # def getCustomParametersDialog(self):
    #     """Define Dialog associed with this algorithm"""
    #     return SlidingAlgorithmDialog(self)

    def initAlgorithm(self, config=None):
        # === INPUT PARAMETERS ===

        # INPUT ASC
        inputAscParam = QgsProcessingParameterRasterLayer(
            name=self.INPUT_ASC,
            description=self.tr('Input layer asc'))

        inputAscParam.setMetadata({
            'widget_wrapper': {
                'class': 'Chloe.chloe_algorithm_dialog.ChloeAscRasterWidgetWrapper'
            }
        })
        self.addParameter(inputAscParam)

        # METRICS

        metricsParam = QgsProcessingParameterString(
            name=self.METRICS,
            description=self.tr('Select metrics'))

        metricsParam.setMetadata({
            'widget_wrapper': {
                'class': 'Chloe.chloe_algorithm_dialog.ChloeDoubleComboboxWidgetWrapper',
                'dictValues': self.types_of_metrics,
                'initialValue': 'diversity metrics',
                'rasterLayerParamName': self.INPUT_ASC,
                'parentWidgetConfig': { 'paramName': self.INPUT_ASC, 'refreshMethod': 'refreshMappingCombobox'}
            }
        })
        
        self.addParameter(metricsParam)

        ###### ADVANCED PARAMETERS ######

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
        
        windowShapeParam.setFlags(windowShapeParam.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(windowShapeParam)

        # FRICTION FILE (OPTIONAL)

        frictionFile = QgsProcessingParameterFile(
            name=self.FRICTION_FILE,
            description=self.tr('Friction file'),
            optional=True)

        frictionFile.setFlags(frictionFile.flags() | QgsProcessingParameterDefinition.FlagAdvanced)

        self.addParameter(frictionFile)

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
        analyzeTypeParam.setFlags(analyzeTypeParam.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(analyzeTypeParam)

        # DISTANCE FUNCTION

        distanceFunctionParam = QgsProcessingParameterString(
            name=self.DISTANCE_FUNCTION,
            description=self.tr('Distance function'),
            optional=True)
        distanceFunctionParam.setFlags(distanceFunctionParam.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(distanceFunctionParam)
        
        # DELTA DISPLACEMENT
        deltaDisplacement = QgsProcessingParameterNumber(
            name=self.DELTA_DISPLACEMENT,
            description=self.tr('Delta displacement (pixels)'),
            defaultValue=1,
            minValue=1)
        deltaDisplacement.setFlags(deltaDisplacement.flags() | QgsProcessingParameterDefinition.FlagAdvanced)

        self.addParameter(deltaDisplacement)


        # INTERPOLATE VALUES BOOL
        interpolateValues = QgsProcessingParameterBoolean(
            name=self.INTERPOLATE_VALUES_BOOL,
            description=self.tr('Interpolate Values'),
            defaultValue=False)
        interpolateValues.setFlags(interpolateValues.flags() | QgsProcessingParameterDefinition.FlagAdvanced)

        self.addParameter(interpolateValues)


        # FILTER
        fieldsParamFilter = QgsProcessingParameterString(
            name=self.FILTER,
            description=self.tr('Filters - Analyse only'),
            defaultValue='',
            optional=True)
        fieldsParamFilter.setMetadata({
            'widget_wrapper': {
                'class': 'Chloe.chloe_algorithm_dialog.ChloeValuesWidgetWrapper'
            }
        })
        fieldsParamFilter.setFlags(fieldsParamFilter.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(fieldsParamFilter)


        # UNFILTER
        fieldsParamUnfilter = QgsProcessingParameterString(
            name=self.UNFILTER,
            description=self.tr('Filters - Do not analyse'),
            defaultValue='',
            optional=True)
        fieldsParamUnfilter.setMetadata({
            'widget_wrapper': {
                'class': 'Chloe.chloe_algorithm_dialog.ChloeValuesWidgetWrapper'
            }
        })

        fieldsParamUnfilter.setFlags(fieldsParamUnfilter.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(fieldsParamUnfilter)

        # MAX RATE MISSING VALUES
        maxRateMissingValues = QgsProcessingParameterNumber(
            name=self.MAXIMUM_RATE_MISSING_VALUES,
            description=self.tr('Maximum rate of missing values'),
            minValue=0,
            maxValue=100,
            defaultValue=100)
        maxRateMissingValues.setFlags(maxRateMissingValues.flags() | QgsProcessingParameterDefinition.FlagAdvanced)

        self.addParameter(maxRateMissingValues)

        # WINDOW SIZE
        
        ''' USING Odd Even Spinbox wrapper
        windowSizeParam = QgsProcessingParameterNumber(
            name=self.WINDOW_SIZES,
            description=self.tr('Windows sizes (pixels)')            
        )
        windowSizeParam.setMetadata({
            'widget_wrapper': {
                'class': 'Chloe.chloe_algorithm_dialog.ChloeIntSpinboxWrapper',
                'initialValue' : 3,
                'minValue' : 3,
                'maxValue' : 100001,
                'oddNum' : True
            }
        })
    '''
        windowSizeParam = QgsProcessingParameterNumber(
            name=self.WINDOW_SIZES,
            description=self.tr('Windows sizes (pixels)'),
            defaultValue=3,
            minValue=3            
        )
        
        self.addParameter(windowSizeParam)

        # === OUTPUT PARAMETERS ===
        

        self.addParameter(ChloeCSVParameterFileDestination(
            name=self.OUTPUT_CSV,
            description=self.tr('Output csv')))

        fieldsParam = ChloeASCParameterFileDestination(
            name=self.OUTPUT_ASC,
            description=self.tr('Output Raster ascii'))
        self.addParameter(fieldsParam, createOutput=True)

        self.addParameter(QgsProcessingParameterFileDestination(
            name=self.SAVE_PROPERTIES,
            description=self.tr('Properties file'),
            fileFilter='Properties (*.properties)'))

    def name(self):
        return 'sliding'

    def displayName(self):
        return self.tr('sliding')

    def group(self):
        return self.tr('landscape metrics')

    def groupId(self):
        return 'landscapemetrics'

    def commandName(self):
        return 'java'

    def PreRun(self, parameters, context, feedback, executing=True):
        """Here is where the processing itself takes place."""

        # === INPUT
        self.INPUT_ASC = self.parameterRasterAsFilePath(
            parameters, self.INPUT_ASC, context)

        self.window_shape = self.types_of_shape[
            self.parameterAsInt(parameters, self.WINDOW_SHAPE, context)]

        self.friction_file = self.parameterAsString(
            parameters, self.FRICTION_FILE, context)

        self.window_sizes = self.parameterAsInt(
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
        self.output_csv = self.parameterAsString(
            parameters, self.OUTPUT_CSV, context)
        self.output_asc = self.parameterAsString(
            parameters, self.OUTPUT_ASC, context)
        self.setOutputValue(self.OUTPUT_CSV, self.output_csv)
        self.setOutputValue(self.OUTPUT_ASC, self.output_asc)

        base_in = os.path.basename(self.INPUT_ASC)
        name_in = os.path.splitext(base_in)[0]
        ext_in = os.path.splitext(base_in)[1]

        dir_out_asc = os.path.dirname(self.output_asc)
        base_out_asc = os.path.basename(self.output_asc)
        name_out_asc = os.path.splitext(base_out_asc)[0]
        #ext_out_asc     = os.path.splitext(base_out_asc)[1]

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
        f_prj = dir_out_asc+os.sep+name_out_asc+".prj"
        self.createProjectionFile(f_prj)

    def createPropertiesTempFile(self):
        """Create Properties File."""

        s_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        with open(self.f_path, "w") as fd:
            fd.write("#"+s_time+"\n")
            fd.write("treatment=sliding\n")
            fd.write(ChloeUtils.formatString(
                'input_ascii=' + self.INPUT_ASC+"\n", isWindows()))
            fd.write(ChloeUtils.formatString(
                'output_csv=' + self.output_csv + "\n", isWindows()))
            fd.write(ChloeUtils.formatString(
                'output_asc=' + self.output_asc + "\n", isWindows()))

            fd.write("window_sizes={" + str(ChloeUtils.toOddNumber(self.window_sizes)) + "}\n")
            fd.write("maximum_nodata_value_rate="
                     + str(self.maximum_rate_missing_values) + "\n")

            if self.analyze_type == "weighted distance":
                fd.write("distance_function=" + str(self.distance_formula) + "\n")
                
            fd.write("metrics={" + self.metrics + "}\n")
            fd.write("delta_displacement="
                     + str(self.delta_displacement) + "\n")
            fd.write("shape=" + str(self.window_shape) + "\n")
            if self.window_shape == "FUNCTIONAL":
                fd.write("friction=" + self.friction_file + "\n")

            if self.b_interpolate_values:
                fd.write("interpolation=true\n")
            else:
                fd.write("interpolation=false\n")

            if self.filter:
                fd.write("filters={" + self.filter + "}\n")
            if self.unfilter:
                fd.write("unfilters={" + self.unfilter + "}\n")

            fd.write("visualize_ascii=false\n")

            # Writing the second part of the properties file
            if self.output_csv:
                fd.write("export_csv=true\n")
            else:
                fd.write("export_csv=false\n")

            if self.output_asc:
                fd.write("export_ascii=true\n")
            else:
                fd.write("export_ascii=false\n")
