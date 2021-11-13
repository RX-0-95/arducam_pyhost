import serial
from PIL import Image
import io 
#Serial Config
usart_baudarde = 921600
#port = "COM3"
port = "COM5"

byte_size = 8
parity = 'N'
stop_bits = 1

# Init serial
ser = serial.Serial()
ser.baudrate = usart_baudarde
ser.port = port
ser.stopbits = stop_bits
ser.parity = parity

ser.open()

#def serial_recieve(ser):
#    buffer = ''
#        buffer += ser.read(ser.inW)
buf = []
prev_buf = ''

while True:
    cur_buf = ser.read(1)
    if prev_buf == b'\xff' and cur_buf == b'\xd9':
        buf.append(cur_buf)
        break
    else:
        buf.append(cur_buf)
    prev_buf = cur_buf

"""
while True:
    cur_buf = ser.read(1)
    print(cur_buf)
"""
buf = b''.join(buf)
print(buf)
picture = Image.open(io.BytesIO(buf))
picture.show()