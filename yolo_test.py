
from torch._C import dtype
from utils.function_timer import timer_func

import torch
from torch.serialization import load
from neural_network.pytorchyolo import detect,models
from neural_network.pytorchyolo.utils.utils import load_classes
import os
import cv2

import matplotlib.pyplot as plt 
import numpy as np 
@timer_func
def detect_call(model,img,img_size):
    return detect.detect_image(model,image=img,img_size=img_size)

if __name__ == "__main__":
    yolo_wieght_dir= "neural_network/weights"
    yolo_cfg_dir =  "neural_network/config"
    yolo_data_dir = "neural_network/data"

    yolov3_weight_path = os.path.join(yolo_wieght_dir,"yolov3.weights")
    yolov3_cfg = os.path.join(yolo_cfg_dir,"yolov3.cfg")
    img_path = "neural_network/data/samples/dog.jpg"
    coco_classes = load_classes(os.path.join(yolo_data_dir,"coco.names"))

    model = models.load_model(yolov3_cfg,yolov3_weight_path)
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)

    #box = detect.detect_image(model,image=img,img_size=416)
    box = detect_call(model, img, 128)
    box = torch.tensor(box)
    img = np.asarray(img,dtype=np.uint8)
    #detect._draw_and_save_output_image(img_path,box,416,"output",coco_classes)
    img = detect.draw_output_image(img,box,coco_classes)
    #cv2.imshow('image',img)
    #cv2.waitKey(0)
    plt.imshow(img)
    plt.show()
    print("done")