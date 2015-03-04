# -*- coding: utf-8 -*-

from PyQt4.Qt import *

class TimePointModel(QAbstractListModel):
    def __init__(self, parent=None):
        super(TimePointModel, self).__init__(parent)
        self._points = []

    def points(self):
        return self._points

    def setPoints(self, points):
        self.beginResetModel()
        self._points = points
        self.endResetModel()

    def reset(self):
        self.setPoints([])

    def columnCount(self, parent=QModelIndex()):
        if not self._points:
            return 0
        return 1

    def rowCount(self, parent=QModelIndex()):
        if not self._points:
            return 0
        return len(self._points)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.UserRole:
            return self._points[index.row()]
        if role != Qt.DisplayRole:
            return QVariant()
        if not self._points:
            return QVariant()
        val = self._points[index.row()]
        return val[0]
