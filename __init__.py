# -*- coding: utf-8 -*-
"""
/***************************************************************************
 APILand
                                 A QGIS plugin
 Interface with APILand
                             -------------------
        begin                : 2017-05-04
        copyright            : (C) 2017 by vbeauzee
        email                : v.beauzee@alkante.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load APILand class from file APILand.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .APILand import APILand
    return APILand(iface)
