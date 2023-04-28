# Original Copyright (c) Microsoft Corporation. Licensed under the MIT License.
# Modifications Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import json
import numpy as np

from semilearn.datasets.utils import split_ssl_data
from .datasetbase import BasicDataset


def get_json_dset(args, alg='fixmatch', dataset='acmIb', num_labels=40, num_classes=20, data_dir='./data', index=None, include_lb_to_ulb=True, onehot=False):
        """
        get_ssl_dset split training samples into labeled and unlabeled samples.
        The labeled data is balanced samples over classes.
        
        Args:
            num_labels: number of labeled data.
            index: If index of np.array is given, labeled data is not randomly sampled, but use index for sampling.
            include_lb_to_ulb: If True, consistency regularization is also computed for the labeled data.
            strong_transform: list of strong transform (RandAugment in FixMatch)
            onehot: If True, the target is converted into onehot vector.
            
        Returns:
            BasicDataset (for labeled data), BasicDataset (for unlabeld data)
        """
        json_dir = os.path.join(data_dir, dataset)
        train_file = os.path.join(json_dir, 'train.json')
        if args.custom_dev_data_file is None:
            dev_file = os.path.join(json_dir, 'dev.json')
        else:
            dev_file = args.custom_dev_data_file
        if args.custom_test_data_file is None:
            test_file = os.path.join(json_dir, 'test.json')
        else:
            test_file = args.custom_test_data_file
        
        # Supervised top line using all data as labeled data.
        with open(train_file,'r') as json_data:
            train_data = json.load(json_data)
            train_sen_list = []
            train_label_list = []
            for idx in train_data:
                train_sen_list.append((train_data[idx]['ori'],train_data[idx]['aug_0'],train_data[idx]['aug_1']))
                train_label_list.append(int(train_data[idx]['label']))              

        with open(dev_file,'r') as json_data:
            dev_data = json.load(json_data)
            dev_sen_list = []
            dev_label_list = []
            for idx in dev_data:
                dev_sen_list.append((dev_data[idx]['ori'],'None','None'))
                dev_label_list.append(int(dev_data[idx]['label']))

        with open(test_file,'r') as json_data:
            test_data = json.load(json_data)
            test_sen_list = []
            test_label_list = []
            for idx in test_data:
                test_sen_list.append((test_data[idx]['ori'],'None','None'))
                test_label_list.append(int(test_data[idx]['label']))
        dev_dset = BasicDataset(alg, dev_sen_list, dev_label_list, num_classes, False, onehot)
        test_dset = BasicDataset(alg, test_sen_list, test_label_list, num_classes, False, onehot)
        if alg == 'fullysupervised':
            lb_dset = BasicDataset(alg, train_sen_list, train_label_list, num_classes, False,onehot)
            return lb_dset, None, dev_dset, test_dset
        
        lb_sen_list, lb_label_list, ulb_sen_list, ulb_label_list = split_ssl_data(args, train_sen_list, train_label_list, num_classes, 
                                                                    lb_num_labels=num_labels,
                                                                    ulb_num_labels=args.ulb_num_labels,
                                                                    lb_imbalance_ratio=args.lb_imb_ratio,
                                                                    ulb_imbalance_ratio=args.ulb_imb_ratio,
                                                                    include_lb_to_ulb=include_lb_to_ulb)

        if args.custom_unlabeled_data_file is not None:
            print("Custom unlabeled data {} is used.".format(args.custom_unlabeled_data_file))
            ulb_sen_list, ulb_label_list = [], []
            with open(args.custom_unlabeled_data_file,'r') as json_data:
                custom_data = json.load(json_data)
                custom_sen_list = []
                custom_label_list = []
                for idx in custom_data:
                    custom_sen_list.append((custom_data[idx]['ori'], custom_data[idx]['aug_0'], custom_data[idx]['aug_1']))
                    custom_label_list.append(int(custom_data[idx]['label']))
            custom_sen_list, custom_label_list = np.array(custom_sen_list), np.array(custom_label_list)
            ulb_sen_list, ulb_label_list = np.concatenate([lb_sen_list, custom_sen_list], axis=0), np.concatenate([lb_label_list, custom_label_list], axis=0)

        # output the distribution of labeled data for remixmatch
        count = [0 for _ in range(num_classes)]
        for c in train_label_list:
            count[c] += 1
        dist = np.array(count, dtype=float)
        dist = dist / dist.sum()
        dist = dist.tolist()
        out = {"distribution": dist}
        output_file = r"./data_statistics/"
        output_path = output_file + str(dataset) + '_' + str(num_labels) + '.json'
        if not os.path.exists(output_file):
            os.makedirs(output_file, exist_ok=True)
        with open(output_path, 'w') as w:
            json.dump(out, w)
        
        lb_dset = BasicDataset(alg, lb_sen_list, lb_label_list, num_classes, False, onehot)
        ulb_dset = BasicDataset(alg, ulb_sen_list, ulb_label_list, num_classes, True, onehot)
        return lb_dset, ulb_dset, dev_dset, test_dset
