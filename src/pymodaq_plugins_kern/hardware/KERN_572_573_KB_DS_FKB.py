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

    # def last_data_transfer_bytearray(self):
    #     """returns in a bytearray the last data transfer in buffer from the instrument"""
    #     self.serial.reset_input_buffer()
    #     dt_reading = self.serial.read(18) # cf. section 7.5.1 "Description of the data transfer" of the instrument documentation
    #     return bytearray(dt_reading)

    def connect(self, serial_port:str, baudrate:int):
        """Instrument initialization (including serial port and baud rate verification).
        In the event of a malfunction, return in 'warning' output an appropriated string."""

        def validate_serial_port(input_buffer_reading):
            return len(input_buffer_reading) != 0

        def validate_baud_rate(input_buffer_reading):
            try:
                decoded_input_buffer = input_buffer_reading.decode()
                return any(c in string.printable for c in decoded_input_buffer)
            except UnicodeDecodeError:
                return False

        self.serial = serial.Serial(serial_port, baudrate)
        time.sleep(self.WAITING_TIME)
        input_buffer_reading = self.serial.read(self.serial.in_waiting) # reads all the bytes in input buffer
        initialized = validate_serial_port(input_buffer_reading)
        if initialized:
            if validate_baud_rate(input_buffer_reading):
                info = "KERN FKB weight balance : Initialisation done on port " + serial_port + ". Baud rate = " + str(baudrate)
                initialized = True
            else:
                info = "KERN FKB weight balance :INITIALISATION TEST : wrong baud rate"
                initialized = False
        else: info = ("KERN FKB weight balance : INITIALISATION TEST : "
                      "no data from the instrument. Maybe the instrument is not pluged, or the serial port is wrong.")
        return initialized, info

    def current_value(self):
        """once the instrument is initialized, return its current measured value"""
        self.serial.reset_input_buffer()
        data_transfer_bytes = self.serial.read(18) # cf. section 7.5.1 "Description of the data transfer" of the instrument documentation
        #     return bytearray(dt_reading)
        data_transfer_bytearray = bytearray(data_transfer_bytes) # self.last_data_transfer_bytearray()
        mesured_value_byterray = data_transfer_bytearray[4:13] # ditto
        return float(mesured_value_byterray)

    def disconnect(self):
        """close the instrument communication"""
        self.serial.close()