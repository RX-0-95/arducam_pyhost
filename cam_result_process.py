from os import terminal_size
from typing_extensions import Literal


def read_cam_result(cam_result_file):
    time_list = []
    res_list = []
    with open(cam_result_file) as f:
        lines = f.readlines()
        for line in lines:
            cur_time,res = line.split(" ")
            cur_time = float(cur_time)
            res = float(res)
            #print("{} {}".format(cur_time,res))
            if res == 3:
                time_list.append(cur_time)
                res_list.append(res)
    return time_list,res_list


def read_host_result(host_result_file):
    time_list = []
    res_list = []
    with open(host_result_file) as f:
        lines = f.readlines()
        for line in lines:
            #print(line)
            cur_time,res = line.split(" ")
            #cur_time,res = lines.split(" ")
            cur_time = float(cur_time)
            res = float(res)
            time_list.append(cur_time)
            res_list.append(res)
    return time_list,res_list



def get_acc_list(truth_list,cam_list,cam_detect_time=1200):
    detected_list = []
    not_detected_list = []
    for c_time in cam_list:
        c_lower = c_time - cam_detect_time
        c_upper = c_time + cam_detect_time
        find_in_true = False
        while (1):
            if len(truth_list) == 0:
                break
            t_time = truth_list[0]
            if t_time < c_lower: 
                not_detected_list.append(truth_list.pop(0))
                #not_detected_list.append(c_time)
                #break
            elif t_time > c_upper:
                #not_detected_list.append(c_time)
                break
            else:
                find_in_true = True
                find_time = truth_list.pop(0)
        #if not find_in_true:
        #    negative_true_list.append(c_time)
        if find_in_true:
            detected_list.append(find_time)
        
    not_detected_list.extend(truth_list)
    return detected_list, not_detected_list

def get_total_detected_time(t_list,effective_threshold=1200):
    _t_list = t_list.copy()
    total_detect_time = 0
    #total_time = _t_list
    if _t_list:
        prev_time = _t_list.pop(0)
    else:
        return total_detect_time

    while len(_t_list) != 0:
        cur_time = _t_list.pop(0)
        if (prev_time+effective_threshold) < cur_time:
            total_detect_time += effective_threshold
        else:
            total_detect_time += cur_time - prev_time
        prev_time = cur_time
    return total_detect_time

if __name__ == "__main__":
    detect_effective_time = 120 #ms
    cam_result_file = "output/save/cam.txt"
    host_result_file = "output/save/host.txt"
    cam_list,_ = read_cam_result(cam_result_file)
    host_list,_ = read_host_result(host_result_file)
    true_positive1, false_positive = get_acc_list(host_list.copy(),cam_list.copy())

    true_positive2, false_negative = get_acc_list(cam_list.copy(),host_list.copy())

    true_positive_time = get_total_detected_time(true_positive1) + get_total_detected_time(true_positive2)
    true_positive_time /= 2 
    false_negative_time = get_total_detected_time(false_negative)
    false_positive_time = get_total_detected_time(false_positive)

    total_time = host_list[-1]-host_list[0]
    total_positive_time = true_positive_time + false_negative_time 
    total_negative_time = total_time - total_positive_time 
    precision = true_positive_time/(true_positive_time+false_positive_time)
    recall = true_positive_time/total_positive_time

    print("Total mointor time :{}, True positive: {}, \
        False Positive: {}, Precision: {}, Recall {}" \
            .format(total_time,true_positive_time,false_positive_time,
            precision,recall))
    
    print(false_negative_time)
    

    l1, l2 = get_acc_list(host_list.copy(),host_list.copy())

    print(l1)
    print(l2)
