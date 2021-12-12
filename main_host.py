import os
from time import time 
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5.QtGui import QPixmap
import numpy as np 

import sys 
from typing import Dict, List

import serial
from dynamic_priority import DynamicPriorityScheduler, DynamicTask

from viewer import main_window 
import buffer_reader as br
from config_yaml import get_config
import format_converter as fc

from person_detection import person_detector

class HostWindow():
    def __init__(self,config:Dict) -> None:
        self.config = config
        com_config = self.config['DATA_TRANSFER']
        image_config = self.config['IMAGE']
        model_cfg = self.config['NEURAL_NETWORK']
        self.is_connected = False
        self.show_buffer_mode = False
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
                                        image_format=br.GetFormat(image_config['FORMAT']),
                                        start_code=image_config['START_CODE'],
                                        end_code=image_config['END_CODE']) 
        #init main window UI
        self.main_window = main_window.MainWindow("Host Window")
        
        #change main window UI based when needed
        self.update_com_list()

        #connect UI to function
        self.connect_ui_function()

        #set up person detector
        self.person_detector = person_detector(img_res=model_cfg['IMG_RES'],
                                                model_cfg_path=model_cfg['MODEL_CFG_PATH'],
                                                model_weight_path=model_cfg['MODLE_WEIGHT_PATH'],
                                                classes_path=model_cfg['COCO_CLASSES']) 

        #setup performance mointer
        self.output_dir = 'output'
        self.cam_out_file = os.path.join(self.output_dir,"cam.txt")
        self.host_out_file = os.path.join(self.output_dir,"host.txt")
        self.fps_out_file = os.path.join(self.output_dir,"fps.txt")

        self.prev_frame_time = 0
        #self.fps_file = open(self.fps_out_file,'a+')
        self.cam_result = []
        self.host_result = []
        self.time_diff_threshold = 25 #25 ms 

        # dynamic queue system
        self.priority_scheduler = DynamicPriorityScheduler()
        self.cam_task1 = DynamicTask(max_priority=3,max_queue=20)
        self.priority_scheduler.add_task(self.cam_task1)

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
            # connect the update frame to buffer reader
            self.buffer_reader.buffer_read_sgn.connect(self.update_frame)
            self.buffer_reader.cam_priorty_sgn.connect(self.record_cam_result)

            print('===>Connect update frame function to buffer reader')
            print('===>Start buffer reader run')
            self.buffer_reader.set_running(True)
            self.buffer_reader.start()
        except serial.SerialException as e:
            #TODO:print connect faild somewhere
            self.is_connected = False
            print('Error happen during connectiong: error msg:{}'.format(e))
    
    def _com_connect_close(self):
        
        print('===> Disconnect to port :{}'.format(self.buffer_provider.get_port()))
        self.is_connected = False
        self.main_window.com_box.setDisabled(False)
        self.main_window.com_connect_btn.setText('Connect')
        self.buffer_reader.set_running(False)
        self.buffer_reader.buffer_read_sgn.disconnect(self.update_frame)
        print('===>Disconnect update frame function to buffer reader')

    def on_connect_click(self):
        if self.is_connected:
            self._com_connect_close()
        else:
            self._com_connect_open()

    def on_exit(self):
        """TODO: disconnect the com connection
        """
        None 
    
    #############This function will be move to anther thread############
    def update_frame(self,format,data):
        # compute fps 
        
        if self.prev_frame_time == 0:
            self.prev_frame_time = time()
        else:
            f = open(self.fps_out_file,"a+")
            refresh_time = time() - self.prev_frame_time
            self.prev_frame_time = time()
            fps = 1/refresh_time
            f.write("{}\n".format(fps))
            f.close()
        
        current_frame_data = data
        if format == br.ImageFormat.GREY:
            #print("GREY \n")
            self.main_window.update_frame_from_greyscale(current_frame_data)
        elif format == br.ImageFormat.JPEG:
            #print("JPEG \n")
            self.main_window.update_frame_from_jpeg(current_frame_data)
        elif format == br.ImageFormat.YUV:
            #print("YUV\n")
            rgb = fc.YUV422Buffer_to_RGB888_ndarray(current_frame_data,96,96)
            self.cam_task1.insert_data(rgb)
            # get the priority task from the task scheduler
            priority_task = self.priority_scheduler.get_highest_priority()
            if priority_task is not None:
                p_rgb = priority_task.get_data()
                p_rgb,detec_person_flag = self.person_detector.detect_and_draw_box(rgb)
                if detec_person_flag:
                    # detect person keep the priority
                    self.record_host_result()
                else:
                    # no person, decrease priority
                    priority_task.set_priority(1)
                self.main_window.update_from_ndarray(rgb)
        else:
            raise NotImplementedError("Unsuppored data format!!!\n")

    def record_cam_result(self,priority):
        cam_file = open(self.cam_out_file,'a+')
        if priority == br.CamPriority.P1:
            p = 1
        elif priority == br.CamPriority.P2:
            p = 2
        elif priority == br.CamPriority.P3:
            p = 3
        else:
            raise NotImplementedError
        self.cam_task1.cam_set_priority(p)
        cam_file.write("{:3f} {}\n".format(time()*1000,p))
        cam_file.close()

    def record_host_result(self):
        host_file = open(self.host_out_file,'a+')
        host_file.write("{:3f} {}\n".format(time()*1000, 1))
        host_file.close()
    


if __name__ == "__main__":

    qtw.QApplication.setAttribute(qtc.Qt.AA_EnableHighDpiScaling)
    qtc.QCoreApplication.setAttribute(qtc.Qt.AA_UseHighDpiPixmaps)
    app = qtw.QApplication(sys.argv)
    config_path = "config.yaml"
    config = get_config(config_path)
    hw = HostWindow(config)
    sys.exit(app.exec())