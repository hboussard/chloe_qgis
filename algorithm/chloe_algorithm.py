# -*- coding: utf-8 -*-

#####################################################################################################
# Chloe - landscape metrics
#
# Copyright 2018 URCAUE-Nouvelle Aquitaine
# Author(s) J-C. Naud, O. Bedel - Alkante (http://www.alkante.com) ;
#           H. Boussard - INRA UMR BAGAP (https://www6.rennes.inra.fr/sad)
# 
# Created on Mon Oct 22 2018
# This file is part of Chloe - landscape metrics.
# 
# Chloe - landscape metrics is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Chloe - landscape metrics is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Chloe - landscape metrics.  If not, see <http://www.gnu.org/licenses/>.
#####################################################################################################



import os
import io
import subprocess
import time
from PyQt4.QtCore import *
from qgis.core import *

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterMultipleInput, ParameterVector, ParameterRaster, ParameterTableField, ParameterNumber, ParameterBoolean, ParameterSelection, ParameterString, ParameterFile
from processing.core.outputs import OutputVector,OutputRaster, OutputFile, OutputDirectory
from processing.tools import dataobjects, vector

from processing.core.ProcessingConfig import ProcessingConfig
from processing.core.SilentProgress import SilentProgress
from processing.tools.system import getTempFilename, isWindows, isMac

from osgeo import osr
from time import gmtime, strftime

from ast import literal_eval


from PyQt4.QtGui import QIcon
from ..ChloeUtils import ChloeUtils
from ..gui.ChloeAlgorithmDialog import ChloeAlgorithmDialog
import tempfile
from processing.tools.system import isWindows

from qgis.utils import iface

class CholeAlgorithm(GeoAlgorithm):
    """
    Main class for Algorithm in Chloe
    Used like abstract class to implement specific algorithm
    """

    # dictionnaire stockant les parameter output qui ont une valeur explicite (non temporaire)
    namedOutputs = {}    

    def execute(self, progress=SilentProgress(), model=None):
        self.collectNonTemporaryOutputs()
        GeoAlgorithm.execute(self, progress, model)


    def getIcon(self):
        """Load algorithme icon"""
        return QIcon(os.path.dirname(__file__) + os.sep+".."+os.sep+"images"+os.sep+"chloe_icon.png")
   
    def getCustomParametersDialog(self):
        """Define Dialog associed with this algorithm
        Abstract class need to be modified"""
        pass

    def defineCharacteristics(self):
        """
        Algorithme variable and parameters parameters
        Need to be modified overload"""
        # === Variables intermediaire
        self.f_path=''
        #_, self.f_path = tempfile.mkstemp(suffix=".properties",prefix="distance_params")


    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place
        Abstract class need to be modified"""
        pass
        
    
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
                crs_output = iface.mapCanvas().mapRenderer().destinationCrs()
        else:                 # crs project
            crs_output = iface.mapCanvas().mapRenderer().destinationCrs()

        fd = os.open(f_prj,os.O_CREAT|os.O_WRONLY)
        os.write(fd,crs_output.toWkt())
        os.close(fd)

    def createPropertiesTempFile(self,f_input,f_output_dir, f_output_name, input_field_name="input_ascii",ouput_field_name='output_name'):
        """Create the first part of de Properties Temp File
        The second part depend of the algorithm used it
        
        Example of first part:

            #2017-12-07 13:20:13
            visualize_ascii=false
            input_ascii=/home/jnaud/tmp/37_INRA/chloe/data/qualitative/raster2007.asc
            output_folder=/tmp/processing2dac8f3ed7be4f3d899052576ae5a9d5/fa235cd4f75748309a4c78cf6c2e21d2
            output_name=raster2007_dist-[1, 2].asc
        """

        s_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        with open(self.f_path,"w") as fd:
          fd.write("#"+s_time+"\n")
          fd.write("visualize_ascii=false\n")
          fd.write( ChloeUtils.formatString(input_field_name+'='+f_input+"\n",isWindows()))  
          fd.write( ChloeUtils.formatString('output_folder='+f_output_dir+"\n",isWindows()))
          fd.write( ChloeUtils.formatString(ouput_field_name+'='+f_output_name+"\n",isWindows()))


    def removePropertiesTempFile(self):
        """Create Properties Temp File"""
        if os.path.isfile(self.f_path):
            os.remove(self.f_path)                     # Remove *.propertie file

    def getConsoleCommands(self, force_properties=None):
        """Get full console command to call Chole
        return arguments : The full command
        Example of return : java -jar bin/chloe-4.0.jar /tmp/distance_paramsrrVtm9.properties
        """

        # If JAVA provider parameter in defined use it (Typical Windows Case), else use simple 'java' command (Linux Case)
        java = ProcessingConfig.getSetting(ChloeUtils.JAVA)
        if java:
            arguments = ['"'+java+'"']
        else:
            arguments = ['java']
        arguments.append('-jar')
        arguments.append('bin' + os.sep + 'chloe-4.0.jar')
    
        # Get temp file path if not existe

        #if f_properties:
        

        if force_properties:    # Force properties path
            arguments.append('"'+force_properties+'"')
        else:
            if not self.f_path:
                #self.f_path = getTempFilename(ext="properties")
                self.f_path = self.getOutputValue(self.SAVE_PROPERTIES)
            arguments.append('"'+self.f_path+'"')

        return arguments

    def tr(self, string, context=''):
        if context == '' or context==None:
            context = self.__class__.__name__
        return QCoreApplication.translate(context, string)

    def help(self):
        """Generation de l'onglet help"""
        localeName = QLocale.system().name()
        helpFilename = self.name + "_" + localeName + ".html"
        helpfile = os.path.dirname(__file__) + os.sep+".."+os.sep+"help_algorithm"+os.sep + helpFilename
        
        plugin_path = os.path.dirname(__file__)
        
        if (isWindows()):
            context={ 'plugin_path' : 'file:///'+(plugin_path+os.sep).replace('/','\\'),
                      'image_path'  : 'file:///'+(plugin_path+os.sep+'..'+os.sep+'help_algorithm'+os.sep+'images'+os.sep).replace('/','\\')}
        else:
            context={ 'plugin_path' : plugin_path+os.sep,
                      'image_path'  : plugin_path+os.sep+'..'+os.sep+'help_algorithm'+os.sep+'images'+os.sep}

        content = ChloeUtils.file_get_contents(helpfile,encoding='utf-8',context=context)

        if not (content==None):
            return True, content
        else:
            return True, self.tr("No help available for this algorithm") 

        


    def shortHelp(self):
        """Generation de l'aide directement dans la fenêtre de l'algorithme"""
        localeName = QLocale.system().name()
        helpFilename = self.name + "_" + localeName + ".html"
        helpfile = os.path.dirname(__file__) + os.sep+".."+os.sep+"help_algorithm"+os.sep + helpFilename
        
        plugin_path = os.path.dirname(__file__)
        
        if (isWindows()):
            context={ 'plugin_path' : 'file:///'+(plugin_path+os.sep).replace('/','\\'),
                      'image_path'  : 'file:///'+(plugin_path+os.sep+'..'+os.sep+'help_algorithm'+os.sep+'images'+os.sep).replace('/','\\')}
        else:
            context={ 'plugin_path' : plugin_path+os.sep,
                      'image_path'  : plugin_path+os.sep+'..'+os.sep+'help_algorithm'+os.sep+'images'+os.sep}

        content = ChloeUtils.file_get_contents(helpfile,encoding='utf-8',context=context)

        if content:
           return content
        else:
           return self.tr("No short help available for this algorithm")
    
    def collectNonTemporaryOutputs(self):
        for out in self.outputs:
            if not out.hidden and out.value is not None:
              baseOutputName  = os.path.basename(out.value)
              baseOutputRadical  = os.path.splitext(baseOutputName)[0]
              self.namedOutputs[out.name] = baseOutputRadical
            
                
        