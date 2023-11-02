import argparse
import dataclasses
import os

import wandb
from pygit2 import Repository

from src.data.main import data_main
from src.evaluate.main import eval_main
from src.model.main import model_main
from src.utils import seed_everything, init_wandb, LoadFromYaml

from src.yml_parse import parse_yml_config


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Main script to reproduce perform the experiments')

    parser.add_argument('-c', '--config', default="params.yml", required=True, help='')

    # will first parse args from yml file, and if same are passed via cmd,
    # those passed via cmd will prevail
    args = parser.parse_args()

    shared_params, data_params, model_params, eval_params = parse_yml_config(args.config)

    if shared_params.log_wandb:

        if 'WANDB_API_KEY' not in os.environ:
            raise ValueError('Cannot log run to wandb if environment variable "WANDB_API_KEY" is not present\n'
                             'Please set the environment variable and add the api key for wandb\n')

        if 'WANDB_ENTITY' not in os.environ:
            raise ValueError('Cannot log run to wandb if environment variable "WANDB_ENTITY" is not present\n'
                             'Please set the environment variable and add the entity for wandb logs\n')

    # this is the config dict that will be logged to wandb
    # apart from the params read from yml file, log env variables needed for reproducibility and
    # also the current active branch in which experiment is being performed
    config_args = {
        "shared_params": dataclasses.asdict(shared_params),
        "data_params": dataclasses.asdict(data_params),
        "model_params": dataclasses.asdict(model_params),
        "eval_params": dataclasses.asdict(eval_params),
        "PYTHONHASHSEED": os.environ.get("PYTHONHASHSEED"),
        "CUBLAS_WORKSPACE_CONFIG": os.environ.get("CUBLAS_WORKSPACE_CONFIG"),
        "git_branch": Repository('.').head.shorthand
    }

    with init_wandb(project="P5-Thesis", name=shared_params.exp_name, config=config_args,
                    should_log=shared_params.log_wandb):

        # at start of each main phase, we re-initialize the state
        seed_everything(shared_params.random_seed)
        dataset_obj = data_main(shared_params, data_params)

        # at start of each main phase, we re-initialize the state
        seed_everything(shared_params.random_seed)
        model_obj = model_main(shared_params, model_params, dataset_obj)

        # at start of each main phase, we re-initialize the state
        seed_everything(shared_params.random_seed)
        eval_main(shared_params, eval_params, dataset_obj, model_obj)