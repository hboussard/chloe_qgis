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
from qgis.core import QgsVectorFileWriter,QgsRasterLayer,QgsProcessingException,QgsProcessingContext,QgsCoordinateReferenceSystem
from osgeo import ogr, osr
from osgeo import gdal, gdalconst
import math
import json
import numpy as np
from pyproj import Transformer

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
from qgis.utils import iface


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
    SAVE_PROPERTIES = "SAVE_PROPERTIES"

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
            description=self.tr(''),
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
        
        self.addParameter(QgsProcessingParameterFileDestination(
            name=self.SAVE_PROPERTIES,
            description=self.tr('Properties file'),
            fileFilter='Properties (*.properties)'))
        
        
        
    def tr(self, string, context=''):
        if context == '':
            context = self.__class__.__name__
        return QCoreApplication.translate(context, string)        
        
        

    def name(self):
        return 'map_builder'

    def displayName(self):
        return self.tr('Build map')

    def group(self):
        return self.tr('generate ascii grid')

    def groupId(self):
        return 'generateasciigrid'

    def commandName(self):
        return 'map_builder'

    def processAlgorithm(self, parameters, context, feedback):
        """Here is where the processing itself takes place."""
        print('processAlgorithm')
        input_raster = self.parameterRasterAsFilePath(parameters, self.INPUT_RASTER, context)
        extent = self.parameterAsString(parameters, self.EXTENT, context)
        vectors_datas=parameters[self.INPUT_VECTORS]["datas"]
        upscale = parameters[self.INPUT_VECTORS]["upscale"]
        downscale = parameters[self.INPUT_VECTORS]["downscale"]
        extentBuffer=parameters[self.INPUT_VECTORS]["extentBuffer"]
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
        param_save = self.parameterAsOutputLayer(parameters, self.SAVE_PROPERTIES, context)
        
        f = open(param_save, "w", encoding="utf-8")
        json.dump({'output':output,
                   'input_raster':input_raster,
                   'extent':extent,
                   'datas':vectors_datas,
                   'downscale' : downscale, 'upscale' : upscale,
                   'extentBuffer': extentBuffer,'reclass':None,'noDataValue':0},f)
        
        self.generateMapFromRaster(output,
                                                  input_raster,
                                                  extent=extent,
                                                  datas=vectors_datas,
                                                  downscale = downscale, upscale = upscale,
                                                  extentBuffer = extentBuffer,reclass=None,noDataValue=0)
        rlayer = QgsRasterLayer(output, "Custom Map")
        if not rlayer.isValid():
            raise QgsProcessingException(self.tr("""Cannot load the output in the application"""))

        rLayerName = ChloeUtils.deduceLayerName(rlayer, self.name())
        ChloeUtils.setLayerSymbology(rlayer, 'continuous.qml')
        context.temporaryLayerStore().addMapLayer(rlayer)
        layerDetails = QgsProcessingContext.LayerDetails(rLayerName,
                                              context.project(),
                                              self.OUTPUT)
        
        #postProcess = ChloeOutputLayerPostProcessor()t
        #layerDetails.setPostProcessor(postProcess)
        context.addLayerToLoadOnCompletion(rlayer.id(), layerDetails)
        results = {}
        results[self.OUTPUT] = rlayer.id()
        return results

    # Open the dataset from the file
    
    
    # raster de référence : celui sur lequel on s'appuie pour définir la position des pixels
    # emprise : on conserve tous les pixels de refRaster dont une part est située dans emprise
    # rArray : liste de (raster,order, liste des valeurs retenues)
    # rArray : liste de (vecteur,order, champ, liste des valeurs retenues)
    
    # ou liste de (filename,type,champ/bande,liste de valeurs retenues)
    
    def getEPSG(ds):
        try :
            proj = osr.SpatialReference(wkt=ds.GetProjection())
            epsg = proj.GetAttrValue('AUTHORITY',1)
            if type(epsg)=='str':
                epsg = int(epsg)
        except :
            epsg = 0
        print("EPSG:",epsg)
        return epsg
            
    
    def validateExtent(self,extent,toEPSG):

        if(type(extent) == str):
            extent = extent.split("[")
            xmin,xmax,ymin,ymax = extent[0].split(",")
            xmin=float(xmin)
            xmax=float(xmax)
            ymin=float(ymin)
            ymax=float(ymax)
            print(xmin,xmax,ymin,ymax)
            if len(extent)>1:
                transformer = Transformer.from_crs(int(extent[1][5:-1]), int(toEPSG), always_xy=True)
                x1,y1 = transformer.transform(xmin, ymin)
                x2,y2 = transformer.transform(xmin, ymax)
                x3,y3 = transformer.transform(xmax, ymin)
                x4,y4 = transformer.transform(xmax, ymax)
                minx=min(x1,x2,x3,x4)
                maxx=max(x1,x2,x3,x4)
                miny=min(y1,y2,y3,y4)
                maxy=max(y1,y2,y3,y4)
                extentNum=[minx,maxx,miny,maxy]
                print(minx,maxx,miny,maxy)
        return extentNum
            
    def transformDataset(dataSource,sourceEPSG,targetEPSG):    
        layer = dataSource.GetLayer()
    
        transformer = Transformer.from_crs(sourceEPSG,targetEPSG)
        #transform = osr.CoordinateTransformation(sourceprj, targetprj)
        
        to_fill = ogr.GetDriverByName("Memory")
        print(to_fill)
        ds = to_fill.CreateDataSource("memData",1)
        targetSpatialReference = osr.SpatialReference()
        targetSpatialReference.ImportFromEPSG(targetEPSG)
        outlayer = ds.CreateLayer('', targetSpatialReference, ogr.wkbPolygon)
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
    
    
    def addDatas(resRaster,datas,refEPSG):
        print("addDatas")
        for data in datas:
            print(data)
    
        print("raster : ",resRaster)
        
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
                    sourceEPSG=MapBuilderAlgorithm.getEPSG(dataset)
                    layer = dataset.GetLayer()
                    if('filter' in data.keys() and data['filter'] is not None):
                        layer.SetAttributeFilter(data['filter'])
        
        
                    #set spatial reference and transformation
                    if(refEPSG!=sourceEPSG and refEPSG!=0 and sourceEPSG!=0):
                        print("Transform...")
                        print(sourceEPSG)
                        print("to")
                        print(refEPSG)
                        dataset = MapBuilderAlgorithm.transformDataset(dataset,sourceEPSG,refEPSG)
        
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
                
    def generateMapFromRaster(self,resRasterFile,refRasterFile,extent=None,datas=None,downscale = 1, upscale = 1,extentBuffer = 0,reclass=None,noDataValue=0):
        
        print("resRasterFile : ")
        print(resRasterFile)
        print("refRasterFile : ")
        print(refRasterFile)
        
        # générer le raster final
        # ouvrir l'image de référence
        refRaster = gdal.Open(refRasterFile, gdalconst.GA_ReadOnly)
        refGeotransform = refRaster.GetGeoTransform()
        refEPSG = MapBuilderAlgorithm.getEPSG(refRaster)
        if refEPSG==0:
            refEPSG=int(iface.mapCanvas().mapSettings().destinationCrs().authid())
        
        if(extent == None):
            minx = refGeotransform[0]
            maxy = refGeotransform[3]
            maxx = minx + refGeotransform[1] * refRaster.RasterXSize
            miny = maxy + refGeotransform[5] * refRaster.RasterYSize
            extent = [minx, miny, maxx, maxy]
        else:
            extent = self.validateExtent(extent,refEPSG)
        
        # calcul des positions en pixel des angles de l'extent dans le raster de référence
        pixelWidth = refGeotransform[1]
        pixelHeight = refGeotransform[5] # dimension signée
        
        if(downscale!=1):
            pixelWidth = pixelWidth*downscale
            pixelHeight = pixelHeight*downscale
        elif(upscale!=1):
            pixelWidth = pixelWidth/upscale
            pixelHeight = pixelHeight/upscale
            
        iL = math.floor((extent[0]-extentBuffer - refGeotransform[0])/pixelWidth)
        iR = math.floor((extent[1]+extentBuffer - refGeotransform[0])/pixelWidth)
        jU = math.floor((extent[3]+extentBuffer - refGeotransform[3])/pixelHeight)
        jB = math.floor((extent[2]-extentBuffer - refGeotransform[3])/pixelHeight)
        
        xL=refGeotransform[0]+iL*pixelWidth
        yU=refGeotransform[3]+jU*pixelHeight
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
        MapBuilderAlgorithm.addDatas(resRaster,datas,refEPSG)
        
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