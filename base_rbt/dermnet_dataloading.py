# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/dermnet_dataloading.ipynb.

# %% auto 0
__all__ = ['label_func', 'get_bt_dermnet_train_dls']

# %% ../nbs/dermnet_dataloading.ipynb 3
import torch
from fastai.vision.all import *
# from self_supervised.augmentations import *
# from self_supervised.layers import *
from .utils import *

# %% ../nbs/dermnet_dataloading.ipynb 4
# Define your label function
# This function should be able to handle paths from both train and test directories correctly
def label_func(x):
    # Example label function, modify it according to your dataset's structure
    return x.parent.name

def get_bt_dermnet_train_dls(bs,size,device,pct_dataset=1.0,num_workers=12):
    #NOTE: assume unzip like: !unzip -q -o "/content/drive/My Drive/dermnet.zip" -d "/content/drive/My Drive/DermNetDataset"

    item_tfms = [Resize(size)]
    
    base_train_dir = "/content/drive/MyDrive/DermNetDataset/train"
    base_test_dir = "/content/drive/MyDrive/DermNetDataset/test"
    fnames_train = get_image_files(base_train_dir)
    fnames_test = get_image_files(base_test_dir)
    fnames = fnames_train + fnames_test #we are doing SSL so we can use all the data

    n = int(len(fnames)*pct_dataset)

    test_eq(len(fnames_train), 15557)
    test_eq(len(fnames_test),4002)
    # Combine the lists
    test_eq(len(fnames),19559)

    # Create the combined DataLoader
    dls = ImageDataLoaders.from_path_func(
        path=".",
        fnames=fnames[0:n],
        label_func=label_func,
        bs=bs,
        item_tfms=item_tfms,
        valid_pct=0,
        device=device,
        num_workers=num_workers*(device=='cuda')
                                          )

    
    
    if pct_dataset == 1.0:
        test_eq(len(dls.train_ds),19559)

    else:
        print('warning: we are not using whole dataset')
        print(f'len(dls.train_ds)={len(dls.train_ds)}')

    return dls



 