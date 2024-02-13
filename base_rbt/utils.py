# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/utils.ipynb.

# %% auto 0
__all__ = ['cfg', 'PACKAGE_NAME', 'test_grad_on', 'test_grad_off', 'seed_everything', 'adjust_config_with_derived_values',
           'load_config', 'get_ssl_dls', 'get_resnet_encoder', 'resnet_arch_to_encoder', 'generate_config_hash',
           'create_experiment_directory', 'save_configuration', 'save_metadata_file', 'update_experiment_index',
           'get_latest_commit_hash', 'setup_experiment']

# %% ../nbs/utils.ipynb 3
from fastcore.test import *
from fastai.vision.all import *
import torch
from torchvision.models import resnet18, resnet34, resnet50
import random 
import os 
import yaml
import numpy as np
import yaml
import configparser
from types import SimpleNamespace
import importlib
from nbdev import config
import json
import hashlib
import subprocess


# %% ../nbs/utils.ipynb 4
cfg = config.get_config()
PACKAGE_NAME = cfg.lib_name

# %% ../nbs/utils.ipynb 5
def test_grad_on(model):
    """
    Test that all grads are on for modules with parameters.
    """
    for name, module in model.named_modules():
        # Check each parameter in the module
        for param_name, param in module.named_parameters(recurse=False):
            assert param.requires_grad, f"Gradients are off for {name}.{param_name}"

def test_grad_off(model):
    """
    Test that all non-batch norm grads are off, but batch norm grads are on.
    """
    for name, module in model.named_modules():
        # Distinguish between BatchNorm and other layers
        if isinstance(module, (torch.nn.BatchNorm1d, torch.nn.BatchNorm2d, torch.nn.BatchNorm3d)):
            for param_name, param in module.named_parameters(recurse=False):
                assert param.requires_grad, f"BatchNorm parameter does not require grad in {name}.{param_name}"
        else:
            for param_name, param in module.named_parameters(recurse=False):
                assert not param.requires_grad, f"Gradients are on for non-BatchNorm layer {name}.{param_name}"

# %% ../nbs/utils.ipynb 6
def seed_everything(seed=42):
    """"
    Seed everything.
    """   
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True

# %% ../nbs/utils.ipynb 7
def adjust_config_with_derived_values(config):
    # Adjust n_in based on dataset
    if config.dataset == 'cifar10':
        config.n_in = 3

    # Adjust encoder_dimension based on architecture
    if config.arch == 'resnet18':
        config.encoder_dimension = 512
    elif config.arch == 'resnet34':
        config.encoder_dimension = 512
    elif config.arch == 'resnet50':
        config.encoder_dimension = 2048

    else :
        raise ValueError(f"Architecture {config.arch} not supported")

    return config

def load_config(file_path):
    with open(file_path, 'r') as f:
        config = yaml.safe_load(f)
        config = SimpleNamespace(**config)
        config = adjust_config_with_derived_values(config)
        

    return config

# %% ../nbs/utils.ipynb 8
def get_ssl_dls(dataset,bs,device):
    # Define the base package name in a variable for easy modification

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
    func_name = f"get_bt_{dataset}_train_dls"
    try:
        # Retrieve the data loading function from the module
        data_loader_func = getattr(dataloading_module, func_name)
    except AttributeError:
        # Handle the case where the function does not exist in the module
        raise AttributeError(f"The function '{func_name}' was not found in '{module_path}'. "
                             "Ensure it is defined and named correctly.") from None
    
    # Proceed to call the function with arguments from the config
    try:
        dls_train = data_loader_func(bs=bs,device=device)
    except Exception as e:
        # Handle any errors that occur during the function call
        raise RuntimeError(f"An error occurred while calling '{func_name}' from '{module_path}': {e}") from None
    
    return dls_train


# %% ../nbs/utils.ipynb 9
@torch.no_grad()
def get_resnet_encoder(model,n_in=3):
    model = create_body(model, n_in=n_in, pretrained=False, cut=len(list(model.children()))-1)
    model.add_module('flatten', torch.nn.Flatten())
    return model

# @torch.no_grad()
# def create_resnet50_encoder(weight_type):

#     #pretrained=True if 'weight_type' in ['bt_pretrain', 'supervised_pretrain'] else False

#     if weight_type == 'bt_pretrain': model = torch.hub.load('facebookresearch/barlowtwins:main', 'resnet50')
    
#     elif weight_type == 'no_pretrain': model = resnet50()

#     elif weight_type == 'supervised_pretrain': model = resnet50(weights='IMAGENET1K_V2')

#     #ignore the 'pretrained=False' argument here. Just means we use the weights above 
#     #(which themselves are either pretrained or not)
#     encoder = get_resnet_encoder(model)

#     return encoder

@torch.no_grad()
def resnet_arch_to_encoder(arch:str,weight_type='random'):
    """Given resnet architecture, return the encoder. Works for 3 channels.
       The 'weight_type' argument is used to specify whether the model is pretrained or not
    """

    n_in=3

    test_eq(arch in ['resnet18','resnet34','resnet50'],True)
    test_eq(weight_type in ['bt_pretrained','supervised_pretrained','random'],True)

    if weight_type == 'bt_pretrained': test_eq(arch,'resnet50')

    
    if arch == 'resnet50':

        if weight_type == 'bt_pretrained':
            _model = torch.hub.load('facebookresearch/barlowtwins:main', 'resnet50')

        elif weight_type == 'supervised_pretrained':
            _model = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2)

        elif weight_type == 'random':
            _model = resnet50()
        

    elif arch == 'resnet34':

        if weight_type == 'supervised_pretrained':
            _model = resnet34(weights=ResNet34_Weights.IMAGENET1K_V1)

        elif weight_type == 'random':
            _model = resnet34() 

    elif arch == 'resnet18':
        if weight_type == 'supervised_pretrained':
            _model = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1) 

        elif weight_type == 'random':
            _model = resnet18()
        
    else: raise ValueError('Architecture not recognized')

    return get_resnet_encoder(_model,n_in) 



# %% ../nbs/utils.ipynb 10
def generate_config_hash(config):
    """
    Generates a unique hash for a given experiment configuration.
    
    Args:
    config (dict or Namespace): Experiment configuration. Can be a dictionary or a namespace object.
    
    Returns:
    str: A unique hash representing the experiment configuration.
    """
    # Convert config to dict if it's a Namespace
    config_dict = vars(config) if not isinstance(config, dict) else config
    
    # Serialize configuration to a sorted JSON string to ensure consistency
    config_str = json.dumps(config_dict, sort_keys=True)
    
    # Generate SHA-256 hash from the serialized string
    hash_obj = hashlib.sha256(config_str.encode())  # Encode to convert string to bytes
    config_hash = hash_obj.hexdigest()
    
    # Optionally, return a truncated version of the hash for readability
    short_hash = config_hash[:8]  # Use the first 8 characters as an example
    return short_hash


# %% ../nbs/utils.ipynb 13
def create_experiment_directory(base_dir, config):
    # Generate a unique hash for the configuration
    unique_hash = generate_config_hash(config)
    
    # Construct the directory path for this experiment
    experiment_dir = os.path.join(base_dir, config.train_type, config.dataset, config.arch, unique_hash)
    
    # Create the directory if it doesn't exist
    os.makedirs(experiment_dir, exist_ok=True)
    
    return experiment_dir,unique_hash


def save_configuration(config, experiment_dir):
    """
    Saves the experiment configuration as a YAML file in the experiment directory.

    Args:
    config (dict, Namespace, or any serializable object): Experiment configuration.
    experiment_dir (str): Path to the directory where the config file will be saved.
    """
    config_file_path = os.path.join(experiment_dir, 'config.yaml')
    
    # Check if config is not a dictionary (e.g., a Namespace object) and convert if necessary
    config_dict = vars(config) if not isinstance(config, dict) else config
    
    with open(config_file_path, 'w') as file:
        yaml.dump(config_dict, file)
    
    print(f"Configuration saved to {config_file_path}")




def save_metadata_file(experiment_dir, git_commit_hash, Description):
    """
    Saves a metadata file with the Git commit hash, start/end times, and a description for the experiment.
    """
    metadata_file_path = os.path.join(experiment_dir, 'metadata.yaml')
    metadata_content = {
        "Git Commit Hash": git_commit_hash,
        "Description": Description
    }

    with open(metadata_file_path, 'w') as file:
        yaml.dump(metadata_content, file)

    print(f"Metadata saved to {metadata_file_path}")


def update_experiment_index(project_root, details):
    central_json_path = os.path.join(project_root, 'experiment_index.json')
    
    if os.path.exists(central_json_path):
        with open(central_json_path, 'r') as file:
            experiments_index = json.load(file)
    else:
        experiments_index = {}
    
    experiment_hash = details["experiment_hash"]
    experiments_index[experiment_hash] = details
    
    with open(central_json_path, 'w') as file:
        json.dump(experiments_index, file, indent=4)
    
    print(f"Updated experiment index for hash: {experiment_hash}")


def get_latest_commit_hash(repo_path):
    try:
        commit_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo_path).decode('ascii').strip()
        return commit_hash
    except subprocess.CalledProcessError as e:
        print(f"Error obtaining latest commit hash: {e}")
        return None

def setup_experiment(config,base_dir,Description:str):

    # Create a unique directory for this experiment based on its configuration
    # This directory will contain all artifacts related to the experiment, such as model checkpoints and logs.
    experiment_dir, experiment_hash = create_experiment_directory(base_dir, config)

    print(f"The experiment_dir is: {experiment_dir} and the experiment hash is: {experiment_hash}")

    # Save the loaded configuration to the experiment directory as a YAML file
    # This ensures that we can reproduce or analyze the experiment later.
    save_configuration(config, experiment_dir)

    git_commit_hash = get_latest_commit_hash('.')
    print(f"The git hash is: {git_commit_hash}")

    return experiment_dir, experiment_hash,git_commit_hash
