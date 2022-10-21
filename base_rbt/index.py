# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/index.ipynb.

# %% auto 0
__all__ = ['device', 'path', 'items', 'split', 'tds', 'dls']

# %% ../nbs/index.ipynb 7
from .base_model import *
from .base_lf import *

# %% ../nbs/index.ipynb 9
import self_supervised
import torch
from fastai.vision.all import *
from self_supervised.augmentations import *
from self_supervised.layers import *

# %% ../nbs/index.ipynb 10
device='cuda' if torch.cuda.is_available() else 'cpu'

# %% ../nbs/index.ipynb 12
@patch
def lf(self:BarlowTwins, pred,*yb): return 0.01*lf_bt(pred, self.I,self.lmb)

# %% ../nbs/index.ipynb 14
#Get some MNIST data and plonk it into a dls
path = untar_data(URLs.MNIST)
items = get_image_files(path/'training') #i.e. NOT testing!!!
items = items[0:10]
split = RandomSplitter(valid_pct=0.0)
tds = Datasets(items, [PILImageBW.create, [parent_label, Categorize()]], splits=split(items))
dls = tds.dataloaders(bs=2,num_workers=0, after_item=[ToTensor(), IntToFloatTensor()], device=device)



# %% ../nbs/index.ipynb 18
@patch
def lf(self:BarlowTwins, pred,*yb): return lf_rbt(pred,seed=self.seed,I=self.I,lmb=self.lmb)

