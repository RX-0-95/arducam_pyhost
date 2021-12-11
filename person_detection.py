
import torch
from neural_network.pytorchyolo import detect,models
from neural_network.pytorchyolo.utils.utils import load_classes

class person_detector:
    def __init__(self,img_res,model_cfg_path,model_weight_path,classes_path):
        self.img_res = img_res
        self.model_cfg_path = model_cfg_path
        self.model_weight_path = model_weight_path
        self.classes_path = classes_path
        self.model = self._load_model()
        self.classes = load_classes(classes_path)


    def _load_model(self):
        return models.load_model(self.model_cfg_path,self.model_weight_path)

    def detect(self,img):
        """
        :return: confidence, box
        """
        box = detect.detect_image(self.model,image=img,img_size=self.img_res)
        return box
    
    def detect_and_draw_box(self,img):
        box = self.detect(img)
        box = torch.tensor(box)
        rt_img,detect_person_flag = detect.draw_output_image(img,box,self.classes)
        return rt_img,detect_person_flag
