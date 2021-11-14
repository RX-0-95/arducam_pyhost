from os import error
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc

import sys 
from typing import Dict, List

import serial

from viewer import main_window
import buffer_reader as br
from config_yaml import get_config

class HostWindow():
    def __init__(self,config:Dict) -> None:
        self.config = config
        com_config = self.config['DATA_TRANSFER']
        image_config = self.config['IMAGE']
        self.is_connected = False
        #init buffer provider
        com_type = com_config['TYPE']
        if com_type == 'USART':
            self.buffer_provider = br.SerialBufferProvider(
                                    port=com_config['PORT'],
                                    baudrate=com_config['BAUD'],
                                    stopbits=com_config['STOPBITS'],
                                    parity=com_config['PARITY']
                                    )
        else:
            raise NotImplementedError('Not support {} \
                communication type!!!'.format(com_type))
        
        #init buffer reader
        self.buffer_reader = br.BufferReader(self.buffer_provider,
                                        start_code=image_config['START_CODE'],
                                        end_code=image_config['END_CODE']) 
        #init main window UI
        self.main_window = main_window.MainWindow("Host Window")
        
        #change main window UI based when needed
        self.update_com_list()

        #connect UI to function
        self.connect_ui_function()

        self.main_window.show()

    def connect_ui_function(self):
        #udpate ports combobox when click combobox
        self.main_window.com_box.before_popup.connect(self.update_com_list)
        # connect button\
        self.main_window.com_connect_btn.clicked.connect(self.on_connect_click)
   
    def update_com_list(self):
        """refreshs the combobox for avaliable communcation ports
        """
        com_list = self.buffer_provider.get_available_ports()
        self.main_window.com_box.clear()       
        self.main_window.com_box.addItems(com_list)
    
    def _com_connect_open(self):
        #change the port to current port on combobox
        cur_port = self.main_window.com_box.currentText()
        try:
            self.buffer_provider.set_port(cur_port)
            self.buffer_provider.open()
            print('===> Connect to port :{}'.format(self.buffer_provider.get_port()))
            self.is_connected = True
            self.main_window.com_box.setDisabled(True)
            self.main_window.com_connect_btn.setText('Disconnect')
        except serial.SerialException as e:
            #TODO:print connect faild somewhere
            self.is_connected = False
            print('Error happen during connectiong: error msg:{}'.format(e))
    
    def _com_connect_close(self):
        self.buffer_provider.close()
        print('===> Disconnect to port :{}'.format(self.buffer_provider.get_port()))

        self.is_connected = False
        self.main_window.com_box.setDisabled(False)
        self.main_window.com_connect_btn.setText('Connect')
    
    def on_connect_click(self):
        if self.is_connected:
            self._com_connect_close()
        else:
            self._com_connect_open()

    

    def on_exit(self):
        """TODO: disconnect the com connection
        """
        None 
    

if __name__ == "__main__":
    qtw.QApplication.setAttribute(qtc.Qt.AA_EnableHighDpiScaling)
    qtc.QCoreApplication.setAttribute(qtc.Qt.AA_UseHighDpiPixmaps)
    app = qtw.QApplication(sys.argv)
    config_path = "config.yaml"
    config = get_config(config_path)
    hw = HostWindow(config)
    sys.exit(app.exec())