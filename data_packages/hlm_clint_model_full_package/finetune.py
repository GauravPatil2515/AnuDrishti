import os
import shutil
import sys
import yaml
import numpy as np
import pandas as pd
from datetime import datetime
import warnings
import random
warnings.filterwarnings("ignore")

import torch
from torch import nn
import torch.nn.functional as F
from torch.utils.tensorboard import SummaryWriter
from torch.optim.lr_scheduler import CosineAnnealingLR
from sklearn.metrics import roc_auc_score, mean_squared_error, mean_absolute_error, precision_score, recall_score, f1_score, balanced_accuracy_score, root_mean_squared_error

from dataset.dataset_test import MolTestDatasetWrapper

try:
    import optuna
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    print("Optuna not available. Install with: pip install optuna")


# Mixed precision
from torch.amp import GradScaler, autocast


def _save_config_file(model_checkpoints_folder):
    if not os.path.exists(model_checkpoints_folder):
        os.makedirs(model_checkpoints_folder)
        shutil.copy('./config_finetune.yaml', os.path.join(model_checkpoints_folder, 'config_finetune.yaml'))


class Normalizer(object):
    """Normalize a Tensor and restore it later. """

    def __init__(self, tensor):
        """tensor is taken as a sample to calculate the mean and std"""
        self.mean = torch.mean(tensor)
        self.std = torch.std(tensor)

    def norm(self, tensor):
        return (tensor - self.mean) / self.std

    def denorm(self, normed_tensor):
        return normed_tensor * self.std + self.mean

    def state_dict(self):
        return {'mean': self.mean,
                'std': self.std}

    def load_state_dict(self, state_dict):
        self.mean = state_dict['mean']
        self.std = state_dict['std']


class FineTune(object):
    def __init__(self, dataset, config):
        self.config = config
        self.device = self._get_device()

        # Set random seeds for reproducibility
        self._set_random_seeds()

        current_time = datetime.now().strftime('%b%d_%H-%M-%S')
        if isinstance(config['dataset']['target'], list):
            target_str = 'multi_task'
        else:
            target_str = config['dataset']['target']
        dir_name = current_time + '_' + config['task_name'] + '_' + target_str
        log_dir = os.path.join('finetune', dir_name)
        self.writer = SummaryWriter(log_dir=log_dir)
        self.dataset = dataset
        self.scaler = GradScaler('cuda', enabled=config['fp16_precision'])
        
        # Early stopping parameters
        self.patience = config.get('patience', 20)  # Default patience
        if config['dataset']['task'] == 'classification':
            self.best_metric = 0  # Maximize ROC AUC
        else:
            self.best_metric = float('inf')  # Minimize MAE for regression
        self.counter = 0
        self.early_stop = False
        
        if config['dataset']['task'] == 'classification':
            if config['task_name'] == 'BBBP':
                # Handle class imbalance for BBBP
                pos_weight = torch.tensor([config.get('pos_weight', 2.5)])  # Adjust based on 76%/24% imbalance
                self.criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight.to(self.device), reduction='none')
            else:
                self.criterion = nn.BCEWithLogitsLoss(reduction='none')
        elif config['dataset']['task'] == 'regression':
            if self.config["task_name"] in ['qm7', 'qm8', 'qm9']:
                self.criterion = nn.L1Loss(reduction='none')
            else:
                self.criterion = nn.MSELoss(reduction='none')

    def _set_random_seeds(self):
        """Set random seeds for reproducibility"""
        seed = self.config.get('random_seed', 42)
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False

    def _get_device(self):
        if torch.cuda.is_available() and self.config['gpu'] != 'cpu':
            device = self.config['gpu']
            torch.cuda.set_device(device)
        else:
            device = 'cpu'
        print("Running on:", device)

        return device

    def _step(self, model, data, n_iter):
        # get the prediction
        __, pred = model(data)  # [N,C]

        if self.config['dataset']['task'] == 'classification':
            loss = self.criterion(pred, data.y)
        elif self.config['dataset']['task'] == 'regression':
            if self.normalizer:
                loss = self.criterion(pred, self.normalizer.norm(data.y))
            else:
                loss = self.criterion(pred, data.y)

        # Masking for missing values (marked with -1)
        is_labeled = (data.y != -1)
        loss = torch.where(is_labeled, loss, torch.zeros_like(loss))
        
        # Avoid division by zero
        if is_labeled.sum() == 0:
            return torch.tensor(0.0, device=self.device, requires_grad=True)
            
        loss = loss.sum() / is_labeled.sum()

        return loss

    def train(self):
        train_loader, valid_loader, test_loader = self.dataset.get_data_loaders()

        self.normalizer = None
        if self.config["task_name"] in ['qm7', 'qm9']:
            labels = []
            for d, __ in train_loader:
                labels.append(d.y)
            labels = torch.cat(labels)
            self.normalizer = Normalizer(labels)
            print(self.normalizer.mean, self.normalizer.std, labels.shape)

        if self.config['model_type'] == 'gin':
            from models.ginet_finetune import GINet
            model = GINet(self.config['dataset']['task'], num_tasks=self.config['num_tasks'], **self.config["model"]).to(self.device)
            model = self._load_pre_trained_weights(model)
        elif self.config['model_type'] == 'gcn':
            from models.gcn_finetune import GCN
            model = GCN(self.config['dataset']['task'], num_tasks=self.config['num_tasks'], **self.config["model"]).to(self.device)
            model = self._load_pre_trained_weights(model)

        layer_list = []
        for name, param in model.named_parameters():
            if 'pred_head' in name:
                print(name, param.requires_grad)
                layer_list.append(name)

        params = list(map(lambda x: x[1],list(filter(lambda kv: kv[0] in layer_list, model.named_parameters()))))
        base_params = list(map(lambda x: x[1],list(filter(lambda kv: kv[0] not in layer_list, model.named_parameters()))))

        optimizer = torch.optim.Adam(
            [{'params': base_params, 'lr': self.config['init_base_lr']}, {'params': params}],
            self.config['init_lr'], weight_decay=eval(self.config['weight_decay'])
        )

        model_checkpoints_folder = os.path.join(self.writer.log_dir, 'checkpoints')

        # save config file
        _save_config_file(model_checkpoints_folder)

        n_iter = 0
        valid_n_iter = 0
        best_valid_loss = np.inf
        best_valid_rgr = np.inf  # This will store MAE for regression
        best_valid_cls = 0

        for epoch_counter in range(self.config['epochs']):
            for bn, data in enumerate(train_loader):
                optimizer.zero_grad()

                data = data.to(self.device)
                if self.config['fp16_precision']:
                    with autocast(device_type='cuda'):
                        loss = self._step(model, data, n_iter)
                    self.scaler.scale(loss).backward()
                    self.scaler.step(optimizer)
                    self.scaler.update()
                else:
                    loss = self._step(model, data, n_iter)
                    loss.backward()
                    optimizer.step()
                n_iter += 1

            # validate the model if requested
            if epoch_counter % self.config['eval_every_n_epochs'] == 0:
                if self.config['dataset']['task'] == 'classification': 
                    valid_loss, valid_metrics = self._validate(model, valid_loader)
                    current_metric = valid_metrics['roc_auc']
                    if current_metric > best_valid_cls:
                        # save the model weights
                        best_valid_cls = current_metric
                        torch.save(model.state_dict(), os.path.join(model_checkpoints_folder, 'model.pth'))
                        
                    # Early stopping check for classification
                    if current_metric > self.best_metric:
                        self.best_metric = current_metric
                        self.counter = 0
                    else:
                        self.counter += 1
                        if self.counter >= self.patience:
                            print(f"Early stopping at epoch {epoch_counter}")
                            self.early_stop = True
                            break
                elif self.config['dataset']['task'] == 'regression': 
                    valid_loss, valid_metrics = self._validate(model, valid_loader)
                    current_metric = valid_metrics['mae']  # Use MAE for model selection
                    if current_metric < best_valid_rgr:
                        # save the model weights
                        best_valid_rgr = current_metric
                        torch.save(model.state_dict(), os.path.join(model_checkpoints_folder, 'model.pth'))
                        
                    # Early stopping check for regression
                    if current_metric < self.best_metric:
                        self.best_metric = current_metric
                        self.counter = 0
                    else:
                        self.counter += 1
                        if self.counter >= self.patience:
                            print(f"Early stopping at epoch {epoch_counter}")
                            self.early_stop = True
                            break

                self.writer.add_scalar('validation_loss', valid_loss, global_step=valid_n_iter)
                valid_n_iter += 1
        
        self._test(model, test_loader)

    def _load_pre_trained_weights(self, model):
        try:
            checkpoints_folder = os.path.join('./ckpt', self.config['fine_tune_from'], 'checkpoints')
            state_dict = torch.load(os.path.join(checkpoints_folder, 'model.pth'), map_location=self.device)
            # model.load_state_dict(state_dict)
            model.load_my_state_dict(state_dict)
            print("Loaded pre-trained model with success.")
        except FileNotFoundError:
            print("Pre-trained weights not found. Training from scratch.")

        return model

    def _validate(self, model, valid_loader):
        predictions = []
        labels = []
        with torch.no_grad():
            model.eval()

            valid_loss = 0.0
            num_data = 0
            for bn, data in enumerate(valid_loader):
                data = data.to(self.device)

                __, pred = model(data)
                loss = self._step(model, data, bn)

                valid_loss += loss.item() * data.y.shape[0] # Use shape[0] for batch size
                num_data += data.y.shape[0]

                if self.normalizer:
                    pred = self.normalizer.denorm(pred)

                if self.config['dataset']['task'] == 'classification':
                    pred = torch.sigmoid(pred) # BCEWithLogitsLoss needs sigmoid for probs

                if self.device == 'cpu':
                    predictions.extend(pred.detach().numpy())
                    labels.extend(data.y.detach().numpy())
                else:
                    predictions.extend(pred.cpu().detach().numpy())
                    labels.extend(data.y.cpu().detach().numpy())

            valid_loss /= num_data
        
        model.train()

        if self.config['dataset']['task'] == 'regression':
            predictions = np.array(predictions)
            labels = np.array(labels)
            # Handle missing labels (marked with -1)
            is_labeled = (labels != -1)
            # Compute metric only on labeled data (average over tasks?)
            # Simplified: flatten and mask
            if self.config['task_name'] in ['qm7', 'qm8', 'qm9']:
                mae = mean_absolute_error(labels[is_labeled], predictions[is_labeled])
                print('Validation loss:', valid_loss, 'MAE:', mae)
                return valid_loss, {'mae': mae}
            else:
                rmse = root_mean_squared_error(labels[is_labeled], predictions[is_labeled])
                mae = mean_absolute_error(labels[is_labeled], predictions[is_labeled])
                print('Validation loss:', valid_loss, 'RMSE:', rmse, 'MAE:', mae)
                return valid_loss, {'rmse': rmse, 'mae': mae}

        elif self.config['dataset']['task'] == 'classification': 
            predictions = np.array(predictions)
            labels = np.array(labels)
            
            metrics = {}
            roc_auc_list = []
            precision_list = []
            recall_list = []
            f1_list = []
            balanced_acc_list = []
            
            for i in range(labels.shape[1]):
                # Mask missing labels (marked with -1) for this task
                task_labels = labels[:, i]
                task_preds = predictions[:, i]
                is_labeled = (task_labels != -1)
                if is_labeled.sum() > 0:
                    try:
                        # Convert probabilities to binary predictions
                        task_preds_binary = (task_preds > 0.5).astype(int)
                        
                        roc_auc_list.append(roc_auc_score(task_labels[is_labeled], task_preds[is_labeled]))
                        precision_list.append(precision_score(task_labels[is_labeled], task_preds_binary[is_labeled], zero_division=0))
                        recall_list.append(recall_score(task_labels[is_labeled], task_preds_binary[is_labeled], zero_division=0))
                        f1_list.append(f1_score(task_labels[is_labeled], task_preds_binary[is_labeled], zero_division=0))
                        balanced_acc_list.append(balanced_accuracy_score(task_labels[is_labeled], task_preds_binary[is_labeled]))
                    except ValueError:
                        pass # Handle cases with only one class
            
            metrics['roc_auc'] = np.mean(roc_auc_list) if roc_auc_list else 0.0
            metrics['precision'] = np.mean(precision_list) if precision_list else 0.0
            metrics['recall'] = np.mean(recall_list) if recall_list else 0.0
            metrics['f1'] = np.mean(f1_list) if f1_list else 0.0
            metrics['balanced_accuracy'] = np.mean(balanced_acc_list) if balanced_acc_list else 0.0
            
            print(f'Validation loss: {valid_loss:.4f}, ROC AUC: {metrics["roc_auc"]:.4f}, '
                  f'Precision: {metrics["precision"]:.4f}, Recall: {metrics["recall"]:.4f}, '
                  f'F1: {metrics["f1"]:.4f}, Balanced Acc: {metrics["balanced_accuracy"]:.4f}')
            return valid_loss, metrics

    def _test(self, model, test_loader):
        model_path = os.path.join(self.writer.log_dir, 'checkpoints', 'model.pth')
        state_dict = torch.load(model_path, map_location=self.device)
        model.load_state_dict(state_dict)
        print("Loaded trained model with success.")

        # test steps
        predictions = []
        labels = []
        with torch.no_grad():
            model.eval()

            test_loss = 0.0
            num_data = 0
            for bn, data in enumerate(test_loader):
                data = data.to(self.device)

                __, pred = model(data)
                loss = self._step(model, data, bn)

                test_loss += loss.item() * data.y.shape[0]
                num_data += data.y.shape[0]

                if self.normalizer:
                    pred = self.normalizer.denorm(pred)

                if self.config['dataset']['task'] == 'classification':
                    pred = torch.sigmoid(pred)

                if self.device == 'cpu':
                    predictions.extend(pred.detach().numpy())
                    labels.extend(data.y.detach().numpy())
                else:
                    predictions.extend(pred.cpu().detach().numpy())
                    labels.extend(data.y.cpu().detach().numpy())

            test_loss /= num_data
        
        model.train()

        if self.config['dataset']['task'] == 'regression':
            predictions = np.array(predictions)
            labels = np.array(labels)
            is_labeled = (labels != -1)
            if self.config['task_name'] in ['qm7', 'qm8', 'qm9']:
                self.mae = mean_absolute_error(labels[is_labeled], predictions[is_labeled])
                print('Test loss:', test_loss, 'Test MAE:', self.mae)
                return self.mae
            else:
                self.rmse = root_mean_squared_error(labels[is_labeled], predictions[is_labeled])
                self.mae = mean_absolute_error(labels[is_labeled], predictions[is_labeled])
                print('Test loss:', test_loss, 'Test RMSE:', self.rmse, 'Test MAE:', self.mae)
                return self.rmse

        elif self.config['dataset']['task'] == 'classification': 
            predictions = np.array(predictions)
            labels = np.array(labels)
            
            metrics = {}
            roc_auc_list = []
            precision_list = []
            recall_list = []
            f1_list = []
            balanced_acc_list = []
            
            for i in range(labels.shape[1]):
                task_labels = labels[:, i]
                task_preds = predictions[:, i]
                is_labeled = (task_labels != -1)
                if is_labeled.sum() > 0:
                    try:
                        # Convert probabilities to binary predictions
                        task_preds_binary = (task_preds > 0.5).astype(int)
                        
                        roc_auc_list.append(roc_auc_score(task_labels[is_labeled], task_preds[is_labeled]))
                        precision_list.append(precision_score(task_labels[is_labeled], task_preds_binary[is_labeled], zero_division=0))
                        recall_list.append(recall_score(task_labels[is_labeled], task_preds_binary[is_labeled], zero_division=0))
                        f1_list.append(f1_score(task_labels[is_labeled], task_preds_binary[is_labeled], zero_division=0))
                        balanced_acc_list.append(balanced_accuracy_score(task_labels[is_labeled], task_preds_binary[is_labeled]))
                    except ValueError:
                        pass
            
            self.roc_auc = np.mean(roc_auc_list) if roc_auc_list else 0.0
            self.precision = np.mean(precision_list) if precision_list else 0.0
            self.recall = np.mean(recall_list) if recall_list else 0.0
            self.f1 = np.mean(f1_list) if f1_list else 0.0
            self.balanced_accuracy = np.mean(balanced_acc_list) if balanced_acc_list else 0.0
            
            print(f'Test loss: {test_loss:.4f}, Test ROC AUC: {self.roc_auc:.4f}, '
                  f'Precision: {self.precision:.4f}, Recall: {self.recall:.4f}, '
                  f'F1: {self.f1:.4f}, Balanced Acc: {self.balanced_accuracy:.4f}')
            return self.roc_auc


def main(config):
    dataset = MolTestDatasetWrapper(config['batch_size'], **config['dataset'])

    fine_tune = FineTune(dataset, config)
    fine_tune.train()
    
    if config['dataset']['task'] == 'classification':
        return fine_tune.roc_auc
    if config['dataset']['task'] == 'regression':
        if config['task_name'] in ['qm7', 'qm8', 'qm9']:
            return fine_tune.mae
        else:
            return fine_tune.rmse


if __name__ == "__main__":
    config = yaml.load(open("config_finetune.yaml", "r"), Loader=yaml.FullLoader)

    # Check if Optuna optimization is requested
    if config.get('use_optuna', False):
        if OPTUNA_AVAILABLE:
            print("🔍 Optuna optimization enabled. Running hyperparameter search...")
            import subprocess
            result = subprocess.run([
                sys.executable, 'optuna_optimization.py',
                '--config', 'config_finetune.yaml',
                '--trials', str(config.get('optuna_trials', 20))
            ], capture_output=True, text=True)

            print(result.stdout)
            if result.stderr:
                print("Errors:", result.stderr)

            # Load best config and continue with normal training
            best_config_file = f'config_finetune_optuna_best_{config["task_name"].lower()}.yaml'
            if os.path.exists(best_config_file):
                print(f"✅ Loading best configuration from {best_config_file}")
                config = yaml.load(open(best_config_file, "r"), Loader=yaml.FullLoader)
            else:
                print("⚠️  Best config not found, continuing with original config")
        else:
            print("⚠️  Optuna requested but not available. Install with: pip install optuna")
            print("Continuing with normal training...")

    # Continue with normal training logic...

    if config['task_name'] == 'BBBP':
        config['dataset']['task'] = 'classification'
        config['dataset']['data_path'] = 'data/BBBP/BBBP.csv'
        target_list = ["p_np"]

    elif config['task_name'] == 'Tox21':
        config['dataset']['task'] = 'classification'
        config['dataset']['data_path'] = 'data/tox21/tox21.csv'
        target_list = [
            "NR-AR", "NR-AR-LBD", "NR-AhR", "NR-Aromatase", "NR-ER", "NR-ER-LBD", 
            "NR-PPAR-gamma", "SR-ARE", "SR-ATAD5", "SR-HSE", "SR-MMP", "SR-p53"
        ]

    elif config['task_name'] == 'ClinTox':
        config['dataset']['task'] = 'classification'
        config['dataset']['data_path'] = 'data/clintox/clintox.csv'
        target_list = ['CT_TOX', 'FDA_APPROVED']

    elif config['task_name'] == 'HIV':
        config['dataset']['task'] = 'classification'
        config['dataset']['data_path'] = 'data/hiv/HIV.csv'
        target_list = ["HIV_active"]

    elif config['task_name'] == 'BACE':
        config['dataset']['task'] = 'classification'
        config['dataset']['data_path'] = 'data/bace/bace.csv'
        target_list = ["Class"]

    elif config['task_name'] == 'SIDER':
        config['dataset']['task'] = 'classification'
        config['dataset']['data_path'] = 'data/sider/sider.csv'
        target_list = [
            "Hepatobiliary disorders", "Metabolism and nutrition disorders", "Product issues", 
            "Eye disorders", "Investigations", "Musculoskeletal and connective tissue disorders", 
            "Gastrointestinal disorders", "Social circumstances", "Immune system disorders", 
            "Reproductive system and breast disorders", 
            "Neoplasms benign, malignant and unspecified (incl cysts and polyps)", 
            "General disorders and administration site conditions", "Endocrine disorders", 
            "Surgical and medical procedures", "Vascular disorders", 
            "Blood and lymphatic system disorders", "Skin and subcutaneous tissue disorders", 
            "Congenital, familial and genetic disorders", "Infections and infestations", 
            "Respiratory, thoracic and mediastinal disorders", "Psychiatric disorders", 
            "Renal and urinary disorders", "Pregnancy, puerperium and perinatal conditions", 
            "Ear and labyrinth disorders", "Cardiac disorders", 
            "Nervous system disorders", "Injury, poisoning and procedural complications"
        ]
    
    elif config['task_name'] == 'MUV':
        config['dataset']['task'] = 'classification'
        config['dataset']['data_path'] = 'data/muv/muv.csv'
        target_list = [
            'MUV-692', 'MUV-689', 'MUV-846', 'MUV-859', 'MUV-644', 'MUV-548', 'MUV-852',
            'MUV-600', 'MUV-810', 'MUV-712', 'MUV-737', 'MUV-858', 'MUV-713', 'MUV-733',
            'MUV-652', 'MUV-466', 'MUV-832'
        ]

    elif config["task_name"] == 'caco2':
        config['dataset']['task'] = 'regression'
        config['dataset']['data_path'] = 'data/caco2/caco2.csv'
        target_list = ["Y"]
    
    elif config["task_name"] == 'clearance':
        config['dataset']['task'] = 'regression'
        config['dataset']['data_path'] = 'data/clearance/clearance_hepatocyte_log.csv'
        target_list = ["clearance_hepatocyte_az"]
    
    elif config["task_name"] == 'HLM_CLint':
        config['dataset']['task'] = 'regression'
        config['dataset']['data_path'] = 'data/HLM_CLint/LOG_HLM_CLint.csv'
        target_list = ["LOG HLM_CLint (mL/min/kg)"]
    
    elif config["task_name"] == 'tox21':
        config['dataset']['task'] = 'classification'
        config['dataset']['data_path'] = 'data/tox21/tox21.csv'
        target_list = [
            "NR-AR", "NR-AR-LBD", "NR-AhR", "NR-Aromatase", "NR-ER", "NR-ER-LBD", 
            "NR-PPAR-gamma", "SR-ARE", "SR-ATAD5", "SR-HSE", "SR-MMP", "SR-p53"
        ]
    
    elif config["task_name"] == 'ESOL':
        config['dataset']['task'] = 'regression'
        config['dataset']['data_path'] = 'data/esol/esol.csv'
        target_list = ["measured log solubility in mols per litre"]

    elif config["task_name"] == 'Lipo':
        config['dataset']['task'] = 'regression'
        config['dataset']['data_path'] = 'data/lipophilicity/Lipophilicity.csv'
        target_list = ["exp"]
    
    elif config["task_name"] == 'qm7':
        config['dataset']['task'] = 'regression'
        config['dataset']['data_path'] = 'data/qm7/qm7.csv'
        target_list = ["u0_atom"]

    elif config["task_name"] == 'qm8':
        config['dataset']['task'] = 'regression'
        config['dataset']['data_path'] = 'data/qm8/qm8.csv'
        target_list = [
            "E1-CC2", "E2-CC2", "f1-CC2", "f2-CC2", "E1-PBE0", "E2-PBE0", 
            "f1-PBE0", "f2-PBE0", "E1-CAM", "E2-CAM", "f1-CAM","f2-CAM"
        ]
    
    elif config["task_name"] == 'qm9':
        config['dataset']['task'] = 'regression'
        config['dataset']['data_path'] = 'data/qm9/qm9.csv'
        target_list = ['mu', 'alpha', 'homo', 'lumo', 'gap', 'r2', 'zpve', 'cv']

    else:
        raise ValueError('Undefined downstream task!')

    config['num_tasks'] = len(target_list) # Set num_tasks for model initialization
    print(config)

    # Pass all targets at once
    config['dataset']['target'] = target_list
    result = main(config)

    os.makedirs('experiments', exist_ok=True)
    df = pd.DataFrame([[config['task_name'], result]])
    df.to_csv(
        'experiments/{}_{}_finetune.csv'.format(config['fine_tune_from'], config['task_name']), 
        mode='a', index=False, header=False
    )