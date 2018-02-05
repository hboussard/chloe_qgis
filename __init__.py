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

 This script initializes the plugin, making it known to QGIS.
"""

__author__ = 'Jean-Charles Naud/Alkante'
__date__ = '2017-10-17'



# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load Chole class from file Chole.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .chloe import CholePlugin
    return CholePlugin()
