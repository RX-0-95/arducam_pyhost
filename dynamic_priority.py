import queue
import time
from typing import Deque,List
class DynamicTask:
    def __init__(self,max_priority=3,max_queue=20) -> None:
        self.last_process_time = time.time()
        self.max_priority = max_priority
        self.priority = 1
        self.max_queue_size = max_queue
        self.data_queue = queue.Queue(max_queue)
    
    def increase_priority(self):
        if self.priority !=3:
            self.priority += 1 
    
    def set_priority(self,priority):
        if priority > self.max_priority or priority < 1:
            assert True, "Invalid priority setting\n"
        else:
            self.priority = priority
    # Camera only allow to increase the priority
    def cam_set_priority(self,priority):
        if priority > self.priority:
            self.priority = priority

    def insert_data(self,data):
        self.data_queue.put(data)
    
    def get_data(self):
        self.last_process_time = time.time()
        if self.data_queue:
            return self.data_queue.get()
        else:
            return None

class DynamicPriorityScheduler:
    def __init__(self) -> None:
        self.taks_list:List[DynamicTask] = []
        self.task_wait_time = 3*10**6; #us 
    def add_task(self,task:DynamicTask):
        self.taks_list.append(task)

    def get_image(self):
        h_task = self.get_highest_priority()
        if h_task is not None:
            return h_task.get_data()
        else:
            return None

    def change_priority(self,taks_idx,priority_level):
        None

    def get_highest_priority(self):
        current_time = time.time()
        highest_priority_task = None 
        for task in self.taks_list:
            if (current_time-task.last_process_time) > self.task_wait_time:
                # increase priority if exceed max wait time
                task.increase_priority()
            if highest_priority_task is None:
                highest_priority_task = task
            else:
                if task.priority > highest_priority_task.priority:
                    highest_priority_task = task
                elif task.priority == highest_priority_task.priority:
                    if task.last_process_time < highest_priority_task.last_process_time:
                        highest_priority_task = task
        return highest_priority_task
        
