#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: recorder_server_2ch
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
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
from gnuradio import uhd
import time
import recorder_server_2ch_epy_block_0 as epy_block_0  # embedded python block
import threading



class recorder_server_2ch(gr.top_block, Qt.QWidget):

    def __init__(self, cent_freq=430.0e6, rx_gain=8, samp_rate=5e6):
        gr.top_block.__init__(self, "recorder_server_2ch", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("recorder_server_2ch")
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

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "recorder_server_2ch")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Parameters
        ##################################################
        self.cent_freq = cent_freq
        self.rx_gain = rx_gain
        self.samp_rate = samp_rate

        ##################################################
        # Blocks
        ##################################################

        self.uhd_usrp_source_0 = uhd.usrp_source(
            ",".join(("", '')),
            uhd.stream_args(
                cpu_format="fc32",
                args='',
                channels=list(range(0,2)),
            ),
        )
        self.uhd_usrp_source_0.set_samp_rate(samp_rate)
        self.uhd_usrp_source_0.set_time_unknown_pps(uhd.time_spec(0))

        self.uhd_usrp_source_0.set_center_freq(cent_freq, 0)
        self.uhd_usrp_source_0.set_antenna("RX2", 0)
        self.uhd_usrp_source_0.set_gain(rx_gain, 0)

        self.uhd_usrp_source_0.set_center_freq(cent_freq, 1)
        self.uhd_usrp_source_0.set_antenna("RX2", 1)
        self.uhd_usrp_source_0.set_gain(8, 1)
        self.epy_block_0 = epy_block_0.PythonExportBlock(exportmodulename="recorder_server_2ch_export", samp_rate=samp_rate)
        self.blocks_threshold_ff_0 = blocks.threshold_ff((0.5e-5), (1e-5), 0)
        self.blocks_complex_to_mag_squared_0 = blocks.complex_to_mag_squared(1)
        self.analog_quadrature_demod_cf_0 = analog.quadrature_demod_cf(1)


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.epy_block_0, 'cmd_out'), (self.uhd_usrp_source_0, 'command'))
        self.msg_connect((self.uhd_usrp_source_0, 'async_msgs'), (self.epy_block_0, 'msg_in'))
        self.connect((self.analog_quadrature_demod_cf_0, 0), (self.epy_block_0, 0))
        self.connect((self.blocks_complex_to_mag_squared_0, 0), (self.blocks_threshold_ff_0, 0))
        self.connect((self.blocks_threshold_ff_0, 0), (self.epy_block_0, 1))
        self.connect((self.uhd_usrp_source_0, 0), (self.analog_quadrature_demod_cf_0, 0))
        self.connect((self.uhd_usrp_source_0, 1), (self.blocks_complex_to_mag_squared_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "recorder_server_2ch")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_cent_freq(self):
        return self.cent_freq

    def set_cent_freq(self, cent_freq):
        self.cent_freq = cent_freq
        self.uhd_usrp_source_0.set_center_freq(self.cent_freq, 0)
        self.uhd_usrp_source_0.set_center_freq(self.cent_freq, 1)

    def get_rx_gain(self):
        return self.rx_gain

    def set_rx_gain(self, rx_gain):
        self.rx_gain = rx_gain
        self.uhd_usrp_source_0.set_gain(self.rx_gain, 0)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.uhd_usrp_source_0.set_samp_rate(self.samp_rate)



def argument_parser():
    parser = ArgumentParser()
    parser.add_argument(
        "--cent-freq", dest="cent_freq", type=eng_float, default=eng_notation.num_to_str(float(430.0e6)),
        help="Set Center frequency [default=%(default)r]")
    parser.add_argument(
        "--rx-gain", dest="rx_gain", type=intx, default=8,
        help="Set RX gain [default=%(default)r]")
    parser.add_argument(
        "--samp-rate", dest="samp_rate", type=eng_float, default=eng_notation.num_to_str(float(5e6)),
        help="Set Sample rate [default=%(default)r]")
    return parser


def main(top_block_cls=recorder_server_2ch, options=None):
    if options is None:
        options = argument_parser().parse_args()

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls(cent_freq=options.cent_freq, rx_gain=options.rx_gain, samp_rate=options.samp_rate)

    tb.start()
    tb.flowgraph_started.set()

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
