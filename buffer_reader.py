"""
Extablish usart communcation to host camear module,
read JPEG buffer and show the image
"""
import io
from os import getlogin
from typing import Dict, List, overload
import abc
#from PIL import Image
from PyQt5 import QtCore as qtc
from cv2 import CAP_GSTREAMER, calibrateCamera
import numpy as np
from numpy.lib.function_base import copy
from torch.functional import cartesian_prod
import config_yaml
import serial

import sys
import glob
import typing
from enum import Enum



class ImageFormat(Enum):
    JPEG = 1
    GREY = 2
    YUV = 3

class CamPriority(Enum):
    P1 = 1
    P2 = 2
    P3 = 3

CamPriorityCode= {
    "p1":b"\x10",
    "p2":b"\x20",
    "p3":b"\x30",
}




def GetFormat(format:str):
    if format == 'JPEG':
        return ImageFormat.JPEG
    if format == 'GREY':
        return ImageFormat.GREY
    if format == 'YUV':
        return ImageFormat.YUV
    raise NotImplementedError("Not support image format {}".format(format))

class BufferProvider(abc.ABC):
    def __init__(self,word_size:int=8) -> None:
        self.word_size = word_size
       
    @abc.abstractmethod
    def open(self):
        """open buffer port
        """
        pass 
    @abc.abstractmethod
    def is_open(self):
        """return true if the port
            is connect
        """
        return False
    @abc.abstractmethod
    def close(self):
        """close the port
        """
        pass
    @abc.abstractmethod
    def read(self,num:int):
        pass
    @abc.abstractmethod
    def cancel_read(self):
        pass 
    @abc.abstractmethod
    def set_port(self,port:str):
        pass
    @abc.abstractmethod
    def get_port(self):
        pass
    @abc.abstractmethod
    def readline(self):
        pass 

    @abc.abstractmethod
    def flush(self):
        pass
    @abc.abstractmethod
    def get_available_ports(self):
        pass

class SerialBufferProvider(BufferProvider):
    def __init__(self,port:str,baudrate:int=921600,
                stopbits:int=1,parity:str='N',
                word_size:int=8) -> None:
        super().__init__(word_size=word_size)
        # init serial
        self.ser = serial.Serial()
        self.ser.stopbits = stopbits
        self.ser.baudrate = baudrate
        self.ser.parity = parity
        self.ser.port = port
    
    def get_available_ports(self):
        return self.serial_ports()

    def serial_ports(self):
        """Lists serial port names
            :returns:
                A list of the serial ports available on the system
        """
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            print("===> MacOs platform detect")
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')
        
        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except(OSError,serial.SerialException):
                pass 
        return result

    def set_port(self, port: str):
        self.ser.port = port 
    def get_port(self):
        return self.ser.port
    def open(self):
        if self.ser.isOpen():
            print('===> Port {} already open'.format(self.ser.port))
            return
        self.ser.open()
        print('===> Open port: {}'.format(self.ser.port))
        assert self.ser.is_open, \
            "Fail to open serial port {}".format(self.ser.port)
    def is_open(self):
        return self.ser.isOpen()
    def close(self):
        if self.ser.isOpen():
            self.ser.close()
        else:
            return
    
    def set_port(self,port:str):
        self.ser.close()
        self.ser.setPort(port)
    
    def read(self,num: int):
        return self.ser.read(num)
    
    def cancel_read(self):
        return self.ser.cancel_read()
    
    def readline(self):
        return self.ser.readline()
    
    def flush(self):
        self.ser.flushInput()
        self.ser.flushOutput()
    
class BufferReader(qtc.QThread):
    buffer_read_sgn = qtc.pyqtSignal(ImageFormat,bytes)
    cam_priorty_sgn = qtc.pyqtSignal(CamPriority)
    #buffer_format_sgn = qtc.pyqtSignal(str)
    
    def __init__(self,buffer_provider:BufferProvider,image_format:ImageFormat,
                start_code:List[int],end_code:List[int]) -> None:
        super().__init__()
        self.buffer_provider = buffer_provider
        self.is_running = False
        self.image_format = image_format
        self.start_code = start_code
        self.end_code = end_code
        self.buf = []
        self.send_buf = b''
        print("Create Buffer reader with format :{}".format(self.image_format))
        
    def run(self):
        # start the buffer provider 
        self.buffer_provider.open()
        prev_buf = ''
        in_recieve_img = False
        while self.is_running:
            cur_buf = self.buffer_provider.read(1)
            if cur_buf:
                if not in_recieve_img:
                    if prev_buf == b'\xaa' and cur_buf == b'\xff':
                        priority = self.buffer_provider.read(1)
                        if priority == CamPriorityCode["p1"]:
                            self.cam_priorty_sgn.emit(CamPriority.P1)
                        elif priority == CamPriorityCode["p2"]:
                            print("===> Detect Motion\n")
                            self.cam_priorty_sgn.emit(CamPriority.P2)
                        elif priority == CamPriorityCode["p3"]:
                            print('===> Person detected\n')
                            self.cam_priorty_sgn.emit(CamPriority.P3)
                # Extract image data from buffer
                if self.image_format == ImageFormat.JPEG:
                    if prev_buf == b'\xff' and cur_buf == b'\xd9': #detected end bytes JPEG
                        self.buf.append(cur_buf)
                        self.send_buf = b''.join(self.buf)
                        self.buffer_read_sgn.emit(ImageFormat.JPEG,self.send_buf)
                        self.buf.clear()
                        self.buffer_provider.flush()
                    if prev_buf == b'\xff' and cur_buf == b'\xd8':#detected start bytes JPEG
                        self.buf.clear()
                        self.buf.append(b'\xff')
                        self.buf.append(b'\xd8')
                    else:
                        self.buf.append(cur_buf)
                elif self.image_format == ImageFormat.GREY:
                    if prev_buf == b'\x55' and cur_buf == b'\xAA': # detect start bytes GREY
                        #print("Detect RGB!!!\n")
                        grey_buf = self.buffer_provider.read(96*96*1)
                        #self.send_buf = b''.join(grey_buf)
                        self.send_buf = grey_buf
                        self.buffer_read_sgn.emit(ImageFormat.GREY,self.send_buf)
                        self.buf.clear()
                        #self.buffer_provider.flush()
                elif self.image_format == ImageFormat.YUV:
                    if prev_buf == b'\x55' and cur_buf == b'\xAF': #detect start bytes YUV
                        #print('===> Recieve YUV buffer\n')
                        yuv_buf = self.buffer_provider.read(96*96*2)
                        self.send_buf = yuv_buf
                        self.buffer_read_sgn.emit(ImageFormat.YUV,self.send_buf)
                        self.buf.clear()
                else:
                    raise NotImplementedError("Not support image format:{}".format(self.image_format))
                    
                prev_buf = cur_buf
        
        print('===>Close buffer provider')
        self.buffer_provider.flush()
        self.buffer_provider.close()
        #self.buffer_provider.cancel_read()
    #TODO: close the buffer provide when stop the thread
    def set_running(self,b:bool):
        self.is_running = b
    """
    def plot_image_from_buffer(self):
        buf = b''.join(self.buf)
        print(buf)
        picture = Image.open(io.BytesIO(buf))
        picture.show()
    """
if __name__ == "__main__":
    print(type(ImageFormat.GREY))