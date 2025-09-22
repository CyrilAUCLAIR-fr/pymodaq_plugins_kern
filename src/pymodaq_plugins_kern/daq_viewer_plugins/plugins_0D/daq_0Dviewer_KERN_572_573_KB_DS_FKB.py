import numpy as np

from pymodaq_utils.utils import ThreadCommand
from pymodaq_data.data import DataToExport
from pymodaq_gui.parameter import Parameter

from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.data import DataFromPlugins

from pymodaq.utils.logger import set_logger
logger = set_logger('viewer0D_plugins', add_to_console=True)

from pymodaq_plugins_kern.hardware.KERN_572_573_KB_DS_FKB import KERN_572_573_KB_DS_FKB

import serial.tools.list_ports

class DAQ_0DViewer_KERN_572_573_KB_DS_FKB(DAQ_Viewer_base):
    """ Instrument plugin class for a OD viewer.

    This viewer concerns the 572, 573, KB, DS and FKB precision balances of KERN & SOHN instruments.

    It has been tested with a FKB 16K0.05 instrument.

    It has been tested with PyMoDAQ 5.

    Operating system’s version : Windows 10 Professional

    No manufacturer's driver need to be installed to make it run.

    Attributes:
    -----------
    controller: object
        The particular object that allow the communication with the hardware, in general a python wrapper around the
         hardware library.

    """
    available_serial_ports = [] # list of all available serial port on the used computer
    # filling of this listing :
    for port in serial.tools.list_ports.comports():
        available_serial_ports.append(port.device)

    params = comon_parameters+[
        {'title': 'Serial Port', 'name': 'serial_port', 'type': 'list', 'limits': available_serial_ports},
        {'title': 'Baud rate', 'name': 'baudrate', 'type': 'list',
         'limits': KERN_572_573_KB_DS_FKB.POSSIBLE_BAUD_RATES, 'value': KERN_572_573_KB_DS_FKB.DEFAULT_BAUD_RATE},
        {'title': 'Measurement unit', 'name': 'measurement_unit', 'type': 'list',
         'limits': KERN_572_573_KB_DS_FKB.AVAILABLE_MEASUREMENT_UNITS,
         'value': KERN_572_573_KB_DS_FKB.DEFAULT_MEASUREMENT_UNIT}
        ]

    def ini_attributes(self):
        #  autocompletion
        self.controller: KERN_572_573_KB_DS_FKB = None

        pass

    def ini_detector(self, controller=None):
        """Detector communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator/detector by controller
            (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """
        serial_port = self.settings['serial_port']
        baudrate = self.settings['baudrate']

        if self.is_master:
            self.controller = KERN_572_573_KB_DS_FKB()
            initialized, info = self.controller.connect(serial_port, baudrate)

        else:
            self.controller = controller
            initialized = True
            info = "KERN weight balance : Initialisation OK"

        self.dte_signal_temp.emit(DataToExport(name='KERN plugin',
                                               data=[DataFromPlugins(name='KERN weight balance',
                                                                    data=[np.array([0])],
                                                                    dim='Data0D',
                                                                    labels=['mesured weight (' + self.settings['measurement_unit'] + ')'])]))
        if info != "":
            if initialized:
                logger.info(info)
            else:
                logger.warning(info)

        return info, initialized



    def close(self):
        """Terminate the communication protocol"""
        if self.is_master:
            self.controller.disconnect()

    def grab_data(self, Naverage=1, **kwargs):
        """Start a grab from the detector

        Parameters
        ----------
        Naverage: int
            Number of hardware averaging (if hardware averaging is possible, self.hardware_averaging should be set to
            True in class preamble and you should code this implementation)
        kwargs: dict
            others optionals arguments
        """

        # synchrone method (blocking function)
        current_measured_value = self.controller.current_value()
        self.dte_signal.emit(DataToExport(name='KERN plugin',
                                        data=[DataFromPlugins(name='KERN weight balance',
                                                                data=current_measured_value, units=self.settings['measurement_unit'],
                                                                dim='Data0D',
                                                                labels=['measured weight (' + self.settings['measurement_unit'] + ')'])]))

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        return ''


if __name__ == '__main__':
    main(__file__)
