# -*- coding: utf-8 -*-

from PyQt4.Qt import *

class ClickRelease(QObject):

    released = pyqtSignal()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonRelease:
            self.released.emit()
        return super(ClickRelease, self).eventFilter(obj, event)

class TimePointHighlighter(QSyntaxHighlighter):
    def highlightBlock(self, text):
        fmt = QTextCharFormat()
        fmt.setForeground(Qt.blue)
        fmt.setFontWeight(QFont.Bold)

        points = []

        reg = QRegExp(r'<(\d{2}:\d{2}:\d{2}(.\d+)?)>')
        index = reg.indexIn(text)
        while index != -1:
            length = reg.matchedLength()
            self.setFormat(index, length, fmt)
            index = reg.indexIn(text, index+length)

