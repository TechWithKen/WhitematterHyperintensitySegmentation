import trimesh
import numpy as np
import pandas as pd
import time
import glob
import os


def calculate_final_metrics_optimized(obj_path, pitch=0.8):
    try:
        mesh = trimesh.load(obj_path)
        
        # 1. Solid Reconstruction (Critical for non-watertight/broken meshes)
        voxels = mesh.voxelized(pitch=pitch).fill()
        solid_mesh = voxels.marching_cubes
        
        volume = float(solid_mesh.volume)
        area = float(solid_mesh.area)
        
        if volume <= 0:
            return None

        # --- THE 10 MEASUREMENTS ---

        # 1. Volume & 2. Surface Area
        # Done.

        # 3. Sphericity
        sphericity = (np.pi**(1/3) * (6 * volume)**(2/3)) / area

        # 4. Fractal Dimension
        points = solid_mesh.vertices
        points_norm = points - points.min(axis=0)
        max_dim = points_norm.max()
        scales = np.logspace(0, np.log10(max_dim / 2), num=12)
        counts = [len(np.unique(np.floor(points_norm / s).astype(np.int32), axis=0)) for s in scales]
        fd_slope, _ = np.polyfit(np.log(1/scales), np.log(counts), 1)
        fractal_dim = abs(fd_slope)

        # 5. Surface-to-Volume Ratio (SAVR)
        savr = area / volume

        # 6. Compactness
        compactness = volume / solid_mesh.bounding_box.volume

        # 7. Convexity (Solidity)
        convexity = volume / solid_mesh.convex_hull.volume

        # 8. Elongation
        bb_extents = solid_mesh.bounding_box.extents
        elongation = max(bb_extents) / min(bb_extents)

        # 9. Radial Distance Variance
        center = solid_mesh.center_mass
        distances = np.linalg.norm(solid_mesh.vertices - center, axis=1)
        radial_variance = np.var(distances) / (np.mean(distances)**2)

        # 10. Tortuosity (Area normalized by bounding box diagonal)
        max_dist = np.linalg.norm(bb_extents)
        tortuosity = area / (max_dist**2)

        return {
            "Subject": obj_path.split('/')[-2],
            "Vol_mm3": round(volume, 2),
            "Area_mm2": round(area, 2),
            "Sphericity": round(float(min(1.0, sphericity)), 4),
            "Fractal_Dim": round(float(fractal_dim), 4),
            "SAVR": round(float(savr), 4),
            "Compactness": round(float(compactness), 4),
            "Convexity": round(float(convexity), 4),
            "Elongation": round(float(elongation), 4),
            "Radial_Var": round(float(radial_variance), 4),
            "Tortuosity": round(float(tortuosity), 4)
        }
    except Exception as e:
        print(f"Error processing {obj_path}: {e}")
        return None


BASE_DIR = "/Users/alert/Downloads/WMH_EXPERIMENT_UTRECHT/SPM_UTRECHT/FLAIR"
subject_folders = sorted(glob.glob(os.path.join(BASE_DIR, "UTR_*")))

files = []
for folder in subject_folders:
    
    files.append(glob.glob(os.path.join(folder, "ples_lpa_*.obj"))[0])

results_list = []

for subject_id, subjects in enumerate(files):
    print(f"Processing Subject {subject_id}...")
    metrics = calculate_final_metrics_optimized(subjects)
    if metrics:
        results_list.append(metrics)

# 2. CONVERT TO CLEAN DATAFRAME
df = pd.DataFrame(results_list)

# 3. DISPLAY RESULTS (Clean and without np.float wrappers)
print("\n--- FINAL LGA MORPHOMETRIC RESULTS ---")
print(df.to_string(index=False))

# Optional: Save to CSV for your paper
df.to_csv("UTRECHT_LPA_Morphometrics.csv", index=False)