import numpy as np
import io
import cv2 
import PIL
def YUV422Buffer_to_RGB888_ndarray(yuv:bytearray,yuv_w:int,yuv_h:int)->np.ndarray:
    #rgb = np.zeros(shape=(yuv_w,yuv_h,3))
    yuv_buf = np.frombuffer(yuv,dtype=np.uint8)
    y_mask = np.arange(start=0,stop=len(yuv_buf),step=2)
    u_mask = np.arange(start=1,stop=len(yuv_buf),step=4)
    v_mask = np.arange(start=2,stop=len(yuv_buf),step=4)
    #check the size
    assert len(u_mask)==len(v_mask), "Length of u and v should be same\n"
    assert len(y_mask)/2 == len(v_mask), "Length of y is not compatable with u and v\n"
    
    y = np.reshape(yuv_buf[y_mask].copy(),(yuv_w,yuv_h))
    u = yuv_buf[u_mask].copy()
    v = yuv_buf[v_mask].copy()
    u = np.reshape(np.repeat(u,2),(yuv_w,yuv_h))
    #print(u)
    v = np.reshape(np.repeat(v,2),(yuv_w,yuv_h))
    #yuv444 = np.dstack((y,u,v)).astype(np.float64)
    """
    m = np.array([
        [1.000,  1.000, 1.000],
        [0.000, -0.39465, 2.03211],
        [1.13983, -0.58060, 0.000],
    ])
    """
    #yuv_data = np.frombuffer(yuv,np.uint8).reshape(96*2,96)
    #brg = cv2.cvtColor(yuv_data,cv2.COLOR_YUV2RGBA_YUYV)
    #u = u.reshape((96//2,96//2))
    #v = v.reshape((96//2,96//2))
    #u = cv2.resize(u,(96,96))
    #v = cv2.resize(v,(96,96))
    yvu = cv2.merge((y,v,u))
    bgr = cv2.cvtColor(yvu,cv2.COLOR_YCrCb2BGR)
    rgb = cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB)
    
    #cv2.imshow("rgb",rgb)
    #rt = np.asarray(brg)
    """
    yuv444[:,:,1:] -= 128
    rgb = np.dot(yuv444,m)
    #print(rgb)
    rgb = rgb.clip(0,255)
    """
    #return rgb.astype(np.uint8)
    #return rgb
    return np.asarray(rgb,dtype=np.uint8)