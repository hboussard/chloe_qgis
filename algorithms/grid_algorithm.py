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
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingParameterFileDestination
)

from processing.tools.system import getTempFilename, isWindows
from time import gmtime, strftime
from ..ChloeUtils import ChloeUtils


# Mother class
from ..chloe_algorithm import ChloeAlgorithm
from ..chloe_algorithm_dialog import ChloeCSVParameterFileDestination
from ..chloe_algorithm_dialog import ChloeASCParameterFileDestination


class GridAlgorithm(ChloeAlgorithm):
    """Grid algorithm"""

    def __init__(self):
        super().__init__()

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

        # METRICS
        metricsParam = QgsProcessingParameterString(
            name=self.METRICS,
            description=self.tr('Select metrics'))

        metricsParam.setMetadata({
            'widget_wrapper': {
                'class': 'Chloe.chloe_algorithm_dialog.ChloeDoubleComboboxWidgetWrapper',
                'dictValues': self.types_of_metrics,
                'initialValue': 'diversity metrics',
                'rasterLayerParamName': self.INPUT_LAYER_ASC,
                'parentWidgetConfig': {'paramName': self.INPUT_LAYER_ASC, 'refreshMethod': 'refreshMappingCombobox'}
            }
        })

        self.addParameter(metricsParam)

        # GRID SIZE
        self.addParameter(QgsProcessingParameterNumber(
            name=self.GRID_SIZES,
            description=self.tr('Grid size (pixels)'),
            defaultValue=2,
            minValue=2))

        # MAXIMUM RATE MISSING VALUES
        self.addParameter(QgsProcessingParameterNumber(
            name=self.MAXIMUM_RATE_MISSING_VALUES,
            description=self.tr('Maximum rate of mising values'),
            minValue=0,
            maxValue=100,
            defaultValue=100))

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
        return 'grid'

    def displayName(self):
        return self.tr('grid')

    def group(self):
        return self.tr('landscape metrics')

    def groupId(self):
        return 'landscapemetrics'

    def commandName(self):
        return 'grid'

    def PreRun(self, parameters, context, feedback, executing=True):
        """Here is where the processing itself takes place."""

        # === INPUT
        self.input_layer_asc = self.parameterRasterAsFilePath(
            parameters, self.INPUT_LAYER_ASC, context)
        self.grid_sizes = self.parameterAsInt(
            parameters, self.GRID_SIZES, context)
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
        """Create Properties File.

        Example of properties produced
        ```
        #2018-11-01 11:08:49
        treatment=grid
        input_ascii=/home/raster.asc
        output_csv=/home/OUTPUTCSV.csv
        output_asc=/home/OUTPUTASC.asc
        grid_sizes={3}
        maximum_nodata_value_rate=100
        metrics={MPS-class_1}
        visualize_ascii=false
        export_csv=true
        export_ascii=true
        ```
        """

        s_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        with open(self.f_path, "w") as fd:
            fd.write("#"+s_time+"\n")
            # fd.write("# "+self.comment+"\n")
            fd.write("treatment=grid\n")
            fd.write(ChloeUtils.formatString(
                'input_ascii=' + self.input_layer_asc+"\n", isWindows()))
            fd.write(ChloeUtils.formatString(
                'output_csv=' + self.output_csv + "\n", isWindows()))
            fd.write(ChloeUtils.formatString(
                'output_asc=' + self.output_asc + "\n", isWindows()))

            fd.write("grid_sizes={" + str(self.grid_sizes) + "}\n")
            fd.write("maximum_nodata_value_rate="
                     + str(self.maximum_rate_missing_values) + "\n")
            fd.write("metrics={" + self.metrics + "}\n")

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
