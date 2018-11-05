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

from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, QUrl, QLocale
from qgis.PyQt.QtWidgets import QDialog, QAbstractItemView, QPushButton, QDialogButtonBox
from qgis.PyQt.QtWebKitWidgets import QWebPage
from qgis.PyQt.QtGui import QStandardItemModel, QStandardItem


from qgis.core import QgsApplication

pluginPath = os.path.split(os.path.dirname(__file__))[0]
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'DlgAbout.ui'))

class AboutDialog(BASE, WIDGET):

    def __init__(self):
        super(AboutDialog, self).__init__(None)
        self.setupUi(self)
        self.title = self.tr("About")
        
    #@pyqtSlot(str)
    def run(self):
        localeName = QLocale.system().name()
        for suf in ['pres', 'dev']:
            htmlFilepath =  os.path.join(pluginPath, '..', 'help_algorithm', 'about_'+suf+'_'+localeName+'.html')
            with open(htmlFilepath, 'r') as htmlFile:
                html=htmlFile.read()
            webView = getattr(self, 'webView_'+suf)
            webView.setHtml(html.decode('UTF-8'), QUrl.fromLocalFile(os.path.join(pluginPath, '..','help_algorithm', 'images' )))
            webView.page().setLinkDelegationPolicy(QWebPage.DelegateExternalLinks)
        
        self.setWindowTitle(self.title)
        self.exec_()
        return True
