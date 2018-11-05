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

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

import os
import sys
import inspect
import locale

from processing.core.Processing import Processing
from chloe_provider import ChloeProvider

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

class CholePlugin:
    """Main input of Chloe plugin"""
    
    def __init__(self):    
        #i18n
        pluginPath = QFileInfo(os.path.realpath(__file__)).path()  # patch by Régis Haubourg

        loc = QSettings().value('locale/userLocale')
        if len(loc) == 5:
            localeName = loc
        elif len(loc) == 2:
            localeName = locale.locale_alias[loc].split('.')[0]
        else:
            localeName = QLocale.system().name()


        if QFileInfo(pluginPath).exists():
            self.localePath = pluginPath+os.sep+"i18n"+os.sep+"Chloe_" + localeName + ".qm"
        if QFileInfo(self.localePath).exists():
            self.translator = QTranslator()
            self.translator.load(self.localePath)
            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        self.provider = ChloeProvider()

    def initGui(self):
        Processing.addProvider(self.provider)

    def unload(self):
        Processing.removeProvider(self.provider)
