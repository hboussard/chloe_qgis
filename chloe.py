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
