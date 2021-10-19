# -*- coding: utf-8 -*-

"""
/***************************************************************************
 Chole
                                 A QGIS plugin
 description
                              -------------------
        begin                : 2017-10-17
        author : Jean-Charles Naud, Olivier Bedel, Hugues Boussard, Daan Guillerme

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
    QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterString,
    QgsProcessingParameterFileDestination
)

from processing.tools.system import getTempFilename, isWindows

from time import gmtime, strftime

from ..ChloeUtils import ChloeUtils

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

        # INPUT MATRIX
        self.addParameter(QgsProcessingParameterMultipleLayers(
            self.INPUTS_MATRIX,
            self.tr('Input rasters'),
            QgsProcessing.TypeRaster))

        # COMBINE EXPRESSION
        combineParam = QgsProcessingParameterString(
            name=self.DOMAINS,
            description=self.tr('Combination'),
            defaultValue='')
        combineParam.setMetadata({
            'widget_wrapper': {
                'class': 'Chloe.chloe_algorithm_dialog.ChloeFactorTableWidgetWrapper',
                'input_matrix': self.INPUTS_MATRIX,
                'parentWidgetConfig': {'paramName': self.INPUTS_MATRIX, 'refreshMethod': 'resetFormula'}
            }
        })

        self.addParameter(combineParam)

        # === OUTPUT PARAMETERS ===

        # self.addParameter(ChloeParameterFolderDestination(
        #    name=self.OUTPUT_DIR,
        #    description=self.tr('Output directory')))

        # Output Asc
        fieldsParam = ChloeASCParameterFileDestination(
            name=self.OUTPUT_ASC,
            description=self.tr('Output Raster ascii'))

        self.addParameter(fieldsParam, createOutput=True)

        # Properties file
        self.addParameter(QgsProcessingParameterFileDestination(
            name=self.SAVE_PROPERTIES,
            description=self.tr('Properties file'),
            fileFilter='Properties (*.properties)'))

    def name(self):
        return 'combine'

    def displayName(self):
        return self.tr('Combine')

    def group(self):
        return self.tr('util')

    def groupId(self):
        return 'util'

    def commandName(self):
        return 'combine'

    def PreRun(self, parameters, context, feedback, executing=True):
        """Here is where the processing itself takes place."""

        # === INPUT
        inputFactors = self.parameterAsString(
            parameters, self.DOMAINS, context).split('.__.')

        self.combination = inputFactors[1]
        self.input_asc = inputFactors[0]

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
            fd.write("visualize_ascii=false\n")
            fd.write('treatment=combine'+"\n")
            fd.write(
                'combination='+self.combination+"\n")
            fd.write(ChloeUtils.formatString(
                'output_asc=' + self.output_asc+"\n", isWindows()))
            fd.write(ChloeUtils.formatString(
                'factors={'+self.input_asc+"}\n", isWindows()))
