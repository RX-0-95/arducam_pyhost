import matplotlib.pyplot as plt
import numpy as np
def get_fps_list(fps_file):
    f = open(fps_file)
    lines = f.readlines()
    fps_list = []
    for line in lines:
        fps_list.append(float(line))
    return fps_list 


if __name__ == "__main__":
    rtos_fps_file = "output/RTOS_fps.txt"
    baremetal_fps_file = "output/baremetal_fps.txt"
    rtos_list = get_fps_list(rtos_fps_file)
    baremetal_list = get_fps_list(baremetal_fps_file)
    plot_len = len(baremetal_list)
    if len(rtos_list) < len(baremetal_fps_file):
        plot_len = len(rtos_list)
    #print(plot_len)
    x = np.arange(plot_len)
    print(len(x))
    baremetal_y = baremetal_list[0:plot_len]
    rtos_y = rtos_list[400:400+plot_len]

    fig,(ax1,ax2) = plt.subplots(1,2)
    fig.suptitle("Baremetal vs RTOS FPS")
    ax1.plot(x,baremetal_y)
    ax1.set_ylabel("FPS")
    ax1.set_xlabel("Baremetal")

    ax2.plot(x,rtos_y)
    ax2.set_ylabel("FPS")
    ax2.set_xlabel("RTOS")
    plt.show()
