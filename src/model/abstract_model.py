from __future__ import annotations

from abc import abstractmethod, ABC
from typing import List, Optional

import numpy as np
import torch

from src.data.abstract_dataset import LaikaDataset
from src.data.abstract_templates import Task


class LaikaModel(ABC):
    str_alias_cls = {}

    # automatically called on subclass definition, will populate the str_alias_cls dict
    def __init_subclass__(cls, **kwargs):
        cls.str_alias_cls[cls.__name__] = cls

        super().__init_subclass__(**kwargs)

    def __init__(self, training_tasks_str: List[str],
                 all_unique_labels: List[str],
                 eval_task_str: str = None,
                 eval_template_id: int = None):

        if training_tasks_str is None:
            raise AttributeError("training_tasks_str parameter can't be None!")
        if all_unique_labels is None:
            raise AttributeError("all_unique_labels parameter can't be None!")

        self.all_unique_labels = np.array(all_unique_labels)
        self.training_tasks = Task.from_string(*training_tasks_str,
                                               all_unique_items=self.all_unique_labels)

        self.eval_task = None
        if eval_task_str is not None:
            self.set_eval_task(eval_task_str, eval_template_id)

    def set_eval_task(self, eval_task_str: str, template_id: int = None):
        self.eval_task = Task.from_string(eval_task_str, all_unique_items=self.all_unique_labels)

        if template_id is not None:
            self.eval_task.force_template_id(template_id)

    @property
    @abstractmethod
    def get_suggested_optimizer(self):
        raise NotImplementedError

    @abstractmethod
    def tokenize(self, batch: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def prepare_input(self, tokenized_batch: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def train_step(self, prepared_batch: dict) -> torch.FloatTensor:
        raise NotImplementedError

    @abstractmethod
    @torch.no_grad()
    # if labels are in "prepared_batch", also valid loss should be returned
    def generate_step(self, prepared_batch: dict) -> tuple[torch.FloatTensor, np.ndarray[str]] | np.ndarray[str]:
        raise NotImplementedError

    @abstractmethod
    def train(self, mode: bool = True):
        raise NotImplementedError

    def eval(self):
        Task.eval()

        return self.train(False)

    @abstractmethod
    def save(self, output_dir: str):
        raise NotImplementedError

    @abstractmethod
    def to(self, device: str):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def load(cls, dir_path: str, **kwargs) -> LaikaModel:
        raise NotImplementedError

    @classmethod
    def from_automatic_usage(cls, dataset_obj: LaikaDataset, **kwargs):

        kwargs["all_unique_labels"] = dataset_obj.all_items.tolist()

        return cls(**kwargs)