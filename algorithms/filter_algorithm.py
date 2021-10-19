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
    QgsProcessingParameterString,
    QgsProcessingParameterFileDestination
)

from processing.tools.system import getTempFilename, isWindows

from time import gmtime, strftime

from ast import literal_eval

from ..ChloeUtils import ChloeUtils

# Mother class
from ..chloe_algorithm import ChloeAlgorithm
from ..chloe_algorithm_dialog import ChloeASCParameterFileDestination


class FilterAlgorithm(ChloeAlgorithm):
    """
    Algorithm filtering ascii grid
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

        # ASCII FILTER
        ascFilterParam = QgsProcessingParameterRasterLayer(
            name=self.ASCII_FILTER,
            description=self.tr('Ascii Grid Filter'))
        ascFilterParam.setMetadata({
            'widget_wrapper': {
                'class': 'Chloe.chloe_algorithm_dialog.ChloeAscRasterWidgetWrapper'
            }
        })
        self.addParameter(ascFilterParam)

        # FILTER VALUES
        fieldsParam = QgsProcessingParameterString(
            name=self.FILTER_VALUES,
            description=self.tr('Filter value(s)'),
            defaultValue='')
        fieldsParam.setMetadata({
            'widget_wrapper': {
                'class': 'Chloe.chloe_algorithm_dialog.ChloeValuesWidgetWrapper',
                'input_asc': self.ASCII_FILTER
            }
        })
        self.addParameter(fieldsParam)

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
        return 'filter'

    def displayName(self):
        return self.tr('filter')

    def group(self):
        return self.tr('util')

    def groupId(self):
        return 'util'

    def commandName(self):
        return 'filter'

    def PreRun(self, parameters, context, feedback, executing=True):
        """Here is where the processing itself takes place."""

        # === INPUT
        self.input_asc = self.parameterRasterAsFilePath(
            parameters, self.INPUT_ASC, context)
        self.ascii_filter = self.parameterRasterAsFilePath(
            parameters, self.ASCII_FILTER, context)
        self.filter_values = self.parameterAsString(
            parameters, self.FILTER_VALUES, context)

        # === OUTPUT
        self.output_asc = self.parameterAsString(
            parameters, self.OUTPUT_ASC, context)

        self.setOutputValue(self.OUTPUT_ASC, self.output_asc)

        # Constrution des chemins de sortie des fichiers

        dir_out = os.path.dirname(self.output_asc)
        base_out = os.path.basename(self.output_asc)
        name_out = os.path.splitext(base_out)[0]
        #ext_out = os.path.splitext(base_out)[1]
        # feedback.pushInfo('self.f_path')

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
            fd.write('treatment=filter'+"\n")
            fd.write(ChloeUtils.formatString(
                'input_ascii='+self.input_asc + "\n", isWindows()))
            fd.write(ChloeUtils.formatString('ascii_filter=' +
                                             self.ascii_filter + "\n", isWindows()))
            fd.write(ChloeUtils.formatString(
                'output_asc=' + self.output_asc+"\n", isWindows()))
            fd.write("filter_values={" + self.filter_values + "}\n")
            fd.write("visualize_ascii=false\n")
