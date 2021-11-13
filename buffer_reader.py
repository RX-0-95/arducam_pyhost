"""
Extablish usart communcation to host camear module,
read JPEG buffer and show the image
"""
import io
from typing import Dict, List
from abc import ABC
from PIL import Image
import config_yaml
import serial

class BufferProvider(ABC):
    def __init__(self,word_size:int=8) -> None:
        self.word_size = word_size
    def open(self):
        """open buffer port
        """
        pass 
    def read(self,num:int):
        pass
    def readline(self):
        pass 
    def flush(self):
        pass 
class SerialBufferProvider(BufferProvider):
    def __init__(self,port:str,baudrate:int=921600,
                stopbits:int=1,parity:str='N',
                word_size:int=8) -> None:
        super().__init__(word_size=word_size)
        # init serial
        self.ser = serial.Serial(
                        port = port,
                        baudrate=baudrate,
                        stopbits = stopbits,
                        parity = parity)

    def open(self):
        if self.ser.isOpen:
            return
        self.ser.open()
        assert self.ser.is_open, \
            "Fail to open serial port {}".format(self.ser.port)
    
    def read(self,num: int):
        return self.ser.read(num)
    
    def readline(self):
        return self.ser.readline()
    
    def flush(self):
        self.ser.flushInput()
        self.ser.flushOutput()
    
        

class BufferReader:
    def __init__(self,buffer_provider:BufferProvider,
                start_code:List[int],end_code:List[int]) -> None:
        self.buffer_provider = buffer_provider
        self.start_code = start_code
        self.end_code = end_code
        self.buf = []
        
    def start(self):
        # start the buffer provider 
        self.buffer_provider.open()
        prev_buf = ''
        while True:
            cur_buf = self.buffer_provider.read(1)
            if cur_buf:
                if prev_buf == b'\xff' and cur_buf == b'\xd9':
                    self.buf.append(cur_buf)
                    self.plot_image_from_buffer()
                    self.buf.clear()
                    self.buffer_provider.flush()
                else:
                    self.buf.append(cur_buf)
                prev_buf = cur_buf

    def plot_image_from_buffer(self):
        buf = b''.join(self.buf)
        print(buf)
        picture = Image.open(io.BytesIO(buf))
        picture.show()


if __name__ == "__main__":
    config_file_path = 'config.yaml'
    config = config_yaml.get_config(config_file_path)
    data_tras_config = config['DATA_TRANSFER']
    image_config = config['IMAGE']
    buffer_provider = SerialBufferProvider(
                            port=data_tras_config['PORT'],
                            baudrate=data_tras_config['BAUD'],
                            stopbits=data_tras_config['STOPBITS'],
                            parity=data_tras_config['PARITY']
                            )
    buffer_reader = BufferReader(buffer_provider,
                                start_code=image_config['START_CODE'],
                                end_code=image_config['END_CODE'])
    buffer_reader.start()
