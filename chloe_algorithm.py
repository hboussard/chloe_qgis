# -*- coding: utf-8 -*-

"""
***************************************************************************
    ChloeAlgorithm.py
    ---------------------
    Date                 : August 2012
    Copyright            : (C) 2012 by Victor Olaya
    Email                : volayaf at gmail dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Jean-Charles Naud/Alkante'
__date__ = 'August 2012'
__copyright__ = '(C) 2012, Victor Olaya'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import re

from qgis.PyQt.QtCore import QUrl, QCoreApplication

from qgis.core import (QgsApplication,
                       QgsVectorFileWriter,
                       QgsProcessingFeatureSourceDefinition,
                       QgsProcessingAlgorithm,
                       QgsProcessingContext,
                       QgsProcessingFeedback,
                       QgsProviderRegistry,
                       QgsMessageLog)

from .chloe_algorithm_dialog import ChloeAlgorithmDialog
from .ChloeUtils import ChloeUtils

from processing.tools import dataobjects
from processing.tools.system import isWindows
from qgis.utils import iface

# Heavy overload
from pprint import pformat
import time

from qgis.PyQt.QtCore import QCoreApplication, Qt, QLocale
from qgis.PyQt.QtWidgets import QMessageBox, QPushButton, QSizePolicy, QDialogButtonBox
from qgis.PyQt.QtGui import QColor, QPalette, QIcon

from qgis.core import (Qgis,
                       QgsProject,
                       QgsApplication,
                       QgsRasterLayer,
                       QgsVectorLayer,
                       QgsProcessingUtils,
                       QgsProcessingParameterDefinition,
                       QgsProcessingAlgRunnerTask,
                       QgsProcessingOutputHtml,
                       QgsProcessingParameterVectorDestination,
                       QgsProcessingOutputLayerDefinition,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingAlgorithm,
                       #QgsProxyProgressTask,
                       QgsTaskManager,
                       QgsProcessingException,
                       QgsProcessingLayerPostProcessorInterface)
from qgis.gui import (QgsGui,
                      QgsMessageBar,
                      QgsProcessingAlgorithmDialogBase)
from qgis.utils import iface

from processing.core.ProcessingLog import ProcessingLog
from processing.core.ProcessingConfig import ProcessingConfig
from processing.core.ProcessingResults import resultsList
from processing.gui.ParametersPanel import ParametersPanel
from processing.gui.BatchAlgorithmDialog import BatchAlgorithmDialog
from processing.gui.AlgorithmDialogBase import AlgorithmDialogBase
from processing.gui.AlgorithmExecutor import executeIterating, execute#, execute_in_place

from processing.gui.wrappers import WidgetWrapper

from processing.tools import dataobjects
import glob
# END : Heavy overload

class ChloeOutputLayerPostProcessor(QgsProcessingLayerPostProcessorInterface):
    
    def postProcessLayer(self, layer, context, feedback):
        print("postProcessing " + layer.name())
        if isinstance(layer, QgsRasterLayer):
            ChloeUtils.setLayerSymbology(layer, 'continuous.qml')



class ChloeAlgorithm(QgsProcessingAlgorithm):
    # All possible paramaters name
    INPUT_ASC = 'INPUT_ASC'
    INPUT_LAYER_ASC = 'INPUT_LAYER_ASC'
    WINDOW_SHAPE = 'WINDOW_SHAPE'
    FRICTION_FILE = 'FRICTION_FILE'
    WINDOW_SIZES = 'WINDOW_SIZES'
    GRID_SIZES = 'GRID_SIZES'
    DOMAINS = 'DOMAINS'
    VALUES_RANGES = 'VALUES_RANGES'
    ASCII_FILTER  = 'ASCII_FILTER'
    FILTER_VALUES = 'FILTER_VALUES'
    MAP_CSV          = 'MAP_CSV'
    CHANGES          = 'CHANGES'
    NODATA_VALUE     = 'NODATA_VALUE'
    INPUTS_MATRIX = 'INPUTS_MATRIX'
    
    INPUT_FILE_CSV = 'INPUT_FILE_CSV'
    INPUT_SHAPEFILE = 'INPUT_SHAPEFILE'

    FIELDS = 'FIELDS'
    FIELD = 'FIELD'

    LOOKUP_TABLE = 'LOOKUP_TABLE'
    EXTENT = 'EXTENT'

    N_COLS = 'N_COLS'
    N_ROWS = 'N_ROWS'
    XLL_CORNER = 'XLL_CORNER'
    YLL_CORNER = 'YLL_CORNER'
    CELL_SIZE = 'CELL_SIZE'

    CLUSTER          = 'CLUSTER'
    CLUSTER_DISTANCE = 'CLUSTER_DISTANCE'
    CLUSTER_TYPE     = 'CLUSTER_TYPE'
    CLUSTER_FRICTION = 'CLUSTER_FRICTION'
    
    clusterTypes = ['rook neighbourhood', 'queen neighbourhood', 'euclidian distance', 'functional distance']

    DELTA_DISPLACEMENT = 'DELTA_DISPLACEMENT'
    INTERPOLATE_VALUES_BOOL = 'INTERPOLATE_VALUES_BOOL'

    FILTER = 'FILTER'
    UNFILTER = 'UNFILTER'

    PIXELS_POINTS_SELECT = 'PIXELS_POINTS_SELECT'
    PIXELS_FILE = 'PIXELS_FILE'
    POINTS_FILE = 'POINTS_FILE'

    MAXIMUM_RATE_MISSING_VALUES = 'MAXIMUM_RATE_MISSING_VALUES'
    METRICS = 'METRICS'
    OPEN_ALL_ASC = 'OPEN_ALL_ASC'

    SAVE_PROPERTIES = 'SAVE_PROPERTIES'
    
    OUTPUT_DIR = 'OUTPUT_DIR'
    OUTPUT_ASC = 'OUTPUT_ASC'
    OUTPUT_CSV = 'OUTPUT_CSV'
    OUTPUT_CSV2 = 'OUTPUT_CSV2'

    #COMMENT = 'COMMENT'

    types_of_pixel_point_select = ['pixel(s) file', 'point(s) file']
    types_of_shape = ['CIRCLE', 'SQUARE', 'FUNCTIONAL']

    types_of_shape_abrev = { 'CIRCLE' : 'cr', 'SQUARE' : 'sq', 'FUNCTIONAL' : 'fn' }

    types_of_metrics = {
        "value metrics": [
            "N-theoretical",
            "N-total",
            "N-valid",
            "Nclass",
            "pN-valid",
            "N-type"],
        "couples metrics": [
            "E-hete",
            "E-homo",
            "NC-hete",
            "NC-homo",
            "NC-total",
            "NC-valid",
            "pNC-valid"],
        "patches metrics": [
            "LPI",
            "MPS",
            "NP",
            "SDPS"],
        "connectivity metrics": [
            "HC"],
        "diversity metrics": [
            "HET",
            "HET-agg",
            "HET-frag",
            "SHDI",
            "SHEI",
            "SIDI",
            "SIEI"],
        "landspace grain": [
            "LG3",
            "LG4",
            "LG5",
            "MD3",
            "MD4",
            "MD5"],
        "quantitative metrics": [
            "NAT",
            "average",
            "count_negatives",
            "count_positives",
            "size",
            "square_sum",
            "standard_deviation",
            "standard_error",
            "sum",
            "variance"]
        }

    types_of_metrics_simple = {
        "value metrics": [
            "NV_",
            "pNV_"],
        "patches metrics": [
            "LPI-class_",
            "MPS-class_",
            "NP-class_",
            "SDPS-class_",
            "VCPS-class_"],
        "connectivity metrics": [
            "AI_",
            "HC-class_"]
    }

    types_of_metrics_cross = {
        "couples metrics": [
            "E_",
            "NC_",
            "pNC_"],
        "diversity metrics": [
            "HETC_"]
    }

    def __init__(self):
        super().__init__()
        self.output_values = {}
        self.f_path = ''  # Path of properties files
        
    def icon(self):
        iconPath = os.path.normpath(os.path.join(os.path.dirname(__file__), 'images', 'chloe_icon.png'))
        return QIcon(iconPath)

    def tags(self):
        return ['chloe', self.commandName()]

    #def svgIconPath(self):
    #    return QgsApplication.iconPath("providerChloe.svg")

    def createInstance(self, config={}):
        return self.__class__()

    def createCustomParametersWidget(self, parent):
        #return ChloeAlgorithmDialog(self, parent=parent)
        return ChloeAlgorithmDialog(self)

    def flags(self):
        return QgsProcessingAlgorithm.FlagSupportsBatch | QgsProcessingAlgorithm.FlagNoThreading # cannot cancel!

    #def getConsoleCommandsJava(self, f_save_properties, force_properties=None):
    
    def getConsoleCommands(self, parameters, context, feedback, executing=True):
        #def getConsoleCommandsJava(self, f_save_properties, force_properties=None):
        """Get full console command to call Chole
        return arguments : The full command
        Example of return : java -jar bin/chloe-4.0.jar /tmp/distance_paramsrrVtm9.properties
        """

        # === SAVE_PROPERTIES
        f_save_properties = self.parameterAsString(
            parameters, self.SAVE_PROPERTIES, context)

        if f_save_properties:
            self.f_path = f_save_properties
        else:
            if not self.f_path:
                self.f_path = getTempFilename(ext="properties")

        # If JAVA provider parameter in defined use it (Typical Windows Case), else use simple 'java' command (Linux Case)
        java = ProcessingConfig.getSetting(ChloeUtils.JAVA)
        if java:
            arguments = ['"'+java+'"']
        else:
            arguments = ['java']
        arguments.append('-jar')
        arguments.append('bin' + os.sep + 'chloe-4.0.jar')

        # Get temp file path if not existe
        force_properties = False # TODO implementation of this
        if force_properties:    # Force properties path
            arguments.append('"'+force_properties+'"')
        else:
            if not self.f_path:
                #self.f_path = self.getOutputValue(self.SAVE_PROPERTIES)
                self.f_path = f_save_properties
            arguments.append('"'+self.f_path+'"')

        return arguments

    #
    # def getOgrCompatibleSource(self, parameter_name, parameters, context, feedback, executing):
    #     """
    #     Interprets a parameter as an OGR compatible source and layer name
    #     :param executing:
    #     """
    #     if not executing and parameter_name in parameters and isinstance(parameters[parameter_name], QgsProcessingFeatureSourceDefinition):
    #         # if not executing, then we throw away all 'selected features only' settings
    #         # since these have no meaning for command line chloe use, and we don't want to force
    #         # an export of selected features only to a temporary file just to show the command!
    #         parameters = {parameter_name: parameters[parameter_name].source}
    #
    #     input_layer = self.parameterAsVectorLayer(parameters, parameter_name, context)
    #     ogr_data_path = None
    #     ogr_layer_name = None
    #     if input_layer is None or input_layer.dataProvider().name() == 'memory':
    #         if executing:
    #             # parameter is not a vector layer - try to convert to a source compatible with OGR
    #             # and extract selection if required
    #             ogr_data_path = self.parameterAsCompatibleSourceLayerPath(parameters, parameter_name, context,
    #                                                                       QgsVectorFileWriter.supportedFormatExtensions(),
    #                                                                       feedback=feedback)
    #             ogr_layer_name = ChloeUtils.ogrLayerName(ogr_data_path)
    #         else:
    #             #not executing - don't waste time converting incompatible sources, just return dummy strings
    #             #for the command preview (since the source isn't compatible with OGR, it has no meaning anyway and can't
    #             #be run directly in the command line)
    #             ogr_data_path = 'path_to_data_file'
    #             ogr_layer_name = 'layer_name'
    #     elif input_layer.dataProvider().name() == 'ogr':
    #         if executing:
    #             # parameter is a vector layer, with OGR data provider
    #             # so extract selection if required
    #             ogr_data_path = self.parameterAsCompatibleSourceLayerPath(parameters, parameter_name, context,
    #                                                                       QgsVectorFileWriter.supportedFormatExtensions(),
    #                                                                       feedback=feedback)
    #             parts = QgsProviderRegistry.instance().decodeUri('ogr', ogr_data_path)
    #             ogr_data_path = parts['path']
    #             if 'layerName' in parts and parts['layerName']:
    #                 ogr_layer_name = parts['layerName']
    #             else:
    #                 ogr_layer_name = ChloeUtils.ogrLayerName(ogr_data_path)
    #         else:
    #             #not executing - don't worry about 'selected features only' handling. It has no meaning
    #             #for the command line preview since it has no meaning outside of a QGIS session!
    #             ogr_data_path = ChloeUtils.ogrConnectionStringAndFormatFromLayer(input_layer)[0]
    #             ogr_layer_name = ChloeUtils.ogrLayerName(input_layer.dataProvider().dataSourceUri())
    #     else:
    #         # vector layer, but not OGR - get OGR compatible path
    #         # TODO - handle "selected features only" mode!!
    #         ogr_data_path = ChloeUtils.ogrConnectionStringFromLayer(input_layer)
    #         ogr_layer_name = ChloeUtils.ogrLayerName(input_layer.dataProvider().dataSourceUri())
    #     return ogr_data_path, ogr_layer_name

    def setOutputValue(self, name, value):
        self.output_values[name] = value
    
    def parameterAsString(self, parameters, paramName, context):
        #print("test3 " + str(parameters[paramName]))
        if type(parameters[paramName])==dict and "data" in parameters[paramName]:
            return parameters[paramName]["data"]
        else:
            return super().parameterAsString(parameters, paramName, context)


    def processAlgorithm(self, parameters, context, feedback):
        self.PreRun(parameters, context, feedback)
        commands = self.getConsoleCommands(parameters, context, feedback)
        ChloeUtils.runChloe(commands, feedback)

        print('parameters : {}'.format(str(parameters)))

        # Auto generate outputs: dict {'name parameter' : 'value', ...}
        for output in self.destinationParameterDefinitions():
            print(str(output) + " " + str(output.metadata()))
        results = {}
        for o in self.outputDefinitions():
            
            if o.name() in parameters:
                results[o.name()] = parameters[o.name()]
        for k, v in self.output_values.items():
            results[k] = v

        # Load OUTPUT_ASC on temp layer on context id checked box checked
        #    (it will be load after in the project)
        #

        
        #print('context : {}'.format(context))
        #print('parameterDefinitions : {}'.format(self.parameterDefinitions()))
        if ('OUTPUT_ASC' in parameters) and 'openLayer' in parameters['OUTPUT_ASC'] and parameters['OUTPUT_ASC']['openLayer']==True:
            # Load OUTPUT_ASC on temp layer on context
            #    (it will be load after in the project)
            output_asc = parameters['OUTPUT_ASC']["data"]
            rlayer = QgsRasterLayer(output_asc, "hillshade")
            if not rlayer.isValid():
                raise QgsProcessingException(self.tr("""Cannot load the outpout in the application"""))

            rLayerName = ChloeUtils.deduceLayerName(rlayer, self.name())
            ChloeUtils.setLayerSymbology(rlayer, 'continuous.qml')
            context.temporaryLayerStore().addMapLayer(rlayer)
            layerDetails = QgsProcessingContext.LayerDetails(rLayerName,
                                                  context.project(),
                                                  self.OUTPUT_ASC)
            
            #postProcess = ChloeOutputLayerPostProcessor()t
            #layerDetails.setPostProcessor(postProcess)
            context.addLayerToLoadOnCompletion(rlayer.id(), layerDetails)
            results[self.OUTPUT_ASC] = rlayer.id()

        if ('OUTPUT_CSV' in parameters) and parameters['OUTPUT_CSV']['openLayer']==True:
            uri = "file:///"+ str(results['OUTPUT_CSV']) + "?type=csv&delimiter=;&detectTypes=yes&geomType=none&subsetIndex=no&watchFile=no"
            output_csv = parameters['OUTPUT_CSV']["data"]
            if 'OUTPUT_ASC' in parameters:
                output_csv = ChloeUtils.adjustExtension(output_csv, parameters['OUTPUT_ASC']["data"])
            
            print("output_csv " + str(uri) + "  " + str(output_csv))
            tLayerName = ChloeUtils.deduceLayerName(output_csv, self.name())
            tLayer = QgsVectorLayer(uri, tLayerName,'delimitedtext')
            if not tLayer.isValid():
                raise QgsProcessingException(self.tr("""Cannot load the outpout in the application"""))

            context.temporaryLayerStore().addMapLayer(tLayer)
            layerDetails = QgsProcessingContext.LayerDetails(tLayerName,
                                                  context.project(),
                                                  self.OUTPUT_CSV)
            context.addLayerToLoadOnCompletion(tLayer.id(), layerDetails)
            results[self.OUTPUT_CSV] = tLayer.id()
        
        if ('OUTPUT_DIR' in parameters) and self.outputFilenames and parameters['OUTPUT_DIR']['openLayer']==True:
            # === import all asc for multi algorithm
            outputDir = self.parameterAsString(parameters, self.OUTPUT_DIR, context)
            if outputDir!=None:
                self.prepareMultiProjectionFiles()
                for file in self.outputFilenames:
                    print(file + " " + os.path.splitext(os.path.basename(file))[0])
                    rlayer = QgsRasterLayer(file, os.path.splitext(os.path.basename(file))[0])
                    #rlayer = QgsRasterLayer(load_it, "hillshade")
                    if not rlayer.isValid():
                        raise QgsProcessingException(self.tr("""Cannot load the outpout in the application"""))

                    rLayerName = ChloeUtils.deduceLayerName(rlayer, self.name())
                    ChloeUtils.setLayerSymbology(rlayer, 'continuous.qml')
                    context.temporaryLayerStore().addMapLayer(rlayer)
                    layerDetails = QgsProcessingContext.LayerDetails(rLayerName,
                                                        context.project(),
                                                        self.OUTPUT_DIR)
                    
                    context.addLayerToLoadOnCompletion(rlayer.id(), layerDetails)

        return results

    def helpUrl(self):
        # helpPath = ChloeUtils.chloeHelpPath()
        # if helpPath == '':
        #     return None

        # if os.path.exists(helpPath):
        #     return QUrl.fromLocalFile(os.path.join(helpPath, '{}.html'.format(self.commandName()))).toString()
        # else:
        #     return helpPath + '{}.html'.format(self.commandName())
        localeName = QLocale.system().name()
        helpFilename = self.name() + "_" + localeName + ".html"
        helpfile = os.path.dirname(__file__) + os.sep+"."+os.sep+"help_algorithm"+os.sep + helpFilename
        return helpfile
    
    def shortHelpString(self):
        return self.helpString()

    def helpString(self):
        """Generation de l'onglet help"""
        helpfile = self.helpUrl()
        plugin_path = os.path.dirname(__file__)
        
        if (isWindows()):
            context={ 'plugin_path' : 'file:///'+(plugin_path+os.sep).replace('/','\\'),
                      'image_path'  : 'file:///'+(plugin_path+os.sep+'.'+os.sep+'help_algorithm'+os.sep+'images'+os.sep).replace('/','\\')}
        else:
            context={ 'plugin_path' : plugin_path+os.sep,
                      'image_path'  : plugin_path+os.sep+'.'+os.sep+'help_algorithm'+os.sep+'images'+os.sep}
        print(helpfile)
        content = ChloeUtils.file_get_contents(helpfile,encoding='utf-8',context=context)

        if not (content==None):
            return content
        else:
            return self.tr("No help available for this algorithm") 



    def commandName(self):
        parameters = {}
        for param in self.parameterDefinitions():
            parameters[param.name()] = "1"
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        name = self.getConsoleCommands(parameters, context, feedback, executing=False)[0]
        if name.endswith(".py"):
            name = name[:-3]
        return name

    def tr(self, string, context=''):
        if context == '':
            context = self.__class__.__name__
        return QCoreApplication.translate(context, string)


    def createProjectionFile(self,f_prj, crs=None, layer_crs=None, param=None):
        """Create Projection File"""

        if crs:               # crs given
            crs_output = crs
        elif layer_crs:          # crs from layer

            # Constrution des chemins de sortie des fichiers
            dir_in   = os.path.dirname(layer_crs)
            base_in  = os.path.basename(layer_crs)
            name_in  = os.path.splitext(base_in)[0]
            path_prj_in = dir_in+os.sep+name_in+'.prj'


            if os.path.isfile(path_prj_in) :
                crs_output = dataobjects.getObjectFromUri(layer_crs).crs()

            else:                 # crs project
                #crs_output = iface.mapCanvas().mapRenderer().destinationCrs()
                crs_output = iface.mapCanvas().mapSettings().destinationCrs()
        else:                 # crs project
            #crs_output = iface.mapCanvas().mapRenderer().destinationCrs()
            crs_output = iface.mapCanvas().mapSettings().destinationCrs()

        # with os.open(f_prj,os.O_CREAT|os.O_WRONLY) as fd:
        #     b_string = str.encode(crs_output.toWkt())
        #     os.write(fd, b_string)

        with open(f_prj,"w") as fd:
            #b_string = str.encode(crs_output.toWkt())
            fd.write(crs_output.toWkt())
    
    def prepareMultiProjectionFiles(self):
        # === Projection file
        for file in self.outputFilenames:
            baseOut = os.path.basename(file)
            radical = os.path.splitext(baseOut)[0]
            f_prj = self.output_dir + os.sep + radical + ".prj"
            self.createProjectionFile(f_prj)
    
    def parameterRasterAsFilePath(self, parameters, paramName, context):
        res = self.parameterAsString(parameters, paramName, context)
        if res==None or res=='':
            layer = self.parameterAsRasterLayer(
                parameters, paramName, context)
            res = layer.dataProvider().dataSourceUri().split('|')[0]
        return res