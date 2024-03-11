# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/base_supervised.ipynb.

# %% auto 0
__all__ = ['supervised_aug_func_dict', 'get_linear_batch_augs', 'LM', 'LinearBt', 'show_linear_batch', 'get_supervised_dls',
           'get_supervised_cifar10_augmentations', 'get_supervised_isic_augmentations', 'get_supervised_aug_pipelines',
           'encoder_head_splitter', 'SaveSupLearnerModel', 'SupervisedLearning', 'get_encoder', 'load_sup_model',
           'main_sup_train', 'get_supervised_experiment_state', 'main_sup_experiment']

# %% ../nbs/base_supervised.ipynb 3
import importlib
import self_supervised
import torch
from fastai.vision.all import *
from self_supervised.augmentations import *
from self_supervised.layers import *
import kornia.augmentation as korniatfm
import torchvision.transforms as tvtfm
from fastai.learner import load_learner
from .utils import *
from .base_model import get_barlow_twins_aug_pipelines
from .metrics import *

# %% ../nbs/base_supervised.ipynb 5
#Batch level augmentations for linear classifier. At present time, just RandomResizedCrop and Normalization.
def get_linear_batch_augs(size,resize=True,
                    resize_scale=(0.08, 1.0),resize_ratio=(3/4, 4/3),
                    stats=None,cuda=default_device().type == 'cuda',xtra_tfms=[]):
    
    "Input batch augmentations implemented in tv+kornia+fastai"
    tfms = []
    if resize:tfms += [tvtfm.RandomResizedCrop((size, size), scale=resize_scale, ratio=resize_ratio)]
    if stats is not None: tfms += [Normalize.from_stats(*stats, cuda=cuda)]
    tfms += xtra_tfms
    pipe = Pipeline(tfms, split_idx = 0)
    return pipe

# %% ../nbs/base_supervised.ipynb 7
class LM(nn.Module):
    "Basic linear model"
    def __init__(self,encoder,numout,encoder_dimension=2048):
        super().__init__()
        self.encoder=encoder
        self.head=nn.Linear(encoder_dimension,numout)

    def forward(self,x):
        return self.head(self.encoder(x))

# %% ../nbs/base_supervised.ipynb 9
# class LinearBt(Callback):
#     order,run_valid = 9,True
#     def __init__(self,aug_pipelines,n_in, show_batch=False, print_augs=False,data=None):
#         assert_aug_pipelines(aug_pipelines)
#         self.aug1= aug_pipelines[0]
#         self.aug2=Pipeline( split_idx = 0) #empty pipeline
#         if print_augs: print(self.aug1), print(self.aug2)
#         self.n_in=n_in
#         self._show_batch=show_batch
#         self.criterion = nn.CrossEntropyLoss()
        
#         self.data=data #if data is just e.g. 20 samples then don't bother re-loading each time
        
#     def before_fit(self): 
#         self.learn.loss_func = self.lf
            
#     def before_batch(self):

#         if self.n_in == 1:
#             xi,xj = self.aug1(TensorImageBW(self.x)), self.aug2(TensorImageBW(self.x))                            
#         elif self.n_in == 3:
#             xi,xj = self.aug1(TensorImage(self.x)), self.aug2(TensorImage(self.x))
#         self.learn.xb = (xi,)

#         if self._show_batch:
#             self.learn.aug_x = torch.cat([xi, xj])

#     def lf(self, pred, *yb):        
#         loss=self.criterion(pred,self.y)
#         return loss

#     @torch.no_grad()
#     def show(self, n=1):
#         if self._show_batch==False:
#             print('Need to set show_batch=True')
#             return
#         bs = self.learn.aug_x.size(0)//2
#         x1,x2  = self.learn.aug_x[:bs], self.learn.aug_x[bs:]
#         idxs = np.random.choice(range(bs),n,False)
#         x1 = self.aug1.decode(x1[idxs].to('cpu').clone(),full=False).clamp(0,1) #full=True / False
#         x2 = self.aug2.decode(x2[idxs].to('cpu').clone(),full=False).clamp(0,1) #full=True / False
#         images = []
#         for i in range(n): images += [x1[i],x2[i]]
#         return show_batch(x1[0], None, images, max_n=len(images), nrows=n)


#A more comprehensive callback, copy pasted from cancer-proj
class LinearBt(Callback):
    order,run_valid = 9,True
    def __init__(self,aug_pipelines,n_in, show_batch=False, print_augs=False,data=None,
                 tune_model_path=None,tune_save_after=None):
        self.aug1= aug_pipelines[0]
        self.aug2=Pipeline( split_idx = 0) #empty pipeline
        if print_augs: print(self.aug1), print(self.aug2)
        self.n_in=n_in
        self._show_batch=show_batch
        self.criterion = nn.CrossEntropyLoss()
        self.data=data #if data is just e.g. 20 samples then don't bother re-loading each time


    def before_fit(self):
        self.learn.loss_func = self.lf
            
    def before_batch(self):

        if self.n_in == 1:
            xi,xj = self.aug1(TensorImageBW(self.x)), self.aug2(TensorImageBW(self.x))                            
        elif self.n_in == 3:
            xi,xj = self.aug1(TensorImage(self.x)), self.aug2(TensorImage(self.x))
        self.learn.xb = (xi,)

        if self._show_batch:
            self.learn.aug_x = torch.cat([xi, xj])

    def lf(self, pred, *yb):        
        loss=self.criterion(pred,self.y)
        return loss

    @torch.no_grad()
    def show(self, n=1):
        if self._show_batch==False:
            print('Need to set show_batch=True')
            return
        bs = self.learn.aug_x.size(0)//2
        x1,x2  = self.learn.aug_x[:bs], self.learn.aug_x[bs:]
        idxs = np.random.choice(range(bs),n,False)
        x1 = self.aug1.decode(x1[idxs].to('cpu').clone(),full=False).clamp(0,1) #full=True / False
        x2 = self.aug2.decode(x2[idxs].to('cpu').clone(),full=False).clamp(0,1) #full=True / False
        images = []
        for i in range(n): images += [x1[i],x2[i]]
        return show_batch(x1[0], None, images, max_n=len(images), nrows=n)

# %% ../nbs/base_supervised.ipynb 13
def show_linear_batch(dls,n_in,aug,n=2,print_augs=True):
    "Given a linear learner, show a batch"
    bt = LinearBt(aug,show_batch=True,n_in=n_in,print_augs=print_augs)
    learn = Learner(dls,model=None, cbs=[bt])
    b = dls.one_batch()
    learn._split(b)
    learn('before_batch')
    axes = learn.linear_bt.show(n=n)
    

# %% ../nbs/base_supervised.ipynb 15
def get_supervised_dls(dataset,
                      pct_dataset_train,
                      pct_dataset_test,
                      bs,
                      bs_test,size,
                      device):
    "Get train and test dataloaders for supervised learning"

    try:
        # Construct the module path
        module_path = f"{PACKAGE_NAME}.{dataset}_dataloading"
        
        # Dynamically import the module
        dataloading_module = importlib.import_module(module_path)
    except ModuleNotFoundError:
        # Handle the case where the module cannot be found
        raise ImportError(f"Could not find a data loading module for '{dataset}'. "
                          f"Make sure '{module_path}' exists and is correctly named.") from None
    
    # Assuming the function name follows a consistent naming convention
    func_name_train = f"get_supervised_{dataset}_train_dls"
    try:
        # Retrieve the data loading function from the module
        train_data_loader_func = getattr(dataloading_module, func_name_train)
    except AttributeError:
        # Handle the case where the function does not exist in the module
        raise AttributeError(f"The function '{func_name_train}' was not found in '{module_path}'. "
                             "Ensure it is defined and named correctly.") from None
    
    # Proceed to call the function with arguments from the config
    try:
        dls_train = train_data_loader_func(bs=bs,
                                           size=size,
                                           pct_dataset=pct_dataset_train,
                                           device=device
                                            )
    except Exception as e:
        # Handle any errors that occur during the function call
        raise RuntimeError(f"An error occurred while calling '{func_name_train}' from '{module_path}': {e}") from None
    
    
      # Assuming the function name follows a consistent naming convention
    func_name_test = f"get_supervised_{dataset}_test_dls"
    try:
        # Retrieve the data loading function from the module
        test_data_loader_func = getattr(dataloading_module, func_name_test)
    except AttributeError:
        # Handle the case where the function does not exist in the module
        raise AttributeError(f"The function '{func_name_test}' was not found in '{module_path}'. "
                             "Ensure it is defined and named correctly.") from None
    
    # Proceed to call the function with arguments from the config
    try:
        dls_test = test_data_loader_func(bs=bs_test,
                                         size=size,
                                         pct_dataset=pct_dataset_test,
                                         device=device
                                        )
    except Exception as e:
        # Handle any errors that occur during the function call
        raise RuntimeError(f"An error occurred while calling '{func_name_test}' from '{module_path}': {e}") from None
    
    
    return {'dls_train':dls_train,'dls_test':dls_test}

# %% ../nbs/base_supervised.ipynb 16
def get_supervised_cifar10_augmentations(size):

    return get_linear_batch_augs(size=size,resize=True,resize_scale=(0.3,1.0),stats=cifar_stats)


def get_supervised_isic_augmentations(size):

    aug_pipelines_tune =  [get_barlow_twins_aug_pipelines(size=size,
                    rotate=True,jitter=False,noise=False,bw=False,blur=False,solar=False,cutout=False, #Whether to use aug or not
                    resize_scale=(0.7, 1.0),resize_ratio=(3/4, 4/3),rotate_deg=45.0,
                    flip_p=0.25, rotate_p=0.25,
                    same_on_batch=False,stats=None
                                                         )
                           ]
    return aug_pipelines_tune


def get_supervised_aug_pipelines(augs,size):

    return supervised_aug_func_dict[augs](size)


supervised_aug_func_dict = {'supervised_cifar10_augmentations':get_supervised_cifar10_augmentations,
                            'supervised_isic_augmentations':get_supervised_isic_augmentations}

# %% ../nbs/base_supervised.ipynb 20
def encoder_head_splitter(m):
    return L(sequential(*m.encoder),m.head).map(params)

# %% ../nbs/base_supervised.ipynb 22
class SaveSupLearnerModel(Callback):
    def __init__(self, experiment_dir,num_run):
        self.experiment_dir = experiment_dir
        self.num_run = num_run
    def after_fit(self):
        model_filename = f"trained_model_num_run_{self.num_run}.pth"
        model_path = os.path.join(self.experiment_dir, model_filename)
        torch.save(self.learn.model.state_dict(), model_path)
        print(f"Model state dict saved to {model_path}")



# %% ../nbs/base_supervised.ipynb 23
class SupervisedLearning:
    "Train model using supervised learning. Either linear evaluation or semi-supervised."

    def __init__(self,
                 model,
                 dls_train,
                 aug_pipelines_supervised,
                 n_in,
                 wd,
                 device,
                 num_it=100,
                 num_run=None, #n of num_runs. e.g. num_runs=5 and num_run=3 means this is the 3rd run. 
                               #Basically just tells what name to save checkpoint as - if applicable.
                 experiment_dir=None,
                 ):

             
       
        store_attr()
        self.learn = self.setup_learn()

    
    def setup_learn(self):
        """
        Sets up the learner with the model, callbacks, and metrics.

        Returns:
        - learn: The Learner object.
        """
        # Setup the model: encoder + head
        #model = LM(encoder=self.encoder, enc_dim=self.enc_dim, numout=len(self.dls_train.vocab))
        self.model.to(self.device)

        cbs = [LinearBt(aug_pipelines=self.aug_pipelines_supervised, show_batch=True, n_in=self.n_in, print_augs=True)]

        # Setup the learner with callbacks and metrics
        learn = Learner(self.dls_train, self.model, splitter=encoder_head_splitter,cbs=cbs,wd=self.wd, metrics=accuracy)

        return learn
    
    def _get_training_cbs(self):
        "Add train-time cbs to learner. Note e.g. we don't want these in operation when we're doing lr_find."

        #NOTE:
        cbs=[] #can add more here if needed.
        if self.experiment_dir:
            cbs.append(SaveSupLearnerModel(experiment_dir=self.experiment_dir,
                                                num_run = self.num_run,
                                            )
                        )
            
        return cbs
    
    def supervised_learning(self,epochs:int=1):

        test_grad_on(self.learn.model.encoder)
        test_grad_on(self.learn.model.head)
        lrs = self.learn.lr_find(num_it=self.num_it)
        self.learn.fit_one_cycle(epochs, lrs.valley,cbs=self._get_training_cbs())
        return self.learn
    
    def linear_evaluation(self,epochs:int=1):

        self.learn.freeze() #freeze encoder
        test_grad_off(self.learn.model.encoder)
        lrs = self.learn.lr_find(num_it=self.num_it) #find learning rate
        self.learn.fit_one_cycle(epochs, lrs.valley,cbs=self._get_training_cbs()) #fit head
        return self.learn

    def semi_supervised(self,freeze_epochs:int=1,epochs:int=1):

        self.learn.freeze() #freeze encoder
        test_grad_off(self.learn.model.encoder)
        self.learn.fit(freeze_epochs) #fit head for (typically one) epoch
        self.learn.unfreeze() #unfreeze encoder
        test_grad_on(self.learn.model)
        lrs = self.learn.lr_find(num_it=self.num_it) #find learning rate
        self.learn.fit_one_cycle(epochs, lrs.valley,cbs=self._get_training_cbs())
        return self.learn

    
    def train(self,learn_type, freeze_epochs:int,epochs:int):

        if learn_type == 'standard':
            return self.supervised_learning(epochs=epochs)

        elif learn_type == 'linear_evaluation':
            return self.linear_evaluation(epochs=epochs)

        elif learn_type == 'semi_supervised':
            return self.semi_supervised(freeze_epochs=freeze_epochs,epochs=epochs)

        else: raise Exception("Invalid weight_type")




# %% ../nbs/base_supervised.ipynb 24
def get_encoder(arch,weight_type,load_pretrained_path=None):
    "Get an encoder for supervised learner. If load_pretrained_path is not None, load the weights from that path."

    encoder = resnet_arch_to_encoder(arch,weight_type)
    if not load_pretrained_path:

        return encoder

    else:

        encoder.load_state_dict(torch.load(load_pretrained_path))
        
        return encoder                          

# %% ../nbs/base_supervised.ipynb 25
def load_sup_model(config,numout,path):

    #Setup model with random weights
    encoder = get_encoder(arch=config.arch,weight_type='random',load_pretrained_path=None)
    model = LM(encoder=encoder, numout=numout, encoder_dimension=config.encoder_dimension)
    
    #load model
    model.load_state_dict(torch.load(path))


# %% ../nbs/base_supervised.ipynb 26
def main_sup_train(config,
        num_run=None,#run we are up to - tell us what name to give the saved checkpoint, if applicable.
        experiment_dir=None, #where to save checkpoints
        ):
    
    "Basically map from config to training a supervised model. Optionally save checkpoints of learner."

    if 'pretrained' in config.weight_type:
        test_eq(config.learn_type in ['semi_supervised','linear_evaluation'],True)

    if config.weight_type == 'dermnet_bt_pretrained':
        print(f"For weight_type={config.weight_type}, make sure you have the correct path. The path to load pretrained encoder we are using is: {config.load_pretrained_path}")


    # #cuda or cpu
    device = default_device()

    dls_dict = get_supervised_dls(dataset=config.dataset,
                                  pct_dataset_train=config.pct_dataset_train,
                                  pct_dataset_test=config.pct_dataset_test,
                                  bs=config.bs, 
                                  bs_test=config.bs_test, 
                                  size=config.size, 
                                  device=device)


    dls_train = dls_dict['dls_train']
    dls_test = dls_dict['dls_test']

    aug_pipelines_supervised = get_supervised_aug_pipelines(config.sup_augs, size=config.size)

    #get encoder: e.g. via loading from checkpoint, or a pretrained model


    #get model: e.g. via loading from checkpoint, or a pretrained model

    numout = len(dls_train.vocab)
    encoder = get_encoder(arch=config.arch,weight_type=config.weight_type,load_pretrained_path=config.load_pretrained_path)
    model = LM(encoder=encoder, numout=numout, encoder_dimension=config.encoder_dimension)

    supervised_trainer = SupervisedLearning(model=model,
                            dls_train=dls_train,
                            aug_pipelines_supervised=aug_pipelines_supervised,
                            n_in=config.n_in,
                            wd=config.wd,
                            device=device,
                            num_it=config.num_it,
                            num_run=num_run,
                            experiment_dir=experiment_dir,
                            )

    # Train the model with the specified configurations and save `learn` checkpoints
    learn = supervised_trainer.train(learn_type=config.learn_type,freeze_epochs=config.freeze_epochs,epochs=config.epochs)
                
    #Save this in experiment_dir also
    classes_to_int={v:i for i,v in enumerate(dls_train.vocab)}
    int_to_classes = {i: v for i, v in enumerate(dls_train.vocab)}
    vocab=dls_train.vocab    

    metrics = get_dls_metrics(dls_test,model,aug_pipelines_supervised,int_to_classes)
    metrics['classes_to_int'] = classes_to_int
    metrics['int_to_classes'] = int_to_classes
    metrics['vocab'] = vocab

    if experiment_dir:
        save_dict_to_gdrive(metrics, experiment_dir, f'metrics_num_run_{num_run}')

    #metrics = load_dict_from_gdrive(experiment_dir, 'metrics')

    return learn,metrics

    


# %% ../nbs/base_supervised.ipynb 27
def get_supervised_experiment_state(config,base_dir):
    """Get the load_learner_path, num_run, for supervised experiment.
       Basically tells us what run we are up to. `load_learner_path` is the path to the highest numbered checkpoint.
       so far. `num_run` is the number of the next run. If num_run>config.num_runs, then we are done.
    """

    load_learner_path, _  = get_highest_num_path(base_dir, config)    

    #Note that if 
    num_run=1 if load_learner_path is None else int(load_learner_path.split('_')[-1])+1

    if num_run>config.num_runs:
        print(f"num_run={num_run}, but already completed {config.num_runs} runs. Exiting.")
        sys.exit()
    

    return load_learner_path, num_run

# %% ../nbs/base_supervised.ipynb 28
def main_sup_experiment(config,
                        base_dir,
                       ):
        """Run a supervised learning experiment with the given configuration and save the results to the experiment directory. Return the experiment directory and experiment hash.
        """
        experiment_dir,experiment_hash,git_commit_hash = setup_experiment(config,base_dir)

        #This time, we don't want to resume but we want to determine which experiment we're running.
        #i.e. for each config, we will train several models.
        #TODO:

        _, num_run = get_supervised_experiment_state(config,base_dir)

        print(f"num_run={num_run}")

        main_sup_train(config=config,
                      num_run=num_run,#run we are up to - tell us what name to give the saved checkpoint, if applicable.
                      experiment_dir=experiment_dir,
                      )
    
  

        # Save a metadata file in the experiment directory with the Git commit hash and other details
        save_metadata_file(experiment_dir=experiment_dir, git_commit_hash=git_commit_hash)

        # After experiment execution and all processing are complete
        update_experiment_index(base_dir,{
        "experiment_hash": experiment_hash,  # Unique identifier derived from the experiment's configuration
        "experiment_dir": experiment_dir,  # Absolute path to the experiment's dedicated directory
        "git_commit_hash": git_commit_hash,  # Git commit hash for the code version used in the experiment
        # Potentially include additional details collected during or after the experiment, such as:
        # Any other metadata or results summary that is relevant to the experiment
                        })

        return experiment_dir,experiment_hash,num_run #Return the experiment_dir so we can easily access the results of the experiment

