import serial

class KERN_16K0_05:
    # At the time of writing this code (August 2025), the documentation of this instrument was available on URL
    # https://dok.kern-sohn.com/manuals/files/English/572-573-KB-DS-FKB-FCB-KBJ-BA-e-1774.pdf .

    POSSIBLE_BAUD_RATES = [2400, 4800, 9600, 19200] # list of all baud rate ajustable (cf. section 7.4 "Interface RS 232 C" of the instrument documentation)
    DEFAULT_BAUD_RATE = POSSIBLE_BAUD_RATES[2]

    serial: serial.Serial

    def __init__(self):
        self.serial = serial.Serial()

    def last_data_transfer_bytearray(self):
        """returns in a bytearray the last data transfer in buffer from the instrument"""
        self.serial.reset_input_buffer()
        dt_reading = self.serial.read(18) # cf. section 7.5.1 "Description of the data transfer" of the instrument documentation
        return bytearray(dt_reading)

    def connect(self, serial_port:str, baudrate:int):
        """Instrument initialization (including serial port and baud rate verification).
        In the event of a malfunction, return in 'warning' output an appropriated string."""

        self.serial = serial.Serial(serial_port, baudrate)
        initial_timeout = self.serial.timeout
        self.serial.timeout = 1  # timeout of the serial port = 1s
        ldtba = self.last_data_transfer_bytearray()
        self.serial.timeout = initial_timeout
        initialized = len(ldtba) != 0
        warning = ""
        if initialized:
            try:
                self.current_value()
            except ValueError as ve:
                if ve.__str__()[0:34] == "could not convert string to float:":
                    warning = ("INITIALISATION TEST : impossible conversion from string to float. "
                               "Maybe the baud rate is wrong ?")
                    initialized = False
        else: warning = ("INITIALISATION TEST : no data from the instrument. Check the instrument is well pluged and the serial port is the right one. ")
        return initialized, warning

    def current_value(self):
        """once the instrument is initialized, return its current measured value"""
        ldtba = self.last_data_transfer_bytearray()
        new_ba = ldtba[4:13] # cf. section 7.5.1 "Description of the data transfer" of the instrument documentation
        return float(new_ba)

    def disconnect(self):
        """close the instrument communication"""
        self.serial.close()