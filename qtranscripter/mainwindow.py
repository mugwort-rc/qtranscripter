# -*- coding: utf-8 -*-

import os
import numpy as np
import scipy.io.wavfile

from PyQt4.Qt import *
from PyQt4.Qwt5 import *
from PyQt4.phonon import Phonon

from ui_mainwindow import Ui_MainWindow

from models import TimePointModel
from utils import ClickRelease
from utils import TimePointHighlighter

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.lastOpenDir = ""

        self.WAVE_FILTER = self.tr('Wave (*.wav)')

        self.initUi()

    def initUi(self):
        self.plot_width = 1.5  # display sec
        self.dy = None

        self.ui.qwtPlot.setAxisScale(QwtPlot.yLeft, -1, 1)
        self.ui.qwtPlot.setAxisScale(QwtPlot.xBottom,
                                     -self.plot_width,
                                     self.plot_width)

        self.c1 = QwtPlotCurve()
        self.c2 = QwtPlotCurve()

        self.c2.setPen(QColor(Qt.red))

        self.c1.attach(self.ui.qwtPlot)
        self.c2.attach(self.ui.qwtPlot)

        self.obj = Phonon.MediaObject()
        self.dev = Phonon.AudioOutput()
        Phonon.createPath(self.obj, self.dev)

        self.ui.seekSlider.setMediaObject(self.obj)

        self.obj.finished.connect(self.media_finished)
        self.obj.tick.connect(self.ticked)
        # Time picker
        self.picker = QwtPlotPicker(QwtPlot.xBottom,
                                    QwtPlot.yLeft,
                                    QwtPicker.PointSelection,
                                    QwtPlotPicker.CrossRubberBand,
                                    QwtPicker.AlwaysOn,
                                    self.ui.qwtPlot.canvas())
        self.picker.selected.connect(self.selected)
        # hook click of seekslider
        self.mouseRelease = ClickRelease()
        self.ui.seekSlider.installEventFilter(self.mouseRelease)
        self.mouseRelease.released.connect(self.released)

        self.timePointModel = TimePointModel(self)
        self.ui.listView.setModel(self.timePointModel)

        self.highlighter = TimePointHighlighter(self.ui.textEdit.document())

        self.ui.splitter.setStretchFactor(0, 1)
        self.ui.splitter.setStretchFactor(1, 4)

        self.timer = QTimer()
        self.timer.timeout.connect(self.replot)
        if os.name == 'posix':
            self.time = QTime()

    def getOpenFileName(self, filter, caption='', dir=None):
        if dir is None:
            dir = self.lastOpenDir
        return QFileDialog.getOpenFileName(self, caption, dir, filter)

    def getSaveFileName(self, filter, caption='', dir=None):
        if dir is None:
            dir = self.lastOpenDir
        return QFileDialog.getSaveFileName(self, caption, dir, filter)

    def setLastOpenDirectory(self, path):
        info = QFileInfo(path)
        if info.isDir():
            self.lastOpenDir = path
        else:
            self.lastOpenDir = info.dir().path()

    def plot(self, start):
        start -= start % 2
        cnt = int(start * (self.rate/1000.0))
        self.ui.statusbar.showMessage(self.tr('%1 / %2')
                                          .arg(cnt/1000.0)
                                          .arg(self.nframe/1000.0))
        wid = self.plot_width * self.rate
        end = cnt+wid
        bef = cnt-wid
        self.c2.setData([cnt*self.interval]*2, [-1, 1])
        dx = np.arange(max(bef, 0), min(end, self.nframe)) * self.interval
        if bef < 0:
            self.c1.setData(dx, self.dy[:end])
        elif bef >= 0 and end < self.nframe-1:
            self.c1.setData(dx, self.dy[bef:end])
        else:
            self.c1.setData(dx, self.dy[bef:])
        self.ui.qwtPlot.setAxisScale(QwtPlot.xBottom,
                                     bef*self.interval,
                                     end*self.interval)
        self.ui.qwtPlot.replot()

    def update_pause_stop(self):
        self.ui.actionStartPause.setText(self.tr('Start'))

    @pyqtSlot(QPointF)
    def selected(self, point):
        if self.obj.state() not in [Phonon.PlayingState,
                                    Phonon.PausedState,
                                    Phonon.BufferingState]:
            return
        time = point.x() * 1000
        self.obj.seek(time)
        self.plot(int(time))

    @pyqtSlot()
    def released(self):
        if self.obj.state() not in [Phonon.PlayingState,
                                    Phonon.PausedState,
                                    Phonon.BufferingState]:
            return
        self.plot(self.obj.currentTime())

    @pyqtSlot(int)
    def ticked(self, time):
        if os.name == 'posix':
            self.time.restart()

    @pyqtSlot()
    def replot(self):
        if self.obj.state() != Phonon.PlayingState:
            return
        if os.name == 'posix':
            self.plot(self.obj.currentTime()+self.time.elapsed())
        else:
            self.plot(self.obj.currentTime())

    @pyqtSlot()
    def on_textEdit_textChanged(self):
        reg = QRegExp(r'<(\d{2}:\d{2}:\d{2}(.\d+)?)>')
        text = self.ui.textEdit.toPlainText()
        points = []
        index = reg.indexIn(text)
        while index != -1:
            points.append((reg.cap(1), index))
            index = reg.indexIn(text, index+reg.matchedLength())
        self.timePointModel.setPoints(points)

    @pyqtSlot(QModelIndex)
    def on_listView_doubleClicked(self, index):
        data = index.data().toString()
        value = index.data(Qt.UserRole)
        assert not value.isNull()
        text,pos = value.toPyObject()
        cursor = self.ui.textEdit.textCursor()
        cursor.setPosition(pos)
        self.ui.textEdit.setTextCursor(cursor)
        self.ui.textEdit.setFocus()

        if self.obj.state() != Phonon.PausedState:
            return

        reg = QRegExp(r'(\d{2}):(\d{2}):(\d{2})(.(\d+))?')
        if reg.exactMatch(data):
            hour   = int(reg.cap(1))
            minute = int(reg.cap(2))
            second = int(reg.cap(3))
            milsec = 0
            if reg.cap(4):
                milsec = int(reg.cap(5))
            time = hour * 3600000 + minute * 60000 + second * 1000 + milsec
            time -= self.baseMsecs()
            if time < 0:
                time = 0
            self.obj.seek(time)
            self.plot(time)

    @pyqtSlot()
    def on_actionWaveOpen_triggered(self):
        filepath = self.getOpenFileName(self.WAVE_FILTER)
        if filepath.isEmpty():
            return
        self.setLastOpenDirectory(filepath)
        filepath = unicode(filepath)
        # get media
        self.rate, self.wav = scipy.io.wavfile.read(filepath, mmap=True)
        self.nframe = len(self.wav)
        self.interval = 1.0 / self.rate
        if self.dy is not None:
            self.dy = None
        # get 1ch
        if isinstance(self.wav[0], np.ndarray):
            ch = len(self.wav[0])
            self.dy = self.wav.reshape(self.nframe*ch)[::ch] / 32768.0
        else:
            self.dy = self.wav / 32768.0

        self.setWindowTitle(self.tr("%1").arg(QFileInfo(filepath).fileName()))

        # set media
        self.obj.setCurrentSource(Phonon.MediaSource(filepath))
        self.plot(0)

    @pyqtSlot()
    def on_actionStartPause_triggered(self):
        if ( self.obj.state() == Phonon.StoppedState or
             self.obj.state() == Phonon.PausedState ):
            self.obj.play()
            self.timer.start(16)
            if os.name == 'posix':
                self.time.start()
            self.ui.actionStartPause.setText(self.tr('Pause'))
        elif self.obj.state() == Phonon.PlayingState:
            self.obj.pause()
            self.timer.stop()
            self.update_pause_stop()
        elif self.obj.state() == Phonon.BufferingState:
            pass
        else:
            print 'Unknown state:', self.obj.state()

    @pyqtSlot()
    def on_actionStop_triggered(self):
        self.obj.stop()
        self.update_pause_stop()

    @pyqtSlot()
    def media_finished(self):
        self.update_pause_stop()

    @pyqtSlot()
    def on_actionInsertTimestamp_triggered(self):
        time = self.obj.currentTime() + self.baseMsecs()
        milsec = time % 1000
        second = time / 1000 % 60
        minute = time / 1000 / 60 % 60
        hour   = time / 1000 / 60 / 60
        text = '<{:02d}:{:02d}:{:02d}.{}>'.format(hour, minute, second, milsec)
        self.ui.textEdit.textCursor().insertText(text)

    def baseMsecs(self):
        return QTime(0, 0).msecsTo(self.ui.timeEdit.time())

    @pyqtSlot()
    def on_actionBack_triggered(self):
        self.back(1000)

    @pyqtSlot()
    def on_actionForward_triggered(self):
        self.forward(1000)

    def back(self, back):
        time = self.obj.currentTime() - back
        self.obj.seek(time)
        self.plot(time)

    def forward(self, forward):
        time = self.obj.currentTime() + forward
        self.obj.seek(time)
        self.plot(time)

    @pyqtSlot()
    def on_actionCursorLeft_triggered(self):
        self.moveCursor(QTextCursor.Left)

    @pyqtSlot()
    def on_actionCursorRight_triggered(self):
        self.moveCursor(QTextCursor.Right)

    @pyqtSlot()
    def on_actionCursorUp_triggered(self):
        self.moveCursor(QTextCursor.Up)

    @pyqtSlot()
    def on_actionCursorDown_triggered(self):
        self.moveCursor(QTextCursor.Down)

    @pyqtSlot()
    def on_actionSelectLeft_triggered(self):
        self.moveCursor(QTextCursor.Left, QTextCursor.KeepAnchor)

    @pyqtSlot()
    def on_actionSelectRight_triggered(self):
        self.moveCursor(QTextCursor.Right, QTextCursor.KeepAnchor)

    @pyqtSlot()
    def on_actionSelectUp_triggered(self):
        self.moveCursor(QTextCursor.Up, QTextCursor.KeepAnchor)

    @pyqtSlot()
    def on_actionSelectDown_triggered(self):
        self.moveCursor(QTextCursor.Down, QTextCursor.KeepAnchor)

    def moveCursor(self, move, anchor=QTextCursor.MoveAnchor):
        cursor = self.ui.textEdit.textCursor()
        cursor.movePosition(move, anchor)
        self.ui.textEdit.setTextCursor(cursor)

    @pyqtSlot()
    def on_actionTextCopy_triggered(self):
        text = self.ui.textEdit.toPlainText()
        QApplication.clipboard().setText(text)

    @pyqtSlot()
    def on_actionTextPaste_triggered(self):
        text = QApplication.clipboard().text()
        self.ui.textEdit.insertPlainText(text)

    @pyqtSlot()
    def on_actionInsertUnprintable_triggered(self):
        unprintable = u"\u25a0"
        self.ui.textEdit.insertPlainText(unprintable)
