# -*- coding: utf-8 -*-

"""
***************************************************************************
    Postprocessing.py
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


__author__ = 'Victor Olaya'
__date__ = 'August 2012'
__copyright__ = '(C) 2012, Victor Olaya'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import traceback
from qgis.PyQt.QtWidgets import QApplication
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (Qgis,
                       QgsProject,
                       QgsProcessingFeedback,
                       QgsProcessingUtils,
                       QgsMapLayer,
                       QgsWkbTypes,
                       QgsMessageLog,
                       QgsProviderRegistry)

from processing.core.ProcessingConfig import ProcessingConfig
from processing.gui.RenderingStyles import RenderingStyles

#from processing.gui.Postprocessing import set_layer_name

def ChloehandleAlgorithmResults(alg, context, feedback=None, showResults=True):
    # Overload
    feedback.setProgressText('ChloehandleAlgorithmResults')
    wrongLayers = []
    if feedback is None:
        feedback = QgsProcessingFeedback()
    feedback.setProgressText(QCoreApplication.translate('Postprocessing', 'Loading resulting layers'))
    i = 0

    for l, details in context.layersToLoadOnCompletion().items():
        # Overload
        QgsMessageLog.logMessage( l,'Processing', Qgis.Info)

        if feedback.isCanceled():
            return False

        if len(context.layersToLoadOnCompletion()) > 2:
            # only show progress feedback if we're loading a bunch of layers
            feedback.setProgress(100 * i / float(len(context.layersToLoadOnCompletion())))

        try:
            layer = QgsProcessingUtils.mapLayerFromString(l, context, typeHint=details.layerTypeHint)
            if layer is not None:
                #set_layer_name(layer, details)

                style = None
                if details.outputName:
                    style = RenderingStyles.getStyle(alg.id(), details.outputName)
                if style is None:
                    if layer.type() == QgsMapLayer.RasterLayer:
                        style = ProcessingConfig.getSetting(ProcessingConfig.RASTER_STYLE)
                    else:
                        if layer.geometryType() == QgsWkbTypes.PointGeometry:
                            style = ProcessingConfig.getSetting(ProcessingConfig.VECTOR_POINT_STYLE)
                        elif layer.geometryType() == QgsWkbTypes.LineGeometry:
                            style = ProcessingConfig.getSetting(ProcessingConfig.VECTOR_LINE_STYLE)
                        else:
                            style = ProcessingConfig.getSetting(ProcessingConfig.VECTOR_POLYGON_STYLE)
                if style:
                    layer.loadNamedStyle(style)

                details.project.addMapLayer(context.temporaryLayerStore().takeMapLayer(layer))

                if details.postProcessor():
                    details.postProcessor().postProcessLayer(layer, context, feedback)

            else:
                wrongLayers.append(str(l))
        except Exception:
            QgsMessageLog.logMessage(QCoreApplication.translate('Postprocessing', "Error loading result layer:") + "\n" + traceback.format_exc(), 'Processing', Qgis.Critical)
            wrongLayers.append(str(l))
        i += 1

    feedback.setProgress(100)

    if wrongLayers:
        msg = QCoreApplication.translate('Postprocessing', "The following layers were not correctly generated.")
        msg += "<ul>" + "".join(["<li>%s</li>" % lay for lay in wrongLayers]) + "</ul>"
        msg += QCoreApplication.translate('Postprocessing', "You can check the 'Log Messages Panel' in QGIS main window to find more information about the execution of the algorithm.")
        feedback.reportError(msg)

    return len(wrongLayers) == 0
