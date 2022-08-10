#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   main.py
@Time    :   2022/06/21 22:27:16
@Author  :   QuYue 
@Email   :   quyue1541@gmail.com
@Desc    :   main
'''

# %% Import Package
# Basic
import os
import torch
import numpy as np
import time
import datetime
import matplotlib.pyplot as plt

# Add path
os.chdir(os.path.dirname(__file__))

# Self-defined
import utils
import dataprocessor as dp
import modeler as ml
import recorder as rd

# %% Set Super-parameters
class MyParam(utils.parameter.PARAM):
    def __init__(self) -> None:
        # Random seed
        self.seed = 1       # Random seed
        # Device
        self.gpu = 0        # Used GPU, when bool (if use GPU), when int (the ID of GPU) 
        # Dataset
        self.dataset_name = "Synthetic"     # Dataset name
        self.train_valid_test = [4, 1, 1]   # The ratio of training, validation and test data
        self.cv = 1                         # Fold number for cross-validation
        # Dataset Parameters
        self.dataset_set = {"synthetic":
                                {"name": "Synthetic",
                                 "data_number": 10000,
                                 "data_dimensions": 10,
                                 "ifprint": False,
                                 "stratify": 't',
                                 "keylist": ['x', 't', 'y', 'potential_y'],
                                 "typelist": [['float', 'gpu'], ['long', 'gpu'], ['float', 'gpu'], ['float', 'gpu']]}}
        # Model
        self.model_name_list = ["s_learner", "t_learner"]   # Model name list
        self.model_name_list = ["s_learner"]   # Model name list
        self.model_save = True                 # Whether to save the model
        # Model Parameters
        self.model_param_set = {"s_learner":
                                    {"name": "S_Learner", 
                                     "input_size": self.dataset_set[self.dataset_name.lower().strip()]["data_dimensions"],
                                     "output_size": 1,
                                     "hidden_size": 15,
                                     "layer_number": 3,
                                     "optimizer": {"name": "Adam", "lr": 0.001}},
                                "t_learner":
                                    {"name": "T_Learner",
                                     "input_size":self.dataset_set[self.dataset_name.lower().strip()]["data_dimensions"],
                                     "output_size":1,
                                     "hidden_size":15,
                                     "layer_number":3}}
        # Training
        self.epochs = 1000            # Epochs
        self.batch_size = 1000      # Batch size
        self.learn_rate = 0.01      # Learning rate
        self.test_epoch = 1         # Test once every few epochs
        # Records
        self.ifrecord = False                # If record
        self.now = datetime.datetime.now()  # Current time
        self.recorder = None                # Recorder (initialization)
        self.save_path = f"../../Results/Experiments_1/{self.now.strftime('%Y-%m-%d_%H-%M-%S')}"
        # Checkpoints
        self.ifcheckpoint = True            # If checkpoint
        # Setting
        self.setting()

Parm = MyParam()



# %% Main Function
if __name__ == "__main__":
    print("Loading dataset ...")
    dataset = dp.datasets.load_dataset(Parm.dataset_name, seed=Parm.seed, **Parm.dataset.dict)
    print("Start training ...")
    Parm.recorder = rd.Recorder_nones([dataset.cv, Parm.epochs])
    for cv in range(dataset.cv):
        Parm.model_setting()        # Models initialization
        Parm.model_device_setting() # Models device setting
        print(f"Cross Validation {cv}: {datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}")
        train_loader, test_loader = dp.process.dataloader(dataset[cv], batch_size=Parm.batch_size, **Parm.dataset.dict)
        for epoch in range(Parm.epochs):
            print(f"Epoch {epoch}: {datetime.datetime .now().strftime('%Y-%m-%d_%H:%M:%S')}")
            record = rd.Record(index=epoch)
            # Training
            ml.train(Parm.model_list) # Train model
            for batch_idx, data in enumerate(train_loader):
                data = [data.to(Parm.device) for data in data]
                data = dict(zip(Parm.dataset.keylist, data))
                batchrecord = rd.BatchRecord(size=data['x'].shape[0], index=batch_idx) 
                batchrecord['train_loss'] = []
                # Model
                pred_list = []
                for model in Parm.model_list:
                    loss = model.on_train(data)
                    batchrecord['train_loss'].append(loss.item() * data['x'].shape[0])
                record.add_batch(batchrecord)
            record.aggregate({'train_loss': 'mean_size'})
            record['time'] = time.time()
            str = record.print_all_str()
            print(str)

            # Testing
            ml.eval(Parm.model_list) # Testing model
            for batch_idx, data in enumerate(test_loader):
                data = [data.to(Parm.device) for data in data]
                data = dict(zip(Parm.dataset.keylist, data))
            Parm.recorder[cv, epoch] = record
        # Parm.save(f"cv{cv}.json")
    
    print("Finish training ...\n")
    if Parm.ifrecord:
        Parm.save("final.json")
        print("Records saved.")
    print("Done!")

# %%
plt.plot(Parm.recorder.query('train_loss')[0])