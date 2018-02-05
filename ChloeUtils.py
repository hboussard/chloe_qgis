# -*- coding: utf-8 -*-

"""
***************************************************************************
    GdalUtils.py
    ---------------------
    Date                 : January 2017

        email                : hugues.boussard at inra.fr
***************************************************************************
"""

__author__ = 'Jean-Charle Naud'
__date__ = 'August 2017'
__copyright__ = '(C) 2017, Jean-Charle Naud'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import subprocess
import time

import platform
import copy

from osgeo import gdal
import numpy as np
import math

from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsApplication, QgsVectorFileWriter, QgsColorRampShader, QgsSingleBandPseudoColorRenderer, QgsRasterShader, QgsRasterBandStats 
from processing.core.ProcessingLog import ProcessingLog
from processing.core.ProcessingConfig import ProcessingConfig
from processing.core.SilentProgress import SilentProgress
from processing.tools.system import isWindows, isMac
from processing.core.parameters import ParameterFile
from processing.core.outputs import OutputRaster
from jinja2 import Template


class ChloeUtils:
  """Generic class to call subprocess"""

  JAVA = 'JAVA'  # Path java.exe in windows
   
  @staticmethod
  def runChole(commands, progress=None):

    cwd=os.path.dirname(__file__) + os.sep + 'Chloe2012'
    
    if progress is None:
      progress = SilentProgress()

    fused_command = ' '.join(commands)
    progress.setInfo('Command:')
    progress.setCommand(fused_command)
    progress.setInfo('Output:')

    # Execution Chloe with subprocess command system
    success = False
    retry_count = 0
    while success == False:
      loglines = []
      loglines.append('Execution console output :')
      try:
        proc = subprocess.Popen(
          fused_command,
          shell=True,
          stdout=subprocess.PIPE,
          stdin=open(os.devnull),
          stderr=subprocess.STDOUT,
          universal_newlines=True,
          cwd=cwd,
        ).stdout
        for line in proc:
          progress.setConsoleInfo(line)
          loglines.append(line)
        success = True
      except IOError as e:
        if retry_count < 5:
          retry_count += 1
        else:
          raise IOError(e.message + u'\nTried 5 times without success. Last iteration stopped after reading {} line(s).\nLast line(s):\n{}'.format(len(loglines), u'\n'.join(loglines[-10:])))
    
    # Save log
    ProcessingLog.addToLog(ProcessingLog.LOG_INFO, loglines)
    ChloeUtils.consoleOutput = loglines

  @staticmethod
  def setLayerSymbology(layer, qmlFilename):
    styleFilepath = os.path.dirname(__file__) + os.sep + 'styles' + os.sep + qmlFilename
    layer.loadNamedStyle(styleFilepath)
    
    # getting statistics from the layer
    stats = layer.dataProvider().bandStatistics(1, QgsRasterBandStats.All, layer.extent())
    min = stats.minimumValue
    max = stats.maximumValue  
    
    # adjusting the symbology to equal intervals from the 
    renderer = layer.renderer() 
    shader = renderer.shader()
    colorRampShader = shader.rasterShaderFunction()
    if type(colorRampShader) is QgsColorRampShader: 
      colorRampItemList = colorRampShader.colorRampItemList()
      nbClasses = len(colorRampItemList)
      newColorRampList = []
      for i in range(0,nbClasses):
        val = min + (i*(max-min)/(nbClasses-1))
        item = QgsColorRampShader.ColorRampItem(val, (colorRampItemList[i]).color, str(val))
        newColorRampList.append(item)  
      colorRampShader.setColorRampItemList(newColorRampList)
    layer.triggerRepaint()
    

  @staticmethod
  def formatString(path_file, isWindowPath=False, encoding='utf8'):
    res = path_file.encode(encoding)
    if (isWindowPath):
      res = res.replace('/','\\').replace('\\','\\\\').replace(':','\:')
    return res
  
  @staticmethod
  def file_get_contents(filename,encoding='utf-8',context=False):

    if os.path.exists(filename):
      with open(filename) as file:  
        data = file.read()
      if context:
        template = Template(data.decode(encoding))
        return template.render(context)
      else:
        return data.decode(encoding)
      
    else:
      return None


  @staticmethod
  def extractValueNotNull(f_input):
        # === Test algorithm
        ds = gdal.Open(f_input)                 # DataSet
        band =  ds.GetRasterBand(1)             # -> band
        array = np.array(band.ReadAsArray())    # -> matrice values
        values = np.unique(array)   
        nodata = band.GetNoDataValue()

        int_values_and_nodata = [int(math.floor(x)) for x in values[(values!=0) & (values!=nodata)] ]

        return int_values_and_nodata

  @staticmethod
  def calculateMetric(metric,metric_simple,metric_cross,value_list):
    """Renerate and update simple and cross metric"""
    result = copy.deepcopy(metric)
    value_list.sort()

    for msk in metric_simple.keys():
      for ms in metric_simple[msk]:
        for val in value_list:
          result[msk].append(ms+str(val))

    for mck in metric_cross.keys():
      for mc in metric_cross[mck]:
        for val1 in value_list:
          for val2 in value_list:
            if val1 <= val2:
              result[mck].append(mc+str(val1)+"-"+str(val2))
              
    return result

class ASCOutputRaster(OutputRaster):
  def getFileFilter(self, alg):
    """ Force asc output raster extension"""
    
    exts = "ASC files (*.asc);; files (*)"
    return exts


class ParameterFileCSVTXT(ParameterFile):
  def getFileFilter(self, alg):
    """ Force asc output raster extension"""
    
    exts = "CSV files (*.csv);; TXT files (*.txt);;files (*)"
    return exts
  
