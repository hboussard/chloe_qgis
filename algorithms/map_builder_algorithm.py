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
import io
import subprocess
import time
import re
from qgis.PyQt.QtCore import QSettings,QCoreApplication
from qgis.core import QgsVectorFileWriter
from osgeo import ogr, osr
from osgeo import gdal, gdalconst
import math
import numpy as np

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterField,
    QgsProcessingParameterExtent,
    QgsProcessingParameterNumber,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterString,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFile,
    QgsProcessingOutputVectorLayer,
    QgsProcessingOutputRasterLayer,
    QgsProcessingParameterFolderDestination,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterMatrix,
    QgsProcessingOutputFolder,
    QgsProcessingFeedback
)

from processing.tools import dataobjects, vector

from processing.core.ProcessingConfig import ProcessingConfig

from processing.tools.system import getTempFilename, isWindows, isMac

from osgeo import osr
from time import gmtime, strftime

from ast import literal_eval


from qgis.PyQt.QtGui import QIcon
from ..ChloeUtils import ChloeUtils
import tempfile

# Mother class
from ..chloe_algorithm import ChloeAlgorithm
from ..chloe_algorithm_dialog import ChloeAlgorithmDialog, ChloeVectorSourcesWidgetWrapper

class MapBuilderAlgorithm(QgsProcessingAlgorithm):#QgsProcessingAlgorithm
    """
    Algorithm map builder
    """
    INPUT_RASTER = "INPUT_RASTER"
    EXTENT = "EXTENT"
    INPUT_VECTORS = "INPUT_VECTORS"
    OUTPUT = "OUTPUT"

    def __init__(self):
        super().__init__()
        
    def createInstance(self, config={}):
        return self.__class__()
        
    def icon(self):
        iconPath = os.path.normpath(os.path.join(os.path.dirname(__file__),'..', 'images', 'chloe_icon.png'))
        return QIcon(iconPath)


    def initAlgorithm(self, config=None):
        # === INPUT PARAMETERS ===

       
        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_RASTER,
                self.tr('Input layer')
            )
        )
        
        self.addParameter(
            QgsProcessingParameterExtent(
                self.EXTENT,
                self.tr('Extent')
            )
        )

        vectorsParam = QgsProcessingParameterString(
            name= self.INPUT_VECTORS,
            description=self.tr('Vector sources'),
            defaultValue='')
        vectorsParam.setIsDynamic(False)

        vectorsParam.setMetadata({
            'widget_wrapper': {
                'class': 'Chloe.chloe_algorithm_dialog.ChloeVectorSourcesWidgetWrapper'
               # 'parentWidgetConfig': { 'paramName': self.INPUT_VECTORS, 'refreshMethod': 'refreshMappingCombobox', 'paramName2': self.INPUT_ASC, 'refreshMethod2':'emptyMappingAsc'}
            }
        })
        self.addParameter(vectorsParam)




        # un Widget qui donne une liste de
        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT,
                self.tr('Output raster')
            )
        )        
        
        
    def tr(self, string, context=''):
        if context == '':
            context = self.__class__.__name__
        return QCoreApplication.translate(context, string)        
        
        

    def name(self):
        return 'map_builder'

    def displayName(self):
        return self.tr('Build map')

    def group(self):
        return self.tr('util')

    def groupId(self):
        return 'util'

    def commandName(self):
        return 'map_builder'

    def processAlgorithm(self, parameters, context, feedback):
        """Here is where the processing itself takes place."""
        print('processAlgorithm')
        input_raster = self.parameterRasterAsFilePath(parameters, self.INPUT_RASTER, context)
        extent = self.parameterAsString(parameters, self.EXTENT, context)
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
        
        MapBuilderAlgorithm.generateMapFromRaster(output,
                                                  input_raster,
                                                  extent=extent,
                                                  datas=parameters[self.INPUT_VECTORS],
                                                  downscale = 1, upscale = 1,
                                                  extentBuffer = 0,reclass=None,noDataValue=0)
    

    # Open the dataset from the file
    
    
    # raster de référence : celui sur lequel on s'appuie pour définir la position des pixels
    # emprise : on conserve tous les pixels de refRaster dont une part est située dans emprise
    # rArray : liste de (raster,order, liste des valeurs retenues)
    # rArray : liste de (vecteur,order, champ, liste des valeurs retenues)
    
    # ou liste de (filename,type,champ/bande,liste de valeurs retenues)
    
    
    
    def validateExtent(extent,projection):
        if(type(extent) == str):
            strExtent = extent.split("[")[0]
            extent = []
            for num in strExtent.split(","):
                extent.append(float(num)) 
            # dataset = ogr.Open(extent)
            # # éventuellement convertir en fonction de la projection
            
            # layer = dataset.GetLayer()
            # extent = layer.GetExtent()
            
        return extent
            
    def transformDataset(dataSource,sourceprj,targetprj):    
        layer = dataSource.GetLayer()
    
        transform = osr.CoordinateTransformation(sourceprj, targetprj)
        
        to_fill = ogr.GetDriverByName("MEMORY")
        ds = to_fill.CreateDataSource("memData",1)
        outlayer = ds.CreateLayer('', targetprj, ogr.wkbPolygon)
        outlayer.CreateField(ogr.FieldDefn('id', ogr.OFTInteger))
        
        #apply transformation
        i = 0
        
        for feature in layer:
            transformed = feature.GetGeometryRef()
            transformed.Transform(transform)
        
            geom = ogr.CreateGeometryFromWkb(transformed.ExportToWkb())
            defn = outlayer.GetLayerDefn()
            feat = ogr.Feature(defn)
            feat.SetField('id', i)
            feat.SetGeometry(geom)
            outlayer.CreateFeature(feat)
            i += 1
            feat = None
        
        ds = None
    
    
    def addDatas(resRaster,datas):
        print("addDatas")
        for data in datas:
            print(data)
    
        #geotransform = resRaster.GetGeoTransform()
        projection = resRaster.GetProjection()
        print(resRaster)
        print(projection)
        
        # pour chaque entree :
        print("loop")
        for data in datas:
            print(data)
            # si vecteur : rasteriser
            if(data['type']=='vector'):
                print('vector')
    
                options = []
                if('8c' in data.keys() and data['8c']):
                    options.append('ALL_TOUCHED=TRUE')  # rasterize all pixels touched by polygons/lines
                if(type(data['burnvalue'])==str):
                    bv = 0
                    options.append('ATTRIBUTE='+data['burnvalue'])  # put raster values according to the 'id' field values
                else:
                    bv = data['burnvalue']
                 
                if(type(data['filenames'])==str):
                    data['filenames']=[data['filenames']]
                    
                for filename in data['filenames']:
                    dataset = ogr.Open(filename)
                    layer = dataset.GetLayer()
                    if('filter' in data.keys() and data['filter'] is not None):
                        layer.SetAttributeFilter(data['filter'])
        
        
                    #set spatial reference and transformation
                    sourceprj = layer.GetSpatialRef()
                    targetprj = osr.SpatialReference(wkt = projection)
                    if(not sourceprj.IsSame(targetprj)):
                        print("Transform...")
                        print(sourceprj)
                        print("to")
                        print(targetprj)
                        #TODO 3.16 : test si gdal corrigé
                        # dataset = MapBuilderAlgorithm.transformDataset(dataset,sourceprj,targetprj)
        
                    #transform = osr.CoordinateTransformation(sourceprj, targetprj)
                    #print(transform)
                    print("Rasterize...")
                    status = gdal.RasterizeLayer(resRaster,  # output to our dataset
                                                  [1],  # output to our new dataset's first band
                                                  layer,  # rasterize this layer
                                                  None, None,  # transformations : pas assez documenté?
                                                  [bv],  # burn value 0
                                                  options
                                                  )
                    print(status)
                    dataset = None
    
            # else:
            #     # raster
                
            #     # si pas même projection : on reprojette
            #     tmp = gdal.GetDriverByName('MEM').Create("", src_model.RasterXSize, src_model.RasterYSize, 1, gdalconst.GDT_Float32)
            #     tmp.SetGeoTransform( src_model.GetGeoTransform() )
            #     tmp.SetProjection( src_model.GetProjection())
            #     tmp.GetRasterBand(1).WriteArray(ETPj)
            #     img = gdal.Open(refRaster, gdalconst.GA_ReadOnly)
                
    def generateMapFromRaster(resRasterFile,refRasterFile,extent=None,datas=None,downscale = 1, upscale = 1,extentBuffer = 0,reclass=None,noDataValue=0):
        
        print("resRasterFile : ")
        print(resRasterFile)
        print("refRasterFile : ")
        print(refRasterFile)
        
        # générer le raster final
        # ouvrir l'image de référence
        refRaster = gdal.Open(refRasterFile, gdalconst.GA_ReadOnly)
        geotransform = refRaster.GetGeoTransform()
        
        if(extent == None):
            minx = geotransform[0]
            maxy = geotransform[3]
            maxx = minx + geotransform[1] * refRaster.RasterXSize
            miny = maxy + geotransform[5] * refRaster.RasterYSize
            extent = [minx, miny, maxx, maxy]
        else:
            extent = MapBuilderAlgorithm.validateExtent(extent,refRaster.GetProjection())
        
        # calcul des positions en pixel des angles de l'extent dans le raster de référence
        pixelWidth = geotransform[1]
        pixelHeight = geotransform[5] # dimension signée
        
        if(downscale!=1):
            pixelWidth = pixelWidth*downscale
            pixelHeight = pixelHeight*downscale
        elif(upscale!=1):
            pixelWidth = pixelWidth/upscale
            pixelHeight = pixelHeight/upscale
            
        iL = math.floor((extent[0]-extentBuffer - geotransform[0])/pixelWidth)
        iR = math.floor((extent[1]+extentBuffer - geotransform[0])/pixelWidth)
        jU = math.floor((extent[3]+extentBuffer - geotransform[3])/pixelHeight)
        jB = math.floor((extent[2]-extentBuffer - geotransform[3])/pixelHeight)
        
        xL=geotransform[0]+iL*pixelWidth
        yU=geotransform[3]+jU*pixelHeight
        width = iR-iL+1
        height = jB-jU+1
        
        resRaster = gdal.GetDriverByName('GTiff').Create(resRasterFile, width, height, 1, gdalconst.GDT_Byte)
        resRaster.SetGeoTransform( (xL,pixelWidth,0,yU,0,pixelHeight))
        resRaster.SetProjection( refRaster.GetProjection() )
        resRaster.GetRasterBand(1).SetNoDataValue(noDataValue)
    
        if(downscale!=1):
            gdal.ReprojectImage( refRaster, resRaster, '', '', gdal.GRA_Mode, options = ['INIT_DEST=NO_DATA'])
        else:
            gdal.ReprojectImage( refRaster, resRaster, '', '', gdal.GRA_NearestNeighbour, options = ['INIT_DEST=NO_DATA'])    
        
        
        # renumérotation du raster de référence
        if(reclass is not None):
            print("reclass")
            rasterOld = resRaster.GetRasterBand(1).ReadAsArray()
            rasterNew = np.full(rasterOld.shape,noDataValue,dtype = np.uint8)
            for p in reclass:
                np.putmask(rasterNew, np.equal(rasterOld, p[0]), p[1])
            rasterOld = None
                  
            resRaster.GetRasterBand(1).WriteArray(rasterNew)
        
        # incorporer les datas
        MapBuilderAlgorithm.addDatas(resRaster,datas)
        
        #resRaster.FlushCache()
        resRaster = None
    
    
    
    def parameterRasterAsFilePath(self, parameters, paramName, context):
        res = self.parameterAsString(parameters, paramName, context)
        
        if res==None or res=='' or re.match(r"^[a-zA-Z0-9_]+$", res):
            layer = self.parameterAsRasterLayer(
                parameters, paramName, context)
            res = layer.dataProvider().dataSourceUri().split('|')[0]

        return res

    def parameterAsString(self, parameters, paramName, context):
        #print("paramName " + str(parameters[paramName]))
        #print("parameters " + str(parameters))
        if type(parameters[paramName])==dict and "data" in parameters[paramName]:
            return parameters[paramName]["data"]
            #return super().parameterAsString(parameters, parameters[paramName]["data"], context)
        else:
            return super().parameterAsString(parameters, paramName, context)