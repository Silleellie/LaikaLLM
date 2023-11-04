import itertools
import random

import numpy as np

from src.data.abstract_templates import Task, PromptTarget


class SequentialTask(Task):
    templates_dict = {
        0: PromptTarget(
            input_prompt="sequential_rec for {}: \n\n"
                         "Predict for the user the next element of the following sequence -> \n"
                         "{}",
            target_text="{}"
        ),
        1: PromptTarget(
            input_prompt="sequential_rec for {}: \n\n"
                         "Predict the next element which the user will buy given the following order history -> \n"
                         "{}",
            target_text="{}"
        ),
        2: PromptTarget(
            input_prompt="sequential_rec for {}: \n\n"
                         "What is the element that should be recommended to the user knowing that it has bought -> \n"
                         "{}",
            target_text="{}"
        ),
        3: PromptTarget(
            input_prompt="sequential_rec for {}: \n\n"
                         "Recommend to the user an item from the catalog given its order history -> \n"
                         "{}",
            target_text="{}"
        ),
        4: PromptTarget(
            input_prompt="sequential_rec for {}: \n\n"
                         "This is the order history of the user -> \n"
                         "{} \n"
                         "Recommend the next element that the user will buy",
            target_text="{}"
        ),
        5: PromptTarget(
            input_prompt="sequential_rec for {}: \n\n"
                         "Please predict what item is best to recommend to the user given its order history -> \n"
                         "{}",
            target_text="{}"
        )
    }

    def valid_templates(self, return_id: bool = False):
        return self.all_templates(return_id)

    @Task.validate_args("user_id", "input_item_seq", "gt_item")
    def __call__(self, **kwargs):
        user_id = kwargs["user_id"]
        order_history = kwargs["input_item_seq"]
        target_item = kwargs["gt_item"]

        # random.choice applied to dict with int key returns a value
        input_prompt, target = random.choice(self.all_templates())

        # random select of string separator for titles sequence and the prompt to use
        separator = " , " if random.getrandbits(1) else " ; "
        order_history_str = separator.join(order_history)

        input_text = input_prompt.format(user_id, order_history_str)
        target_text = target.format(target_item)

        return input_text, target_text


class SequentialSideInfoTask(Task):
    templates_dict = {
        0: PromptTarget(
            input_prompt="sequential recommendation - {}: \n\n"
                         "Predict for the user the next element of the following sequence -> {} \n"
                         "The category of each element of the sequence is -> {}",
            target_text="{}"
        ),
        1: PromptTarget(
            input_prompt="sequential recommendation - {}: \n\n"
                         "Predict the next element which the user will buy given the following order history -> {} \n"
                         "Each item bought belongs to these categories (in order) -> {}",
            target_text="{}"
        ),
        2: PromptTarget(
            input_prompt="sequential recommendation - {}: \n\n"
                         "What is the element that should be recommended to the user knowing that it has "
                         "bought -> {} \n"
                         "Categories of the items are -> {}",
            target_text="{}"
        ),
        3: PromptTarget(
            input_prompt="sequential recommendation - {}: \n\n"
                         "Recommend to the user an item from the catalog given its order history -> {} \n"
                         "Each item of the order history belongs to the following categories (in order) -> {}",
            target_text="{}"
        ),
        4: PromptTarget(
            input_prompt="sequential recommendation - {}: \n\n"
                         "This is the order history of the user -> {} \n"
                         "These are the categories of each item -> {} \n"
                         "Please recommend the next element that the user will buy",
            target_text="{}"
        ),
        5: PromptTarget(
            input_prompt="sequential recommendation - {}: \n\n"
                         "Please predict what item is best to recommend to the user given its order history -> {} \n"
                         "Categories of each item -> {}",
            target_text="{}"
        ),

        # extractive qa
        6: PromptTarget(
            input_prompt="sequential recommendation - {}: \n\n"
                         "The user has the following order history -> {} \n"
                         "The categories of each item bought are -> {} \n"
                         "Which item would the user buy next? Select from the following: \n"
                         "{}",
            target_text="{}"
        ),

        7: PromptTarget(
            input_prompt="sequential recommendation - {}: \n\n"
                         "The user has bought {}, and the categories of those items are {}. \n"
                         "Choose an item to recommend to the user selecting from: \n"
                         "{}",
            target_text="{}"
        ),

        # pair seq
        8: PromptTarget(
            input_prompt="sequential recommendation - {}: \n\n"
                         "The user has recently bought {} which has the following categories: {} \n"
                         "What is the next item to recommend?",
            target_text="{}"
        ),

        9: PromptTarget(
            input_prompt="sequential recommendation - {}: \n\n"
                         "The latest item bought by the user is {}. The categories of that item are {}. "
                         "Predict which item the user will buy next",
            target_text="{}"
        )
    }

    def valid_templates(self, return_id: bool = False):
        return self.all_templates(return_id)[:6]

    def qa_templates(self, return_id: bool = False):
        return [self.templates_dict[6], self.templates_dict[7]] if not return_id else [6, 7]

    def pair_templates(self, return_id: bool = False):
        return [self.templates_dict[8], self.templates_dict[9]] if not return_id else [8, 9]

    @Task.validate_args("user_id", "input_item_seq", "input_categories_seq", "gt_item")
    def __call__(self, **kwargs):

        assert len(kwargs["gt_item"]) == 1, "This task was designed for Leave One Out strategy!"

        user_id = kwargs["user_id"]
        order_history = kwargs["input_item_seq"]
        input_categories_seq = kwargs["input_categories_seq"]
        [target_item] = kwargs["gt_item"]

        out_list = []

        # using all categories is maybe too much, let's use only one category for each item in the seq
        reduced_categories = [random.choice(categories) for categories in input_categories_seq]

        input_prompt_valid, target_valid = random.choice(self.valid_templates())

        # random select of string separator for titles sequence and the prompt to use
        separator = " , " if random.getrandbits(1) else " ; "
        order_history_str = separator.join(order_history)
        input_categories_str = separator.join(reduced_categories)

        # random choice of valid template
        input_text_valid = input_prompt_valid.format(user_id, order_history_str, input_categories_str)
        target_text_valid = target_valid.format(target_item)

        out_list.append((input_text_valid, target_text_valid))

        if self.training:

            input_text_qa, target_text_qa = self._create_input_target_qa(user_id,
                                                                         order_history_str,
                                                                         input_categories_str,
                                                                         target_item)

            input_text_pair, target_text_pair = self._create_input_target_pair(user_id,
                                                                               order_history,
                                                                               input_categories_seq,
                                                                               target_item)

            out_list.extend([(input_text_qa,  target_text_qa), (input_text_pair, target_text_pair)])

        return out_list

    def _create_input_target_qa(self, user_id, order_history_str, input_categories_str, target_item):
        # random choice of qa template
        input_prompt_support, target_support = random.choice(self.qa_templates())

        bullet_list_wrong_size = 4
        all_possible_candidates = self.all_unique_items[self.all_unique_items != target_item]
        candidates = np.random.choice(all_possible_candidates, size=bullet_list_wrong_size, replace=False)

        candidates = np.append(candidates, target_item)
        np.random.shuffle(candidates)

        bullet_notation = "* " if random.getrandbits(1) else "- "
        bullet_list = (f"{bullet_notation} {{}}\n" * len(candidates)).format(*candidates)

        input_text_qa = input_prompt_support.format(user_id, order_history_str, input_categories_str, bullet_list)
        target_text_qa = target_support.format(target_item)

        return input_text_qa, target_text_qa

    def _create_input_target_pair(self, user_id, order_history, input_categories, target_item):
        # random choice of pair template
        input_prompt_support, target_support = random.choice(self.pair_templates())

        first_of_pair_idx = random.randint(0, len(order_history) - 1)
        first_of_pair = order_history[first_of_pair_idx]

        separator = " , " if random.getrandbits(1) else " ; "
        first_of_pair_cat = separator.join(input_categories[first_of_pair_idx])

        if first_of_pair_idx == (len(order_history) - 1):
            second_of_pair = target_item
        else:
            second_of_pair = order_history[first_of_pair_idx + 1]

        input_text_pair = input_prompt_support.format(user_id, first_of_pair, first_of_pair_cat)
        target_text_pair = second_of_pair

        return input_text_pair, target_text_pair


class DirectTask(Task):
    templates_dict = {
        0: PromptTarget(
            input_prompt="direct recommendation - {}: \n\n"
                         "Pick an item from the catalog likely to be bought by the user",
            target_text="{}"
        ),
        1: PromptTarget(
            input_prompt="direct recommendation - {}: \n\n"
                         "Recommend an item to the user",
            target_text="{}"
        ),
        2: PromptTarget(
            input_prompt="direct recommendation - {}: \n\n"
                         "What is the item that should be recommended to the user?",
            target_text="{}"
        ),
        3: PromptTarget(
            input_prompt="direct recommendation - {}: \n\n"
                         "Select an item to present to the user",
            target_text="{}"
        ),
        4: PromptTarget(
            input_prompt="direct recommendation - {}: \n\n"
                         "Please recommend an item that the user will buy",
            target_text="{}"
        ),
        5: PromptTarget(
            input_prompt="direct recommendation - {}: \n\n"
                         "Please predict what item is best to recommend to the user",
            target_text="{}"
        )
    }

    def valid_templates(self, return_id: bool = False):
        return self.all_templates(return_id)

    @Task.validate_args("user_id", "input_item_seq", "gt_item")
    def __call__(self, **kwargs):
        user_id = kwargs["user_id"]
        input_item_seq = kwargs["input_item_seq"]
        target_item = kwargs["gt_item"]

        if self.training:
            input_item_seq = input_item_seq + [target_item]

            target_idx = random.randint(0, len(input_item_seq) - 1)

            target_item = input_item_seq.pop(target_idx)

        # random.choice applied to dict with int key returns a value
        input_prompt, target = random.choice(self.all_templates())

        input_text = input_prompt.format(user_id)
        target_text = target.format(target_item)

        return input_text, target_text


class DirectSideInfoTask(Task):
    templates_dict = {
        0: PromptTarget(
            input_prompt="direct recommendation - {}: \n\n"
                         "Pick an item from the catalog knowing that these are the categories "
                         "the user likes -> {}",
            target_text="{}"
        ),
        1: PromptTarget(
            input_prompt="direct recommendation - {}: \n\n"
                         "Recommend an item to the user. The categories of the items bought by the user are -> {}",
            target_text="{}"
        ),
        2: PromptTarget(
            input_prompt="direct recommendation - {}: \n\n"
                         "What is the item that should be recommended to the user? It likes "
                         "these categories -> {}",
            target_text="{}"
        ),
        3: PromptTarget(
            input_prompt="direct recommendation - {}: \n\n"
                         "Select an item to present to the user given the categories that it likes -> {}",
            target_text="{}"
        ),
        4: PromptTarget(
            input_prompt="direct recommendation - {}: \n\n"
                         "These are the categories of the items bought by the user -> {} \n"
                         "Please recommend an item that the user will buy",
            target_text="{}"
        ),
        5: PromptTarget(
            input_prompt="direct recommendation - {}: \n\n"
                         "Please predict what item is best to recommend to the user. The categories that it likes "
                         "are -> {}",
            target_text="{}"
        ),

        # extractive qa
        6: PromptTarget(
            input_prompt="direct recommendation - {}: \n\n"
                         "The categories liked by the user are -> {} \n"
                         "Which item can interest the user? Select one from the following: \n"
                         "{}",
            target_text="{}"
        ),
        7: PromptTarget(
            input_prompt="direct recommendation - {}: \n\n"
                         "The user so far has bought items with these categories -> {}. \n"
                         "Choose an item to recommend to the user selecting from: \n"
                         "{}",
            target_text="{}"
        ),
        8: PromptTarget(
            input_prompt="direct recommendation - {}: \n\n"
                         "These are the categories of the items bought by the user -> {}. \n"
                         "Predict an item to suggest to the user from the followings: \n"
                         "{}",
            target_text="{}"
        ),
    }

    def valid_templates(self, return_id: bool = False):
        return self.all_templates(return_id)[:6]

    def qa_templates(self, return_id: bool = False):
        return self.all_templates(return_id)[6:]

    @Task.validate_args("user_id", "input_item_seq", "input_categories_seq", "gt_item", "gt_categories")
    def __call__(self, **kwargs):
        user_id = kwargs["user_id"]
        input_item_seq = kwargs["input_item_seq"]
        input_categories_seq = kwargs["input_categories_seq"]
        [target_categories] = kwargs["gt_categories"]
        [target_item] = kwargs["gt_item"]

        out_list = []

        if self.training:
            input_item_seq = input_item_seq + [target_item]
            input_categories_seq = input_categories_seq + [target_categories]

            target_idx = random.randint(0, len(input_item_seq) - 1)

            target_item = input_item_seq.pop(target_idx)
            input_categories_seq.pop(target_idx)  # this is simply removed , we don't use this

        # we use only unique categories
        unique_categories = set(itertools.chain.from_iterable(input_categories_seq))

        input_prompt_valid, target_valid = random.choice(self.valid_templates())

        # random select of string separator for titles sequence and the prompt to use
        separator = " , " if random.getrandbits(1) else " ; "
        categories_liked_str = separator.join(unique_categories)

        input_text_valid = input_prompt_valid.format(user_id, categories_liked_str)
        target_text_valid = target_valid.format(target_item)

        out_list.append((input_text_valid, target_text_valid))

        if self.training:
            input_text_qa, target_text_qa = self._create_input_target_qa(user_id,
                                                                         categories_liked_str,
                                                                         target_item)

            out_list.append((input_text_qa, target_text_qa))

        return out_list

    def _create_input_target_qa(self, user_id, input_categories_str, target_item):
        # random choice of qa template
        input_prompt_support, target_support = random.choice(self.qa_templates())

        bullet_list_wrong_size = 4
        all_possible_candidates = self.all_unique_items[self.all_unique_items != target_item]
        candidates = np.random.choice(all_possible_candidates, size=bullet_list_wrong_size, replace=False)

        candidates = np.append(candidates, target_item)
        np.random.shuffle(candidates)

        bullet_notation = "* " if random.getrandbits(1) else "- "
        bullet_list = (f"{bullet_notation} {{}}\n" * len(candidates)).format(*candidates)

        input_text_qa = input_prompt_support.format(user_id, input_categories_str, bullet_list)
        target_text_qa = target_support.format(target_item)

        return input_text_qa, target_text_qa
