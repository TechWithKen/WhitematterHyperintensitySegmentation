import torch
import nibabel as nib
import numpy as np
import pandas as pd
import os
import glob
from monai.metrics import DiceMetric, HausdorffDistanceMetric, MeanIoU, ConfusionMatrixMetric

# --- CONFIGURATION ---
BASE_DIR = "/Users/alert/Downloads/WMH_EXPERIMENT_UTRECHT/SPM_UTRECHT/T1_FLAIR"

def load_and_preprocess(path, is_manual=False):
    """Loads NIfTI and returns a binarized 5D Torch Tensor."""
    img = nib.load(path)
    data = img.get_fdata()
    
    if is_manual:
        # STRIVE Criteria: Isolate WMH (Label 1)
        binary = (np.round(data) == 1).astype(np.float32)
    else:
        # Threshold probabilistic output at 0.5
        binary = (data > 0.5).astype(np.float32)
    
    return torch.from_numpy(binary).unsqueeze(0).unsqueeze(0)

def calculate_all_metrics(y_pred, y_true):
    """Calculates a full suite of medical imaging metrics."""
    dice_func = DiceMetric(include_background=False, reduction="mean")
    iou_func = MeanIoU(include_background=False, reduction="mean")
    hd95_func = HausdorffDistanceMetric(include_background=False, percentile=95)
    conf_matrix_func = ConfusionMatrixMetric(
        include_background=False, 
        metric_name=["precision", "sensitivity"], 
        reduction="mean"
    )

    dice_func(y_pred=y_pred, y=y_true)
    iou_func(y_pred=y_pred, y=y_true)
    hd95_func(y_pred=y_pred, y=y_true)
    conf_matrix_func(y_pred=y_pred, y=y_true)

    conf = conf_matrix_func.aggregate()
    
    return {
        "Dice": dice_func.aggregate().item(),
        "IoU": iou_func.aggregate().item(),
        "HD95": hd95_func.aggregate().item(),
        "Precision": conf[0].item(),
        "Recall": conf[1].item(),
    }

# --- BATCH EXECUTION ---
results_list = []

# Get all subject folders (UTRECHT_01, UTRECHT_02, etc.)
subject_folders = sorted(glob.glob(os.path.join(BASE_DIR, "UTR_*")))

for folder in subject_folders:
    subject_id = os.path.basename(folder)
    print(f"🧐 Processing {subject_id}...")

    # Find the files
    # Note: Using wildcards to find 'ples_lga' because the Kappa value (0.09) might change
    pred_files = glob.glob(os.path.join(folder, "ples_lga_*.nii"))
    manual_files = glob.glob(os.path.join(folder, "wmh.nii")) # Adjust if inside T1_FLAIR

    if not pred_files or not manual_files:
        print(f"⚠️ Skipping {subject_id}: Missing prediction or manual file.")
        continue


    try:
        # Load tensors
        y_pred = load_and_preprocess(pred_files[0], is_manual=False)
        y_true = load_and_preprocess(manual_files[0], is_manual=True)

        # Skip if one is empty (avoid NaN metrics)
        if torch.sum(y_pred) == 0 or torch.sum(y_true) == 0:
            print(f"❌ {subject_id} has an empty mask. Skipping.")
            continue

        # Calculate
        stats = calculate_all_metrics(y_pred, y_true)
        stats["Subject"] = subject_id
        results_list.append(stats)

    except Exception as e:
        print(f"🔥 Error processing {subject_id}: {e}")

# --- FINAL DATAFRAME ---
df = pd.DataFrame(results_list)

# Reorder columns to put Subject first
cols = ['Subject', 'Dice', 'IoU', 'HD95', 'Precision', 'Recall']
df = df[cols]

print("\n--- BATCH LPA EVALUATION COMPLETE ---")
print(df.to_string(index=False))

# Optional: Save for your paper
df.to_csv("Utrecht_LGA_Validation_Metrics.csv", index=False)