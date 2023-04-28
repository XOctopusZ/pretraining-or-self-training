# Original Copyright (c) Microsoft Corporation. Licensed under the MIT License.
# Modifications Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# Ref: https://github.com/open-mmlab/mmcv/blob/master/mmcv/runner/hooks/evaluation.py

import os
from .hook import Hook


class EvaluationHook(Hook):
    def __init__(self) -> None:
        super().__init__()
    
    def after_train_step(self, algorithm):
        if self.every_n_iters(algorithm, algorithm.num_eval_iter) or self.is_last_iter(algorithm):
            algorithm.print_fn("validating...")
            eval_dict = algorithm.evaluate('eval')
            algorithm.tb_dict.update(eval_dict)

            # # update best metrics
            # if algorithm.tb_dict['eval/top-1-acc'] > algorithm.best_eval_acc:
            #     algorithm.best_eval_acc = algorithm.tb_dict['eval/top-1-acc']
            #     algorithm.best_it = algorithm.it

            # Use F1 score as the metric to save the best model
            if algorithm.tb_dict['eval/F1'] > algorithm.best_eval_acc:
                algorithm.best_eval_acc = algorithm.tb_dict['eval/F1']
                algorithm.best_it = algorithm.it    

    def after_run(self, algorithm):
        # results_dict = {'eval/best_acc': algorithm.best_eval_acc, 'eval/best_it': algorithm.best_it}
        results_dict = {'eval/best_f1': algorithm.best_eval_acc, 'eval/best_it': algorithm.best_it}
        if 'test' in algorithm.loader_dict:
            # load the best model and evaluate on test dataset
            best_model_path = os.path.join(algorithm.args.save_dir, algorithm.args.save_name, 'model_best.pth')
            tmp_it = algorithm.it
            algorithm.load_model(best_model_path)
            test_dict = algorithm.evaluate('test')
            results_dict['test/acc'] = test_dict['test/top-1-acc']
            results_dict['test/f1'] = test_dict['test/F1']
            algorithm.it = tmp_it
        algorithm.results_dict = results_dict
