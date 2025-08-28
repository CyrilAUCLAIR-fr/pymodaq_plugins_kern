import serial
import time
import string

class KERN_572_573_KB_DS_FKB:
    # At the time of writing this code (August 2025), the documentation of these instruments was available on URL
    # https://dok.kern-sohn.com/manuals/files/English/572-573-KB-DS-FKB-FCB-KBJ-BA-e-1774.pdf .

    POSSIBLE_BAUD_RATES = [2400, 4800, 9600, 19200] # list of all baud rate ajustable (cf. section 7.4 "Interface RS 232 C" of the instrument documentation)
    DEFAULT_BAUD_RATE = POSSIBLE_BAUD_RATES[2]

    WAITING_TIME = 3  # time (in s) to let the input buffer fill in order to test the initialization

    serial: serial.Serial

    def __init__(self):
        self.serial = serial.Serial()

    def connect(self, serial_port:str, baudrate:int):
        """Instrument initialization (including serial port and baud rate verification).
        Returns in 'info' informations to log."""

        def validate_serial_port(input_buffer_content):
            return len(input_buffer_content) != 0

        def validate_baud_rate(input_buffer_content):
            try:
                decoded_input_buffer = input_buffer_content.decode()
                return any(c in string.printable for c in decoded_input_buffer) # standard method to check the channel baud rate
            except UnicodeDecodeError:
                return False

        self.serial = serial.Serial(serial_port, baudrate)
        time.sleep(self.WAITING_TIME)
        input_buffer_content = self.serial.read(self.serial.in_waiting) # reads all the bytes in input buffer
        initialized = validate_serial_port(input_buffer_content)
        if initialized:
            if validate_baud_rate(input_buffer_content):
                info = "KERN weight balance : initialisation done on port " + serial_port + ". Baud rate = " + str(baudrate)
                initialized = True
            else:
                info = "KERN weight balance : initialization test : wrong baud rate"
                initialized = False
        else: info = ("KERN weight balance : initialization test : "
                      "no data from the instrument. Maybe the instrument is not plugged, or the serial port is wrong.")
        return initialized, info

    def current_value(self):
        """once the instrument is initialized, return its current measured value"""
        self.serial.reset_input_buffer()
        data_transfer_bytes = self.serial.read(18) # cf. section 7.5.1 "Description of the data transfer" of the instrument documentation
        data_transfer_bytearray = bytearray(data_transfer_bytes)
        mesured_value_bytearray = data_transfer_bytearray[4:13] # ditto
        return float(mesured_value_bytearray)

    def disconnect(self):
        """close the instrument communication"""
        self.serial.close()