# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QLayout, QVBoxLayout, QWidget
from jinja2 import Template
from qgis.core import (
    Qgis,
    QgsApplication,
    QgsVectorFileWriter,
    QgsProcessingFeedback,
    QgsProcessingUtils,
    QgsMessageLog,
    QgsSettings,
    QgsCredentials,
    QgsDataSourceUri,
    QgsProcessingOutputRasterLayer,
    QgsProcessingParameterFile,
    QgsRasterLayer,
    QgsColorRampShader,
    QgsRasterBandStats,
)

"""
***************************************************************************
    ChloeUtils.py
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

__author__ = "Jean-Charles Naud/Alkante"
__date__ = "August 2012"
__copyright__ = "(C) 2012, Victor Olaya"

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = "$Format:%H$"

import os
import subprocess
import platform
import copy
import re
import warnings
from osgeo import gdal
import numpy as np
import math
import psycopg2

from qgis.PyQt.QtWidgets import QWidget, QLayout, QVBoxLayout

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    from osgeo import ogr


try:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        from osgeo import chloe  # NOQA

    chloeAvailable = True
except:
    chloeAvailable = False


class ChloeUtils:

    supportedRasters = None
    supportedOutputRasters = None

    @staticmethod
    def runChloe(commands, feedback=None):

        cwd = f"{os.path.dirname(__file__)}{os.sep}Chloe"

        if feedback is None:
            feedback = QgsProcessingFeedback()
        envval = os.getenv("PATH")
        # We need to give some extra hints to get things picked up on OS X
        isDarwin = False
        try:
            isDarwin = platform.system() == "Darwin"
        except IOError:  # https://travis-ci.org/m-kuhn/QGIS#L1493-L1526
            pass
        if isDarwin and os.path.isfile(
            os.path.join(QgsApplication.prefixPath(), "bin", "chloeinfo")
        ):
            # Looks like there's a bundled chloe. Let's use it.
            os.environ[
                "PATH"
            ] = f'{os.path.join(QgsApplication.prefixPath(), "bin")}{os.pathsep}{envval}'
            os.environ["DYLD_LIBRARY_PATH"] = os.path.join(
                QgsApplication.prefixPath(), "lib"
            )
        else:
            # Other platforms should use default chloe finder codepath
            settings = QgsSettings()
            path = settings.value("/ChloeTools/chloePath", "")
            if not path.lower() in envval.lower().split(os.pathsep):
                envval += "{}{}".format(os.pathsep, path)
                os.putenv("PATH", envval)

        fused_command = " ".join([str(c) for c in commands])
        QgsMessageLog.logMessage(fused_command, "Processing", Qgis.Info)
        feedback.pushInfo("CHLOE command:")
        feedback.pushCommandInfo(fused_command)
        feedback.pushInfo("CHLOE command output:")

        success = False
        retry_count = 0
        while not success:
            loglines = []
            loglines.append("CHLOE execution console output")
            # print('step while')
            try:
                # print('runChloe')
                # feedback.pushConsoleInfo('runChloe')
                # print(fused_command)
                with subprocess.Popen(
                    fused_command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stdin=subprocess.DEVNULL,
                    stderr=subprocess.STDOUT,
                    # universal_newlines=True,
                    cwd=cwd,
                ) as proc:
                    for byte_line in proc.stdout:
                        line = byte_line.decode(
                            "utf8", errors="backslashreplace"
                        ).replace("\r", "")
                        feedback.pushConsoleInfo(line)
                        loglines.append(line)
                    success = True
            except IOError as e:
                if retry_count < 5:
                    # print('retry ' + str(retry_count))
                    retry_count += 1
                else:
                    raise IOError(
                        str(e)
                        + "\nTried 5 times without success. Last iteration stopped after reading {} line(s).\nLast line(s):\n{}".format(
                            len(loglines), "\n".join(loglines[-10:])
                        )
                    )

            QgsMessageLog.logMessage("\n".join(loglines), "Processing", Qgis.Info)
            ChloeUtils.consoleOutput = loglines

    @staticmethod
    def getConsoleOutput():
        return ChloeUtils.consoleOutput

    @staticmethod
    def getSupportedRasters():
        if not chloeAvailable:
            return {}

        if ChloeUtils.supportedRasters is not None:
            return ChloeUtils.supportedRasters

        if chloe.GetDriverCount() == 0:
            chloe.AllRegister()

        ChloeUtils.supportedRasters = {}
        ChloeUtils.supportedOutputRasters = {}
        ChloeUtils.supportedRasters["GTiff"] = ["tif"]
        ChloeUtils.supportedOutputRasters["GTiff"] = ["tif"]

        for i in range(chloe.GetDriverCount()):
            driver = chloe.GetDriver(i)
            if driver is None:
                continue
            shortName = driver.ShortName
            metadata = driver.GetMetadata()
            if (
                chloe.DCAP_RASTER not in metadata
                or metadata[chloe.DCAP_RASTER] != "YES"
            ):
                continue

            if chloe.DMD_EXTENSION in metadata:
                extensions = metadata[chloe.DMD_EXTENSION].split("/")
                if extensions:
                    ChloeUtils.supportedRasters[shortName] = extensions
                    # Only creatable rasters can be referenced in output rasters
                    if (
                        chloe.DCAP_CREATE in metadata
                        and metadata[chloe.DCAP_CREATE] == "YES"
                    ) or (
                        chloe.DCAP_CREATECOPY in metadata
                        and metadata[chloe.DCAP_CREATECOPY] == "YES"
                    ):
                        ChloeUtils.supportedOutputRasters[shortName] = extensions

        return ChloeUtils.supportedRasters

    @staticmethod
    def getSupportedOutputRasters():
        if not chloeAvailable:
            return {}

        if ChloeUtils.supportedOutputRasters is not None:
            return ChloeUtils.supportedOutputRasters
        else:
            ChloeUtils.getSupportedRasters()

        return ChloeUtils.supportedOutputRasters

    @staticmethod
    def getSupportedRasterExtensions():
        allexts = ["tif"]
        for exts in list(ChloeUtils.getSupportedRasters().values()):
            for ext in exts:
                if ext not in allexts and ext != "":
                    allexts.append(ext)
        return allexts

    @staticmethod
    def getSupportedOutputRasterExtensions():
        allexts = ["tif"]
        for exts in list(ChloeUtils.getSupportedOutputRasters().values()):
            for ext in exts:
                if ext not in allexts and ext != "":
                    allexts.append(ext)
        return allexts

    @staticmethod
    def getVectorDriverFromFileName(filename):
        ext = os.path.splitext(filename)[1]
        if ext == "":
            return "ESRI Shapefile"

        formats = QgsVectorFileWriter.supportedFiltersAndFormats()
        for format in formats:
            if ext in format.filterString:
                return format.driverName
        return "ESRI Shapefile"

    @staticmethod
    def getFormatShortNameFromFilename(filename):
        ext = filename[filename.rfind(".") + 1 :]
        supported = ChloeUtils.getSupportedRasters()
        for name in list(supported.keys()):
            exts = supported[name]
            if ext in exts:
                return name
        return "GTiff"

    @staticmethod
    def escapeAndJoin(strList):
        joined = ""
        for s in strList:
            if not isinstance(s, str):
                s = str(s)
            if s and s[0] != "-" and " " in s:
                escaped = '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
            else:
                escaped = s
            if escaped is not None:
                joined += escaped + " "
        return joined.strip()

    @staticmethod
    def version():
        return int(chloe.VersionInfo("VERSION_NUM"))

    @staticmethod
    def readableVersion():
        return chloe.VersionInfo("RELEASE_NAME")

    @staticmethod
    def chloeHelpPath():
        return "http://www.chloe.org/"

    @staticmethod
    def ogrConnectionStringFromLayer(layer):
        """Generates OGR connection string from a layer"""
        return ChloeUtils.ogrConnectionStringAndFormatFromLayer(layer)[0]

    @staticmethod
    def ogrConnectionStringAndFormat(uri, context):
        """Generates OGR connection string and format string from layer source
        Returned values are a tuple of the connection string and format string
        """
        ogrstr = None
        format = None

        layer = QgsProcessingUtils.mapLayerFromString(uri, context, False)
        if layer is None:
            path, ext = os.path.splitext(uri)
            format = QgsVectorFileWriter.driverForExtension(ext)
            return uri, '"' + format + '"'

        return ChloeUtils.ogrConnectionStringAndFormatFromLayer(layer)

    @staticmethod
    def ogrConnectionStringAndFormatFromLayer(layer):
        provider = layer.dataProvider().name()
        if provider == "spatialite":
            # dbname='/geodata/osm_ch.sqlite' table="places" (Geometry) sql=
            regex = re.compile("dbname='(.+)'")
            r = regex.search(str(layer.source()))
            ogrstr = r.groups()[0]
            format = "SQLite"
        elif provider == "postgres":
            # dbname='ktryjh_iuuqef' host=spacialdb.com port=9999
            # user='ktryjh_iuuqef' password='xyqwer' sslmode=disable
            # key='gid' estimatedmetadata=true srid=4326 type=MULTIPOLYGON
            # table="t4" (geom) sql=
            dsUri = QgsDataSourceUri(layer.dataProvider().dataSourceUri())
            conninfo = dsUri.connectionInfo()
            conn = None
            ok = False
            while not conn:
                try:
                    conn = psycopg2.connect(dsUri.connectionInfo())
                except psycopg2.OperationalError:
                    (ok, user, passwd) = QgsCredentials.instance().get(
                        conninfo, dsUri.username(), dsUri.password()
                    )
                    if not ok:
                        break

                    dsUri.setUsername(user)
                    dsUri.setPassword(passwd)

            if not conn:
                raise RuntimeError(
                    "Could not connect to PostgreSQL database - check connection info"
                )

            if ok:
                QgsCredentials.instance().put(conninfo, user, passwd)

            ogrstr = "PG:%s" % dsUri.connectionInfo()
            format = "PostgreSQL"
        elif provider == "mssql":
            # 'dbname=\'db_name\' host=myHost estimatedmetadata=true
            # srid=27700 type=MultiPolygon table="dbo"."my_table"
            # #(Shape) sql='
            dsUri = layer.dataProvider().uri()
            ogrstr = "MSSQL:"
            ogrstr += "database={0};".format(dsUri.database())
            ogrstr += "server={0};".format(dsUri.host())
            if dsUri.username() != "":
                ogrstr += "uid={0};".format(dsUri.username())
            else:
                ogrstr += "trusted_connection=yes;"
            if dsUri.password() != "":
                ogrstr += "pwd={0};".format(dsUri.password())
            ogrstr += "tables={0}".format(dsUri.table())
            format = "MSSQL"
        elif provider == "oracle":
            # OCI:user/password@host:port/service:table
            dsUri = QgsDataSourceUri(layer.dataProvider().dataSourceUri())
            ogrstr = "OCI:"
            if dsUri.username() != "":
                ogrstr += dsUri.username()
                if dsUri.password() != "":
                    ogrstr += "/" + dsUri.password()
                delim = "@"

            if dsUri.host() != "":
                ogrstr += delim + dsUri.host()
                delim = ""
                if dsUri.port() != "" and dsUri.port() != "1521":
                    ogrstr += ":" + dsUri.port()
                ogrstr += "/"
                if dsUri.database() != "":
                    ogrstr += dsUri.database()
            elif dsUri.database() != "":
                ogrstr += delim + dsUri.database()

            if ogrstr == "OCI:":
                raise RuntimeError("Invalid oracle data source - check connection info")

            ogrstr += ":"
            if dsUri.schema() != "":
                ogrstr += dsUri.schema() + "."

            ogrstr += dsUri.table()
            format = "OCI"
        else:
            ogrstr = str(layer.source()).split("|")[0]
            path, ext = os.path.splitext(ogrstr)
            format = QgsVectorFileWriter.driverForExtension(ext)

        return ogrstr, '"' + format + '"'

    @staticmethod
    def ogrLayerName(uri):
        uri = uri.strip('"')
        # if os.path.isfile(uri):
        #    return os.path.basename(os.path.splitext(uri)[0])

        if " table=" in uri:
            # table="schema"."table"
            re_table_schema = re.compile(' table="([^"]*)"\\."([^"]*)"')
            r = re_table_schema.search(uri)
            if r:
                return r.groups()[0] + "." + r.groups()[1]
            # table="table"
            re_table = re.compile(' table="([^"]*)"')
            r = re_table.search(uri)
            if r:
                return r.groups()[0]
        elif "layername" in uri:
            regex = re.compile("(layername=)([^|]*)")
            r = regex.search(uri)
            return r.groups()[1]

        fields = uri.split("|")
        basePath = fields[0]
        fields = fields[1:]
        layerid = 0
        for f in fields:
            if f.startswith("layername="):
                return f.split("=")[1]
            if f.startswith("layerid="):
                layerid = int(f.split("=")[1])

        ds = ogr.Open(basePath)
        if not ds:
            return None

        ly = ds.GetLayer(layerid)
        if not ly:
            return None

        name = ly.GetName()
        ds = None
        return name

    @staticmethod
    def parseCreationOptions(value):
        parts = value.split("|")
        options = []
        for p in parts:
            options.extend(["-co", p])
        return options

    @staticmethod
    def writeLayerParameterToTextFile(
        filename, alg, parameters, parameter_name, context, quote=True, executing=False
    ):
        listFile = os.path.join(QgsProcessingUtils.tempFolder(), filename)
        with open(listFile, "w") as f:
            if executing:
                layers = []
                for l in alg.parameterAsLayerList(parameters, parameter_name, context):
                    if quote:
                        layers.append('"' + l.source() + '"')
                    else:
                        layers.append(l.source())
                f.write("\n".join(layers))
        return listFile

    @staticmethod
    def chloe_crs_string(crs):
        """
        Converts a QgsCoordinateReferenceSystem to a string understandable
        by CHLOE
        :param crs: crs to convert
        :return: chloe friendly string
        """
        if crs.authid().upper().startswith("EPSG:"):
            return crs.authid()

        # fallback to proj4 string, stripping out newline characters
        return crs.toProj4().replace("\n", " ").replace("\r", " ")

    # --------------------------------------------------ADD----------------------

    @staticmethod
    def formatString(path_file, isWindowPath=False, encoding="utf8"):
        res = path_file  # .encode(encoding)
        if isWindowPath:
            res = res.replace("/", "\\").replace("\\", "\\\\").replace(":", "\:")
        return res

    @staticmethod
    def wrapperSetValue(wrapper, value):
        """setValue function for wrapper to be used for 3.2 or 3.4"""
        w = wrapper
        wrappedWidget = getattr(wrapper, "wrappedWidget", None)
        if callable(wrappedWidget):
            w = wrappedWidget()
        w.setValue(value)

    @staticmethod
    def file_get_contents(filename, encoding="utf-8", context=False):
        if os.path.exists(filename):
            with open(filename, "rb") as file:
                data = file.read()
                data = data.decode("utf-8")
            if context:
                template = Template(data)
                return template.render(context)
            else:
                return data
        else:
            return None

    @staticmethod
    def deduceLayerName(layer, defaultName="output") -> str:
        res = defaultName
        if not (layer is None):
            if isinstance(layer, QgsRasterLayer):
                layerSource = layer.dataProvider().dataSourceUri()
                basename = os.path.basename(layerSource)
                res = os.path.splitext(basename)[0]
            elif isinstance(layer, str):
                basename = os.path.basename(layer)
                res = os.path.splitext(basename)[0]
            else:
                res = str(layer)
        return res

    @staticmethod
    def setLayerSymbology(layer, qmlFilename):
        styleFilepath = (
            os.path.dirname(__file__) + os.sep + "styles" + os.sep + qmlFilename
        )
        layer.loadNamedStyle(styleFilepath)

        # getting statistics from the layer
        stats = layer.dataProvider().bandStatistics(
            1, QgsRasterBandStats.All, layer.extent()
        )
        min = stats.minimumValue
        max = stats.maximumValue

        # print("symbology " + str(min) + " " + str(max))
        # adjusting the symbology to equal intervals from the
        renderer = layer.renderer()
        shader = renderer.shader()
        colorRampShader = shader.rasterShaderFunction()
        if type(colorRampShader) is QgsColorRampShader:
            colorRampItemList = colorRampShader.colorRampItemList()
            nbClasses = len(colorRampItemList)
            newColorRampList = []
            for i in range(0, nbClasses):
                val = min + (i * (max - min) / (nbClasses - 1))
                item = QgsColorRampShader.ColorRampItem(
                    val, (colorRampItemList[i]).color, str(val)
                )
                newColorRampList.append(item)
            colorRampShader.setColorRampItemList(newColorRampList)
        # layer.triggerRepaint()

    @staticmethod
    def extractValueNotNull(f_input):
        # === Test algorithm
        ds = gdal.Open(f_input)  # DataSet
        band = ds.GetRasterBand(1)  # -> band
        array = np.array(band.ReadAsArray())  # -> matrice values
        values = np.unique(array)
        nodata = band.GetNoDataValue()

        int_values_and_nodata = [
            int(math.floor(x)) for x in values[(values != 0) & (values != nodata)]
        ]

        return int_values_and_nodata

    @staticmethod
    def calculateMetric(metric, metric_simple, metric_cross, value_list):
        """Renerate and update simple and cross metric"""
        result = copy.deepcopy(metric)
        value_list.sort()

        # Remove duplicates to get a clean array
        clean_list = list(dict.fromkeys(value_list))
        no_zero_list = list(filter(lambda x: x != 0, clean_list))  # Remove value 0

        if len(no_zero_list) < 1000:

            for msk in metric_simple.keys():
                for ms in metric_simple[msk]:
                    for val in no_zero_list:
                        result[msk].append(ms + str(val))

            if len(no_zero_list) < 100:

                for mck in metric_cross.keys():
                    for mc in metric_cross[mck]:
                        for val1 in no_zero_list:  # value_list
                            for val2 in no_zero_list:  # value_list
                                if val1 <= val2:
                                    result[mck].append(mc + str(val1) + "-" + str(val2))
        return result

    @staticmethod
    def adjustTempDirectory(tempDirectory):
        """ """
        if "Local/Temp" in tempDirectory or "Local\Temp" in tempDirectory:
            if not os.path.exists(tempDirectory):
                os.makedirs(tempDirectory)

    @staticmethod
    def adjustExtension(filePath, filePathRef):
        """return the filename of filePath in the directory of filePathRef"""
        extension = os.path.splitext(filePath)[1]
        basename = os.path.splitext(filePathRef)[0]
        res = basename + extension
        # res = os.path.join(dirPath, filename)
        return res

    @staticmethod
    def toOddNumber(input_integer: int) -> int:
        """returns a odd number if input number is even"""
        if int(input_integer) % 2 == 0:
            return int(input_integer) + 1
        else:
            return int(input_integer)

    @staticmethod
    def toEvenNumber(input_integer: int) -> int:
        """returns a even number if input number is odd"""
        if int(input_integer) % 2 > 0:
            return int(input_integer) + 1
        else:
            return int(input_integer)

    @staticmethod
    def displayFloatToInt(input_float) -> str:
        """returns an int formated string if input number is an integer"""
        if input_float is None:
            return None
        elif input_float.is_integer():
            return str(int(input_float))
        else:
            return str(input_float)

    @staticmethod
    def insertWidgetInLayout(
        parent, target_layout_name: str, widget: QWidget, position: int
    ):
        """insert a widget at a given position in a target layout"""
        if not parent:
            return

        for layout in parent.findChildren(QLayout):
            if isinstance(layout, (QVBoxLayout)):
                if layout.objectName() == target_layout_name:
                    layout.insertWidget(position, widget)


class ASCOutputRaster(QgsProcessingOutputRasterLayer):
    def getFileFilter(self, alg):
        """Force asc output raster extension"""

        exts = "ASC files (*.asc);; files (*)"
        return exts


class ParameterFileCSVTXT(QgsProcessingParameterFile):
    def getFileFilter(self, alg):
        """Force csv/txt file extension"""

        exts = "CSV files (*.csv);; TXT files (*.txt);;files (*)"
        return exts
