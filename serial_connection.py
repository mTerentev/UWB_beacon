import serial

# configure the serial port
ser = serial.Serial('/dev/ttyUSB0', 9600)

# write data to the serial port
ser.write(b'Hello, world!')

# read data from the serial port
data = ser.readline()
print(data)

# close the serial port
ser.close()