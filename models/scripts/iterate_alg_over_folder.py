# -*- coding: utf-8 -*-

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


##group=Chloe
##folder_in=folder
##folder_out=folder

import os
import processing
import time

#get the path of the file in the 'path' variable
for file in os.listdir(folder_in):
    if file.find('.asc') != -1 :
        progress.setText('Fichier ' + file)
        path = folder_in + '/'+ file
        progress.setText('Processing file ' + path);
        rast_in = processing.getObjectFromUri(path);
        rast_out = folder_out + 'distance_' + file; 
        res = processing.runalg("chloe:distance", rast_in, '1', None, rast_out)
        progress.setText('result ' + res);
        time.sleep(2)