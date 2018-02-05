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