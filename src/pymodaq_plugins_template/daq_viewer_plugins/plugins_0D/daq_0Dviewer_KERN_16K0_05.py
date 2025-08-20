import numpy as np

from pymodaq_utils.utils import ThreadCommand
from pymodaq_data.data import DataToExport
from pymodaq_gui.parameter import Parameter

from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.data import DataFromPlugins

import serial
import serial.tools.list_ports

class KERN_16K0_05:

    serial: serial.Serial

    def __init__(self):
        self.serial = serial.Serial()

    def connect(self, serial_port:str, baudrate:int):
        self.serial = serial.Serial(serial_port, baudrate)
        self.serial.timeout = 1  # timeout of the serial port = 1s
        test_reading = self.serial.read()
        ba = bytearray(test_reading)
        initialized = len(ba) >= 1
        return initialized

    def current_value(self):
        ser = self.serial
        ser.reset_input_buffer()
        new_complete_byte = ser.read(18) # cf. section 7.5.1 "Description of the data transfer" of the instrument documentation

        ba = bytearray(new_complete_byte)
        new_ba = ba[4:12] # ditto
        new_bytes = bytes(new_ba)
        new_value = float(new_bytes)

        return new_value

    def disconnect(self):
        self.serial.close()

# At the time of writing this code, the documentation of this instrument was available on URL
# https://dok.kern-sohn.com/manuals/files/English/572-573-KB-DS-FKB-FCB-KBJ-BA-e-1774.pdf .

class DAQ_0DViewer_KERN_16K0_05(DAQ_Viewer_base):
    """ Instrument plugin class for a OD viewer.
    
    This object inherits all functionalities to communicate with PyMoDAQ’s DAQ_Viewer module through inheritance via
    DAQ_Viewer_base. It makes a bridge between the DAQ_Viewer module and the Python wrapper of a particular instrument.

    This instrument plugin concerns the FKB 16K0.05 precision balance of KERN & SOHN instruments (and has been tested
    with such instrument).

    It has been tested with PyMoDAQ 5.

    Operating system’s version : Windows 10 Professional

    No manufacturer's driver need to be installed to make it run.

    Attributes:
    -----------
    controller: object
        The particular object that allow the communication with the hardware, in general a python wrapper around the
         hardware library.

    # TODO add your particular attributes here if any

    """
    available_serial_ports = [] # list of all available serial port on the used computer
    # filling of this listing :
    for port in serial.tools.list_ports.comports():
        available_serial_ports.append(port.name)

    possible_baudrates = [2400, 4800, 9600, 19200] # list of all baud rate ajustable (cf. section 7.4 "Interface RS 232 C" of the product documentation)

    params = comon_parameters+[
        {'title': 'Serial Port', 'name': 'serial_port', 'type': 'list', 'limits': available_serial_ports},
        {'title': 'Baud rate', 'name': 'baudrate', 'type': 'list', 'limits': possible_baudrates}
        ]

    def ini_attributes(self):
        #  autocompletion
        self.controller: KERN_16K0_05 = None

        pass

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        ## TODO for your custom plugin
        if param.name() == "a_parameter_you've_added_in_self.params":
           self.controller.your_method_to_apply_this_param_change()  # when writing your own plugin replace this line
#        elif ...
        ##

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
        serial_port = self.settings['serial_port'] #"COM1"
        baudrate = self.settings['baudrate'] #9600

        if self.is_master:
            self.controller = KERN_16K0_05()
            # self.controller.connect(serial_port, baudrate)
            # self.controller.serial.timeout = 1 # timeout of the serial port = 1s
            # test_reading = self.controller.serial.read()
            # ba = bytearray(test_reading)
            initialized = self.controller.connect(serial_port, baudrate) # len(ba) >= 1
        else:
            self.controller = controller
            initialized = True

        self.dte_signal_temp.emit(DataToExport(name='Kern plugin',
                                               data=[DataFromPlugins(name='KERN FKB 16K0.05',
                                                                    data=[np.array([0])],
                                                                    dim='Data0D',
                                                                    labels=['mesured weight (g)'])]))

        info = "Whatever info you want to log"
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

        # synchrone version (blocking function)
        try:
            data_tot = self.controller.current_value()
            self.dte_signal.emit(DataToExport(name='myplugin',
                                              data=[DataFromPlugins(name='KERN FKB 16K0.05',
                                                                    data=data_tot,
                                                                    dim='Data0D',
                                                                    labels=['mesured weight (g)'])]))
        except ValueError as ve:
            if ve.__str__()[0:34] == "could not convert string to float:":
                print("DATA GRABING : impossible conversion from string to float. Maybe the baud rate is wrong ?")



    def callback(self):
        """optional asynchrone method called when the detector has finished its acquisition of data"""
        data_tot = self.controller.your_method_to_get_data_from_buffer()
        self.dte_signal.emit(DataToExport(name='myplugin',
                                          data=[DataFromPlugins(name='Mock1', data=data_tot,
                                                                dim='Data0D', labels=['dat0', 'data1'])]))

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        return ''


if __name__ == '__main__':
    main(__file__)
