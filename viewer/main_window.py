from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
import typing
import numpy as np

import sys

class ClickRefreshComboBox(qtw.QComboBox):
    before_popup = qtc.pyqtSignal()
    def __init__(self, parent: typing.Optional[qtw.QWidget] = ...) -> None:
        super().__init__(parent=parent)
   
    def showPopup(self) -> None:
        self.before_popup.emit()
        return super().showPopup()

class MainWindow(qtw.QMainWindow):
    def __init__(self,window_name:str='window') -> None:
        super(MainWindow,self).__init__()
        self.window_name = window_name
        self.image_view = None
        self.image_scene = None

        self.main_layout = None
        self.tools_layout = None
        self.com_btn = None
        self.com_connect_btn = None

        self.init_ui()
        self.show()
    
    def init_ui(self):
        self.setWindowTitle(self.window_name)
        self.resize(1000,800)
    
        self.image_scene = qtw.QGraphicsScene()
        self.image_view = qtw.QGraphicsView(self.image_scene)

        self.main_layout = qtw.QGridLayout()
        self.main_layout.addWidget(self.image_view,0,0,12,1)

        ###################Tools####################
        
        # communicaton port button
        self.tools_layout = qtw.QGridLayout()

        self.com_box = ClickRefreshComboBox(self)
        self.tools_layout.addWidget(self.com_box,0,0,qtc.Qt.AlignCenter)

        self.com_connect_btn = qtw.QPushButton(self)
        self.com_connect_btn.setText('Connect')
        self.tools_layout.addWidget(self.com_connect_btn,0,1,qtc.Qt.AlignCenter)

        self.main_layout.addLayout(self.tools_layout,12,0,1,1)

        widget = qtw.QWidget(self)
        widget.setLayout(self.main_layout)
        self.setCentralWidget(widget)
    
    def udpate_frame(self,data:np.ndarray):
        ## TODO: add multithread support in read data
        image = qtg.QPixmap(data,
                            data.shape[0],
                            data.shape[0],
                            qtg.QImage.Format_RGB32)
        self.image_scene.clear()
        self.image_scene.addPixmap(image)
        self.image_scene.update()
        self.image_view.setSceneRect(image.rect())

    def update_frame_from_data(self,data):
        qp = qtg.QPixmap()
        qp.loadFromData(data)
        qp = qp.scaledToWidth(self.image_view.width())
        self.image_scene.clear()
        self.image_scene.addPixmap(qp)
        self.image_scene.update()
        self.image_view.setSceneRect(qtc.QRectF(qp.rect()))

if __name__ == "__main__":
    qtw.QApplication.setAttribute(qtc.Qt.AA_EnableHighDpiScaling)
    qtc.QCoreApplication.setAttribute(qtc.Qt.AA_UseHighDpiPixmaps)
    app = qtw.QApplication(sys.argv)

    mw = MainWindow()
    sys.exit(app.exec())