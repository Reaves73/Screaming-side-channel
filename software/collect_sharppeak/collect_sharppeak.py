#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: collect_sharppeak
# GNU Radio version: 3.10.9.2

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from gnuradio import analog
import math
from gnuradio import blocks
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation



class collect_sharppeak(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "collect_sharppeak", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("collect_sharppeak")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "collect_sharppeak")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)

        ##################################################
        # Variables
        ##################################################
        self.volume = volume = 0.500
        self.tx_gain = tx_gain = 10
        self.samp_rate = samp_rate = 15e6
        self.rf_gain = rf_gain = 10
        self.lsb_freq = lsb_freq = 434e6
        self.freq_shift = freq_shift = 12.5e6

        ##################################################
        # Blocks
        ##################################################

        self._volume_range = qtgui.Range(0, 100, 0.100, 0.500, 200)
        self._volume_win = qtgui.RangeWidget(self._volume_range, self.set_volume, "Volume", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._volume_win)
        self._tx_gain_range = qtgui.Range(0, 40, 1, 10, 200)
        self._tx_gain_win = qtgui.RangeWidget(self._tx_gain_range, self.set_tx_gain, "TX Gain", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._tx_gain_win)
        self._rf_gain_range = qtgui.Range(0, 40, 1, 10, 200)
        self._rf_gain_win = qtgui.RangeWidget(self._rf_gain_range, self.set_rf_gain, "RX Gain", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._rf_gain_win)
        self._lsb_freq_range = qtgui.Range(425e6, 445e6, 1e6, 434e6, 200)
        self._lsb_freq_win = qtgui.RangeWidget(self._lsb_freq_range, self.set_lsb_freq, "LSB Freq", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._lsb_freq_win)
        self.blocks_throttle2_0 = blocks.throttle( gr.sizeof_gr_complex*1, 10000, True, 0 if "auto" == "auto" else max( int(float(0.1) * 10000) if "auto" == "time" else int(0.1), 1) )
        self.blocks_selector_0 = blocks.selector(gr.sizeof_float*1,0,0)
        self.blocks_selector_0.set_enabled(True)
        self.blocks_null_sink_0 = blocks.null_sink(gr.sizeof_float*1)
        self.blocks_file_sink_1 = blocks.file_sink(gr.sizeof_float*1, '/home/parallels/Desktop/cw-code/data_sharppeak/sharppeak', False)
        self.blocks_file_sink_1.set_unbuffered(False)
        self.analog_quadrature_demod_cf_0 = analog.quadrature_demod_cf(1)
        self.analog_noise_source_x_0 = analog.noise_source_c(analog.GR_GAUSSIAN, 1, 0)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_noise_source_x_0, 0), (self.blocks_throttle2_0, 0))
        self.connect((self.analog_quadrature_demod_cf_0, 0), (self.blocks_selector_0, 0))
        self.connect((self.blocks_selector_0, 1), (self.blocks_file_sink_1, 0))
        self.connect((self.blocks_selector_0, 0), (self.blocks_null_sink_0, 0))
        self.connect((self.blocks_throttle2_0, 0), (self.analog_quadrature_demod_cf_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "collect_sharppeak")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_volume(self):
        return self.volume

    def set_volume(self, volume):
        self.volume = volume

    def get_tx_gain(self):
        return self.tx_gain

    def set_tx_gain(self, tx_gain):
        self.tx_gain = tx_gain

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate

    def get_rf_gain(self):
        return self.rf_gain

    def set_rf_gain(self, rf_gain):
        self.rf_gain = rf_gain

    def get_lsb_freq(self):
        return self.lsb_freq

    def set_lsb_freq(self, lsb_freq):
        self.lsb_freq = lsb_freq

    def get_freq_shift(self):
        return self.freq_shift

    def set_freq_shift(self, freq_shift):
        self.freq_shift = freq_shift




def main(top_block_cls=collect_sharppeak, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
