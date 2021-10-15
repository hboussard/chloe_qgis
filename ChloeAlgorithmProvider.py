# -*- coding: utf-8 -*-

"""
***************************************************************************
    ChloeAlgorithmProvider.py
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

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.core import (QgsApplication,
                       QgsProcessingProvider,
                       QgsRuntimeProfiler)
from processing.core.ProcessingConfig import ProcessingConfig, Setting
from .ChloeUtils import ChloeUtils

from .algorithms.from_csv_algorithm import FromCSVAlgorithm
from .algorithms.from_shapefile_algorithm import FromShapefileAlgorithm
from .algorithms.grid_algorithm import GridAlgorithm
from .algorithms.grid_multi_algorithm import GridMultiAlgorithm
from .algorithms.map_algorithm import MapAlgorithm
from .algorithms.selected_algorithm import SelectedAlgorithm
from .algorithms.selected_multi_algorithm import SelectedMultiAlgorithm
from .algorithms.sliding_algorithm import SlidingAlgorithm
from .algorithms.sliding_multi_algorithm import SlidingMultiAlgorithm
from .algorithms.cluster_algorithm import ClusterAlgorithm
from .algorithms.classification_algorithm import ClassificationAlgorithm
from .algorithms.distance_algorithm import DistanceAlgorithm
from .algorithms.overlay_algorithm import OverlayAlgorithm
from .algorithms.filter_algorithm import FilterAlgorithm
from .algorithms.search_and_replace_algorithm import SearchAndReplaceAlgorithm
from .algorithms.combine_algorithm import CombineAlgorithm


class ChloeAlgorithmProvider(QgsProcessingProvider):

    def __init__(self):
        super().__init__()
        self.algs = []

    def load(self):
        with QgsRuntimeProfiler.profile('Chloe Provider'):
            ProcessingConfig.settingIcons[self.name()] = self.icon()
            ProcessingConfig.addSetting(Setting(self.name(), 'ACTIVATE_CHLOE',
                                                self.tr('Activate'), True))
            ProcessingConfig.addSetting(Setting(
                self.name(),
                ChloeUtils.JAVA,
                self.tr('Path java exe'),
                ''))
            ProcessingConfig.readSettings()
            self.refreshAlgorithms()
        return True

    def unload(self):
        ProcessingConfig.removeSetting('ACTIVATE_CHLOE')
        ProcessingConfig.removeSetting(ChloeUtils.JAVA)

    def isActive(self):
        return ProcessingConfig.getSetting('ACTIVATE_CHLOE')

    def setActive(self, active):
        ProcessingConfig.setSettingValue('ACTIVATE_CHLOE', active)

    def name(self):
        return 'Chloe - Landscape metrics'

    def longName(self):
        #version = ChloeUtils.readableVersion()
        # return 'CHLOE ({})'.format(version)
        return 'Chloe - Landscape metrics'

    def id(self):
        return 'chloe'

    def helpId(self):
        return 'chloe'

    def icon(self):
        iconPath = os.path.normpath(os.path.join(
            os.path.dirname(__file__), 'images', 'chloe_icon.png'))
        return QIcon(iconPath)

    # def svgIconPath(self):
    #    return QgsApplication.iconPath("providerChloe.svg")

    def loadAlgorithms(self):
        self.algs = [
            FromCSVAlgorithm(),
            FromShapefileAlgorithm(),
            GridAlgorithm(),
            GridMultiAlgorithm(),
            MapAlgorithm(),
            SelectedAlgorithm(),
            SelectedMultiAlgorithm(),
            SlidingAlgorithm(),
            SlidingMultiAlgorithm(),
            ClusterAlgorithm(),
            ClassificationAlgorithm(),
            DistanceAlgorithm(),
            OverlayAlgorithm(),
            FilterAlgorithm(),
            SearchAndReplaceAlgorithm(),
            CombineAlgorithm()
        ]
        for a in self.algs:
            self.addAlgorithm(a)

    def supportedOutputRasterLayerExtensions(self):
        return ChloeUtils.getSupportedRasterExtensions()

    def supportsNonFileBasedOutput(self):
        """
        CHLOE Provider doesn't support non file based outputs
        """
        return False

    def tr(self, string, context=''):
        if context == '':
            context = 'ChloeAlgorithmProvider'
        return QCoreApplication.translate(context, string)
