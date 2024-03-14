# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/cifar10_dataloading.ipynb.

# %% auto 0
__all__ = ['get_bt_cifar10_train_dls', 'get_supervised_cifar10_train_dls', 'get_supervised_cifar10_test_dls',
           'load_cifar10_train_data', 'load_cifar10_test_data', 'label_func']

# %% ../nbs/cifar10_dataloading.ipynb 3
import torch
from fastai.vision.all import *
import time #for resetting to random state
# from self_supervised.augmentations import *
# from self_supervised.layers import *
import random
from .utils import *

# %% ../nbs/cifar10_dataloading.ipynb 5
def get_bt_cifar10_train_dls(bs, size, device, pct_dataset=1.0, num_workers=12):
    path,fnames_train, labels_train = load_cifar10_train_data(pct_dataset)
    test_eq(len(labels_train), len(fnames_train))
    dls = ImageDataLoaders.from_lists(path, fnames_train, labels_train, bs=bs, item_tfms=[Resize(size=size)],
                                      valid_pct=0.0, num_workers=num_workers, device=device)
    if pct_dataset == 1.0:
        test_eq(len(dls.train), 50000)
    return dls

def get_supervised_cifar10_train_dls(bs, size, device, pct_dataset=1.0, num_workers=12):
    path,fnames_train, labels_train = load_cifar10_train_data(pct_dataset)
    test_eq(len(labels_train), len(fnames_train))
    dls = ImageDataLoaders.from_lists(path, fnames_train, labels_train, bs=bs, item_tfms=[Resize(size=size)],
                                      valid_pct=0.0, num_workers=num_workers, device=device)
    if pct_dataset == 1.0:
        test_eq(len(dls.train_ds), 50000)
    return dls

def get_supervised_cifar10_test_dls(bs, size, device, pct_dataset=1.0, num_workers=12):
    path,fnames_test, labels_test = load_cifar10_test_data(pct_dataset)
    test_eq(len(labels_test), len(fnames_test))
    dls = ImageDataLoaders.from_lists(path, fnames_test, labels_test, bs=bs, item_tfms=[Resize(size=size)],
                                      valid_pct=0.0, num_workers=num_workers, device=device)
    if pct_dataset == 1.0:
        test_eq(len(dls.train_ds), 10000)
    return dls

def load_cifar10_train_data(pct_dataset=1.0):
    path = untar_data(URLs.CIFAR)
    fnames_train = get_image_files(path / "train")
    fnames_train.sort()
    #shuffle data (in reproducible way)
    seed_everything(seed=42)
    fnames_train = fnames_train.shuffle()
    #TODO: test that always orders in same way
    seed_everything(seed=int(time.time())) #reset to (pseudo)-random state
    
    labels_train = [label_func(fname) for fname in fnames_train]
    n = int(len(fnames_train) * pct_dataset)
    fnames_train,labels_train = fnames_train[:n], labels_train[:n]
    if pct_dataset == 1.0:
        test_eq(len(fnames_train), 50000)
    return path, fnames_train, labels_train

def load_cifar10_test_data(pct_dataset=1.0):
    path = untar_data(URLs.CIFAR)
    fnames_test = get_image_files(path / "test")
    labels_test = [label_func(fname) for fname in fnames_test]
    
    # Shuffle the data. Why? So e.g. if we only use 10% of the dataset, we get a random 10%,
    #which should include all classes.
    data = list(zip(fnames_test, labels_test))
    random.shuffle(data)
    fnames_test, labels_test = zip(*data)
    
    n = int(len(fnames_test) * pct_dataset)
    fnames_test, labels_test = fnames_test[:n], labels_test[:n]
    
    if pct_dataset == 1.0:
        test_eq(len(fnames_test), 10000)
    
    return path, fnames_test, labels_test


def label_func(fname):
    return fname.name.split('_')[1].strip('png').strip('.')
