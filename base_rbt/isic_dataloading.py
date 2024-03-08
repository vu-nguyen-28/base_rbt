# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/isic_dataloading.ipynb.

# %% auto 0
__all__ = ['directory', 'process_path', 'extract_id', 'get_class_from_id', 'get_label_func_dict', 'get_difference', 'get_fnames',
           'get_data', 'get_pct_dataset', 'load_data', 'is_colab', 'get_supervised_isic_train_dls',
           'get_supervised_isic_test_dls']

# %% ../nbs/isic_dataloading.ipynb 2
directory = "/content/drive/MyDrive/ISIC_2019_Training_Input/"

# %% ../nbs/isic_dataloading.ipynb 4
import torch
from fastai.vision.all import *
# from self_supervised.augmentations import *
# from self_supervised.layers import *
from .utils import *
import re
import pandas as pd
import os
from collections import Counter

# %% ../nbs/isic_dataloading.ipynb 6
def process_path(name):
    return name.as_posix().split('/')[-1] #basically get end part of Path('...') as a string

def extract_id(string):
    regex = r'ISIC_\d+'
    match = re.search(regex, string)
    if match:
        return match.group(0)
    else:
        return None

def get_class_from_id(string):
    "Given the identifier e.g. ISIC_0000000.jpg return the class label"

    row=data.loc[data['image'] == string]
    lst = [colname for colname in row.columns if row[colname].values==1]
    test_eq(len(lst),1)

    return lst[0]

def get_label_func_dict(_fnames):
    label_func_dict={}
    for name in _fnames:
        label_func_dict[name] = get_class_from_id(extract_id(process_path(name)))

    return label_func_dict


#label_func_dict = get_label_func_dict(_fnames) #can just load this in future to save time
#label_func_dict = data_dict['label_func_dict']

def get_difference(x1, x2):
    return list(set(x1) - set(x2))

#_labels = [label_func(x) for x in _fnames] 
#test_eq(len(_labels),len(_fnames))

# %% ../nbs/cancer_dataloading.ipynb 6
def get_fnames(_fnames,_labels,label_func):

    fnames_train=[]
    labels_train=[]
    count_dict={i:0 for i in set(_labels)}

    fnames = _fnames[0:5000]
    labels = _labels[0:5000]

    for i,lab in enumerate(labels):

        if count_dict[lab]<500:
            fnames_train.append(_fnames[i])
            labels_train.append(_labels[i])

        count_dict[lab]+=1

    fnames_valid = _fnames[5000:5000+256*5]
    labels_valid = _labels[5000:5000+256*5]

    fnames_test = get_difference(_fnames,fnames_train+fnames_valid)
    fnames_test.sort()
    labels_test = [label_func(path) for path in fnames_test]

   
    return {'fnames_train':fnames_train,'fnames_valid':fnames_valid,'fnames_test':fnames_test,
            'labels_train':labels_train,'labels_valid':labels_valid,'labels_test':labels_test
           }

def get_data(load=False):

    data = pd.read_csv("/content/drive/MyDrive/ISIC_2019_Training_GroundTruth.csv").drop("UNK", axis=1)
    data = data[~data["image"].str.contains("downsampled")]
    labels = pd.read_csv("/content/drive/MyDrive/ISIC_2019_Training_GroundTruth.csv")

    if not load:
    #Method 1: load from saved dict in drive
        data_dict = load_dict_from_gdrive(directory='/content/drive/My Drive/cancer_colab',filename='data_dict')
        _fnames = data_dict['_fnames']
        label_func_dict = data_dict['label_func_dict']

    else:
    #Method 2: compute freshly (and I guess we could save for future use)
        _fnames = get_image_files(directory)
        _fnames = [name for name in _fnames if 'downsampled' not in name.as_posix()]
        label_func_dict = get_label_func_dict(_fnames) #can just load this in future to save time

    return _fnames,label_func_dict

def get_pct_dataset(fnames,
            labels,
            pct_dataset=1.0
            ):
    
    N = len(fnames)
    n=int(pct_dataset*N)

    new_labels = labels[0:n]
    new_fnames = fnames[0:n]

    return new_fnames,new_labels


def load_data(load=False):

    global fnames,labels, fnames_train,labels_train, fnames_test,labels_test, label_func
    
    _fnames,label_func_dict = get_data(load=load) #get _fnames, label_func_dict

    # def label_func(name):
    #     return label_func_dict[name]

    def get_label_func(label_func_dict):

        def label_func(name):

            return label_func_dict[name]

        return label_func

    label_func = get_label_func(label_func_dict) #get label_func

    _labels = [label_func(i) for i in _fnames] #get _labels 

    test_eq(process_path(_fnames[0]),'ISIC_0071718.jpg')
    test_eq(process_path(_fnames[10]),'ISIC_0071719.jpg')

    _fnames_dict = get_fnames(_fnames,_labels,label_func)
    fnames_train,fnames_valid,fnames_test = _fnames_dict['fnames_train'],_fnames_dict['fnames_valid'],_fnames_dict['fnames_test']
    labels_train,labels_valid,labels_test = _fnames_dict['labels_train'],_fnames_dict['labels_valid'],_fnames_dict['labels_test']


def is_colab():
    return 'COLAB_GPU' in os.environ

# %% ../nbs/isic_dataloading.ipynb 7
if is_colab():
    load_data() #load fnames_train, fnames_test, label_func etc which are used to build dls. Only want to call if in colab environment

# %% ../nbs/isic_dataloading.ipynb 9
def get_supervised_isic_train_dls(bs, size, device, pct_dataset=1.0, num_workers=12):

    _fnames,_labels = get_pct_dataset(fnames_train,labels_train,pct_dataset=pct_dataset)

    counter = Counter(_labels)
    if pct_dataset == 1.0:
        test_eq(Counter({'NV': 500, 'MEL': 500, 'BCC': 500, 'BKL': 467, 'AK': 306, 'SCC': 171, 'VASC': 55, 'DF': 55}),counter)
    
    elif pct_dataset == 0.1:
        test_eq(Counter({'NV': 83, 'MEL': 68, 'BCC': 49, 'BKL': 24, 'AK': 12, 'SCC': 11, 'DF': 5, 'VASC': 3}),counter)

    elif pct_dataset == 0.01:
        test_eq(Counter({'MEL': 12, 'NV': 6, 'BCC': 4, 'BKL': 1, 'AK': 1, 'SCC': 1}),counter)

    dls=ImageDataLoaders.from_path_func(directory, _fnames, label_func,
                                bs=bs,
                                item_tfms=[Resize(size=size)],
                                valid_pct=0,
                                device=device,
                                num_workers=12*(device=='cuda')
                                             )
    
    if pct_dataset==1.0:
        test_eq(len(dls.train_ds),2554)

    elif pct_dataset==0.1:
        test_eq(len(dls.train_ds),255)

    elif pct_dataset==0.01:
        test_eq(len(dls.train_ds),25)

    
    return dls

def get_supervised_isic_test_dls(bs, size, device, pct_dataset=1.0, num_workers=12):

    _fnames,_labels = get_pct_dataset(fnames_test,labels_test,pct_dataset=pct_dataset)

    counter = Counter(_labels)
    if pct_dataset == 1.0:
        test_eq(Counter({'NV': 10601, 'MEL': 3339, 'BCC': 2549, 'BKL': 1663, 'AK': 498, 'SCC': 414, 'VASC': 186, 'DF': 173}),counter)
    

    dls=ImageDataLoaders.from_path_func(directory, _fnames, label_func,
                                bs=bs,
                                item_tfms=[Resize(size=size)],
                                valid_pct=0,
                                device=device,
                                num_workers=12*(device=='cuda')
                                             )
    
    if pct_dataset==1.0:
        test_eq(len(dls.train_ds),19423)

    
    return dls
