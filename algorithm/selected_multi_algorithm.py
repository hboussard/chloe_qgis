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

__author__ = 'Jean-Charles Naud/Alkante'
__date__ = '2017-10-17'


# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'


import os
import io
import glob
import subprocess
import time
from PyQt4.QtCore import QSettings
from qgis.core import QgsVectorFileWriter

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterMultipleInput, ParameterVector, ParameterRaster, ParameterTableField, ParameterNumber, ParameterBoolean, ParameterSelection, ParameterString, ParameterFile, ParameterTable
from processing.core.outputs import OutputVector,OutputRaster, OutputFile, OutputDirectory, OutputTable
from processing.tools import dataobjects, vector

from processing.core.ProcessingConfig import ProcessingConfig
from processing.core.SilentProgress import SilentProgress
from processing.tools.system import getTempFilename, isWindows, isMac

from osgeo import osr
from time import gmtime, strftime

from ast import literal_eval

# Tooling
from PyQt4.QtGui import QIcon
from ..ChloeUtils import ChloeUtils
import tempfile
from processing.tools.system import isWindows


from .chloe_algorithm         import CholeAlgorithm        # Mother(inheritance)
from ..gui.SelectedMultiAlgorithmDialog import SelectedMultiAlgorithmDialog    # Dialog
from ..ChloeUtils import ASCOutputRaster

class SelectedMultiAlgorithm(CholeAlgorithm):
    """Algorithm generate ascii grid from csv"""

    # Paramaters
    INPUT_LAYER_ASC             = 'INPUT_LAYER_ASC'
    WINDOW_SHAPE                = 'WINDOW_SHAPE'
    FRICTION_FILE               = 'FRICTION_FILE'
    WINDOW_SIZES                = 'WINDOW_SIZES'
    
    PIXELS_POINTS_SELECT        = 'PIXELS_POINTS_SELECT'
    PIXELS_FILE                 = 'PIXELS_FILE'
    POINTS_FILE                 = 'POINTS_FILE'
    # NUMBER_GENERATED_PIXEL      = 'NUMBER_GENERATED_PIXEL'
    # MINIMUM_DISTANCE            = 'MINIMUM_DISTANCE'

    # FILTER                      = 'FILTER'
    # UNFILTER                    = 'UNFILTER'

    MAXIMUM_RATE_MISSING_VALUES = 'MAXIMUM_RATE_MISSING_VALUES'
    METRICS                     = 'METRICS'
    OPEN_ALL_ASC                = 'OPEN_ALL_ASC'

    SAVE_PROPERTIES    = 'SAVE_PROPERTIES'
    # OUTPUT_CSV        = 'OUTPUT_CSV'
    # OUTPUT_ASC        = 'OUTPUT_ASC'

    OUTPUT_DIR         = 'OUTPUT_DIR'
    #OUTPUT_CSV_BOOL    = 'OUTPUT_CSV_BOOL'
    #OUTPUTS_ASC_BOOL   = 'OUTPUTS_ASC_BOOL'
    #VISUALISE_ASC_BOOL = 'VISUALISE_ASC_BOOL'


    types_of_pixel_point_select = ['pixel(s) file', 'point(s) file']
    types_of_shape =['SQUARE','CIRCLE','FUNCTIONAL']

    types_of_metrics = {
        "value metrics" : [
            "N-theoretical",
            "N-total",
            "N-valid"
            "Nclass",
            "pN-valid"],
        "couples metrics" :[
            "E-hete",
            "E-homo",
            "NC-hete",
            "NC-homo",
            "NC-total",
            "NC-valid",
            "pNC-valid"],
        "patches metrics":[
            "LPI",
            "MPS",
            "NP",
            "SDPS"],
        "connectivity metrics":[
            "HC"],
        "diversity metrics":[
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
            "maximum",
            "minimum",
            "size",
            "square_sum",
            "standard_deviation",
            "standard_error",
            "sum",
            "variance"]
        }
    
    types_of_metrics_simple = {
        "value metrics" : [
            "NV_",
            "pNV_"],
        "patches metrics" : [
            "LPI-class_",
            "MPS-class_",
            "NP-class_",
            "SDPS-class_",
            "VCPS-class_"],
        "connectivity metrics" : [
            "AI_",
            "HC-class_"]
    }

    types_of_metrics_cross = {
        "couples metrics" :[
            "E_",
            "NC_",
            "pNC_"],
        "diversity metrics" : [
            "HETC_"]
    }

    def getCustomParametersDialog(self):
        """Define Dialog associed with this algorithm"""
        return SelectedMultiAlgorithmDialog(self)

    def defineCharacteristics(self):
        """Algorithme variable and parameters parameters"""

        CholeAlgorithm.defineCharacteristics(self)

        # The name/group that the user will see in the toolbox
        self.group      = 'landscape metrics'
        self.i18n_group = self.tr('landscape metrics')
        self.name       = 'selected multi'
        self.i18n_name  = self.tr('selected multi')

        # === INPUT PARAMETERS ===
        self.addParameter(ParameterRaster(
            name=self.INPUT_LAYER_ASC,
            description=self.tr('Input layer asc')))

        self.addParameter(ParameterSelection(
            name=self.WINDOW_SHAPE,
            description=self.tr('Window shape'),
            options = ';'.join(self.types_of_shape)))

        self.addParameter(ParameterFile(
            name=self.FRICTION_FILE,
            description=self.tr('Friction file')))

        self.addParameter(ParameterString(
            name=self.WINDOW_SIZES, 
            description=self.tr('Windows sizes (pixels) [constraint V1.0: "select only one"]')))

        self.addParameter(ParameterSelection(
            name=self.PIXELS_POINTS_SELECT,
            description=self.tr('Pixels/points selection'),
            options = ';'.join(self.types_of_pixel_point_select)))

        self.addParameter(ParameterFile(
            name=self.PIXELS_FILE,
            description=self.tr('Pixels file')))

        self.addParameter(ParameterFile(
            name=self.POINTS_FILE,
            description=self.tr('Points file')))

        self.addParameter(ParameterNumber(
            name=self.MAXIMUM_RATE_MISSING_VALUES, 
            description=self.tr('Maximum rate of mising values'),
            default=100))

        self.addParameter(ParameterString(
            name=self.METRICS, 
            description=self.tr('Select metrics [constraint V1.0: "select only one"]')))

        # === OUTPUT PARAMETERS ===                                  
        self.addOutput(OutputFile(
            name=self.SAVE_PROPERTIES,
            description=self.tr('Properties file'),
            ext='properties'))

        self.addOutput(OutputDirectory(
            name=self.OUTPUT_DIR,
            description=self.tr('Output directory')))

        self.addParameter(ParameterBoolean(
            name=self.OPEN_ALL_ASC,
            description=self.tr('Open all ascii'),
            default=True,
            optional=True))

    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place"""

        # === INPUT_LAYER
        # @inprogress test utf8 encoding strategy
        self.input_layer_asc = self.getParameterValue(self.INPUT_LAYER_ASC).encode('utf-8')

        self.window_shape       = self.types_of_shape[self.getParameterValue(self.WINDOW_SHAPE)]
        self.friction_file      = self.getParameterValue(self.FRICTION_FILE).encode('utf-8')
        self.window_sizes       = self.getParameterValue(self.WINDOW_SIZES)

        self.pixels_point_selection = self.getParameterValue(self.PIXELS_POINTS_SELECT)
        self.pixels_file            = self.getParameterValue(self.PIXELS_FILE).encode('utf-8')
        self.points_file            = self.getParameterValue(self.POINTS_FILE).encode('utf-8')

        self.maximum_rate_missing_values = self.getParameterValue(self.MAXIMUM_RATE_MISSING_VALUES)
        self.metrics     = self.getParameterValue(self.METRICS.encode('utf-8'))
        self.open_all_asc = self.getParameterValue(self.OPEN_ALL_ASC)

        # === SAVE_PROPERTIES
        #f_save_properties = self.getParameterValue(self.SAVE_PROPERTIES)
        f_save_properties = self.getOutputValue(self.SAVE_PROPERTIES)
        if f_save_properties:
            self.f_path = f_save_properties
        else:
            if not self.f_path:
                self.f_path = getTempFilename(ext="properties")

        # === OUTPUT_LAYER
        self.output_dir      = self.getOutputValue(self.OUTPUT_DIR.encode('utf-8')).encode('utf-8')


        ## Constrution des chemin de sortie des fichiers    
        base_in = os.path.basename(self.input_layer_asc)
        name_in = os.path.splitext(base_in)[0]
        ext_in = os.path.splitext(base_in)[1]

        # === Properties file
        self.createPropertiesTempFile() # Create Properties file (temp or chosed)

        # === CORE
        commands = self.getConsoleCommands()            # Get args command
        ChloeUtils.runChole(commands, progress)         # RUN

        # === Projection file
        for file in glob.glob(self.output_dir+"/*.asc"):
            dir_out_asc     = os.path.dirname(file)
            base_out_asc    = os.path.basename(file)
            name_out_asc    = os.path.splitext(base_out_asc)[0]
            #ext_out_asc     = os.path.splitext(base_out_asc)[1] 
            
            f_prj = dir_out_asc+os.sep+name_out_asc+".prj"
            self.createProjectionFile(f_prj)


    def createPropertiesTempFile(self):
        """Create Properties File"""

        s_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        with open(self.f_path,"w") as fd:
            fd.write("#"+s_time+"\n")
            fd.write("treatment=selected\n")
            fd.write( ChloeUtils.formatString('input_ascii='+self.input_layer_asc+"\n",isWindows()))  
            fd.write( ChloeUtils.formatString('output_folder=' +self.output_dir +"\n",isWindows()))

            fd.write("window_sizes={"  + self.window_sizes +"}\n")
            fd.write("maximum_nodata_value_rate="  + str(self.maximum_rate_missing_values) +"\n")
            fd.write("metrics={"  + self.metrics +"}\n")

            fd.write("shape="  + str(self.window_shape) +"\n")
            if self.window_shape == "FUNCTIONAL":
                fd.write("friction="  + self.friction_file +"\n")
            if self.pixels_point_selection == 0:   # pixel(s) file
                fd.write("pixels="  + str(self.pixels_file) +"\n")
            elif self.pixels_point_selection == 1: # point(s) file
                fd.write("points="  + str(self.points_file) +"\n")


            fd.write("visualize_ascii=false\n")

            fd.write("export_csv=true\n")
            fd.write("export_ascii=true\n")
