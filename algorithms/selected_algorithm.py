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
# from .selected_algorithm_dialog import SelectedAlgorithmDialog

class SelectedAlgorithm(ChloeAlgorithm):
    """Algorithm selection."""

    def __init__(self):
        super().__init__()

    # def getCustomParametersDialog(self):
    #     """Define Dialog associed with this algorithm."""
    #     return SelectedAlgorithmDialog(self)

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

        self.addParameter(QgsProcessingParameterNumber(
            name=self.WINDOW_SIZES,
            description=self.tr('Windows sizes (pixels)'),
            defaultValue=3))

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

        self.addParameter(QgsProcessingParameterFile(
            name=self.PIXELS_FILE,
            description=self.tr('Pixels file'),
            optional=True))

        self.addParameter(QgsProcessingParameterFile(
            name=self.POINTS_FILE,
            description=self.tr('Points file'),
            optional=True))

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
                'class': 'Chloe.chloe_algorithm_dialog.ChloeDoubleComboboxWidgetWrapper',
                'dictValues': self.types_of_metrics,
                'initialValue': 'value metrics',
                'rasterLayerParamName': self.INPUT_LAYER_ASC,
                'parentWidgetConfig': { 'paramName': self.INPUT_LAYER_ASC, 'refreshMethod': 'refreshMappingCombobox'}
            }
        })
        
        self.addParameter(metricsParam)

        # === OUTPUT PARAMETERS ===
        self.addParameter(QgsProcessingParameterFileDestination(
            name=self.SAVE_PROPERTIES,
            description=self.tr('Properties file'),
            fileFilter='Properties (*.properties)'))

        self.addParameter(ChloeCSVParameterFileDestination(
            name=self.OUTPUT_CSV,
            description=self.tr('Output csv')))

        fieldsParam = ChloeASCParameterFileDestination(
            name=self.OUTPUT_ASC,
            description=self.tr('Output Raster ascii'))
        self.addParameter(fieldsParam, createOutput=True)

    def name(self):
        return 'selected'

    def displayName(self):
        return self.tr('selected')

    def group(self):
        return self.tr('landscape metrics')

    def groupId(self):
        return 'landscapemetrics'

    def commandName(self):
        return 'selected'

    def PreRun(self, parameters, context, feedback, executing=True):
        """Here is where the processing itself takes place."""

        # === INPUT
        self.input_layer_asc = self.parameterRasterAsFilePath(
            parameters, self.INPUT_LAYER_ASC, context)
        self.window_shape = self.types_of_shape[
            self.parameterAsInt(parameters, self.WINDOW_SHAPE, context)]
        self.friction_file = self.parameterAsString(
            parameters, self.FRICTION_FILE, context)
        self.window_sizes = self.parameterAsInt(
            parameters, self.WINDOW_SIZES, context)

        self.pixels_point_selection = self.parameterAsInt(
            parameters, self.PIXELS_POINTS_SELECT, context)
        self.pixels_file = self.parameterAsString(
            parameters, self.PIXELS_FILE, context)
        self.points_file = self.parameterAsString(
            parameters, self.POINTS_FILE, context)

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

        base_in = os.path.basename(self.input_layer_asc)
        name_in = os.path.splitext(base_in)[0]
        ext_in = os.path.splitext(base_in)[1]

        dir_out_asc     = os.path.dirname(self.output_asc)
        base_out_asc    = os.path.basename(self.output_asc)
        name_out_asc    = os.path.splitext(base_out_asc)[0]
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

            fd.write("treatment=" + self.name() + "\n")
            fd.write(ChloeUtils.formatString(
                'input_ascii=' + self.input_layer_asc+"\n", isWindows()))
            fd.write(ChloeUtils.formatString(
                'output_csv=' + self.output_csv + "\n", isWindows()))
            fd.write(ChloeUtils.formatString(
                'output_asc=' + self.output_asc + "\n", isWindows()))

            fd.write("window_sizes={" + str(self.window_sizes) + "}\n")
            fd.write("maximum_nodata_value_rate="
                     + str(self.maximum_rate_missing_values) + "\n")
            fd.write("metrics={" + self.metrics + "}\n")

            fd.write("shape=" + str(self.window_shape) + "\n")
            if self.window_shape == "FUNCTIONAL":
                fd.write("friction=" + self.friction_file + "\n")
            if self.pixels_point_selection == 0:   # pixel(s) file
                fd.write("pixels=" + str(self.pixels_file) + "\n")
            elif self.pixels_point_selection == 1:  # point(s) file
                fd.write("points=" + str(self.points_file) + "\n")

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
