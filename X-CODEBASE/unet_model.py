import os
import torch
import nibabel as nib
import numpy as np
from monai.networks.nets import SegResNet
from monai.inferers import sliding_window_inference
from monai.transforms import (
    Compose, LoadImaged, EnsureChannelFirstd, 
    Orientationd, ScaleIntensityd, EnsureTyped
)

# --- 1. CONFIGURATION ---
data_dir = "/Users/alert/Downloads/WMH-EXPERIMENTS/U_NET_UTRETCH"
weights_path = "/Users/alert/Downloads/WMH-EXPERIMENTS/huggingface/hub/models--MONAI--brats_mri_segmentation/snapshots/370f7f9d062745fbac445e7fe6d6616d35df04ec/models/model.pt"

device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(f"Using device: {device}")

# --- 2. MODEL SETUP ---
model = SegResNet(
    spatial_dims=3,
    init_filters=16,      
    in_channels=4,        
    out_channels=3, # Note: BraTS models often output 3 channels (TC, WT, ET) directly
).to(device)

if os.path.exists(weights_path):
    model.load_state_dict(torch.load(weights_path, map_location=device))
    print("✅ Weights loaded successfully!")
else:
    print("❌ Weights not found!")
    exit()

model.eval()

# --- 3. PIPELINE ---
transforms = Compose([
    LoadImaged(keys=["image"]),
    EnsureChannelFirstd(keys=["image"]),
    Orientationd(keys=["image"], axcodes="RAS"),
    ScaleIntensityd(keys=["image"]),
    EnsureTyped(keys=["image"]),
])

# --- 4. INFERENCE LOOP ---
subfolders = [f for f in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, f))]

with torch.no_grad():
    for folder in subfolders:
        folder_path = os.path.join(data_dir, folder)
        nii_files = [f for f in os.listdir(folder_path) if (f.endswith('.nii') or f.endswith('.nii.gz')) and not f.startswith('monai')]
        
        if not nii_files: continue
        
        image_path = os.path.join(folder_path, nii_files[0])
        data = transforms({"image": image_path})
        
        # Stacking Hack
        flair_tensor = data["image"]
        stacked_input = torch.cat([flair_tensor] * 4, dim=0).unsqueeze(0).to(device)

        # Sliding Window
        output = sliding_window_inference(stacked_input, (96, 96, 96), 4, model)
        
        # --- NEW LOGIC: CHANNEL SELECTION ---
        # Instead of argmax (which picks background), we apply Sigmoid to see the probabilities
        # We then take the "Whole Tumor" logic: where ANY lesion channel is high.
        probabilities = torch.sigmoid(output[0]) 
        
        # Let's create a combined mask of all lesion labels
        # We take the max probability across the 3 channels
        combined_prob, _ = torch.max(probabilities, dim=0)
        
        # Create a binary mask where probability > 0.5
        final_mask = (combined_prob > 0.5).cpu().numpy()

        # Save
        orig_img = nib.load(image_path)
        output_nifti = nib.Nifti1Image(final_mask.astype(np.float32), orig_img.affine, orig_img.header)
        
        output_name = "monai_seg_brats.nii.gz"
        nib.save(output_nifti, os.path.join(folder_path, output_name))
        print(f"✅ Processed: {folder} | Lesion voxels found: {np.sum(final_mask)}")

print("\nDone! Check your folders for the new masks.")