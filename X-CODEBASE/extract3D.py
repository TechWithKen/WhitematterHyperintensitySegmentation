import os
import nibabel as nib
import numpy as np
from skimage import measure

# --- 1. CONFIGURATION ---
parent_dir = "/Users/alert/Downloads/WMH_EXPERIMENT_UTRECHT/SPM_UTRECHT/FLAIR"

def create_obj_from_nifti(nifti_path, output_obj_path):
    """
    Converts NIfTI to OBJ with enhanced cleaning to prevent Blender spikes.
    """
    try:
        # Load the NIfTI
        img = nib.load(nifti_path)
        data = img.get_fdata()
        
        if np.max(data) <= 0:
            print(f"  ⚠️ Skipping {os.path.basename(nifti_path)}: Empty mask.")
            return
        
        # --- PADDING FIX ---
        padded_data = np.pad(data, pad_width=1, mode='constant', constant_values=0)
        
        # Adjust spacing from header
        spacing = img.header.get_zooms()[:3]
        
        # Run Marching Cubes on the PADDED data
        verts, faces, normals, values = measure.marching_cubes(
            padded_data, level=0.5, spacing=spacing
        )
        
        # Subtract the 1-voxel padding from the vertices to maintain alignment
        verts -= spacing
        
        # --- NEW: REMOVE VERTICES NEAR ORIGIN ---
        # Calculate the center of mass of the mesh
        center = np.mean(verts, axis=0)
        
        # Find vertices that are suspiciously close to origin (0,0,0)
        # and far from the center of mass
        distances_from_origin = np.linalg.norm(verts, axis=1)
        distances_from_center = np.linalg.norm(verts - center, axis=1)
        
        # Threshold: vertices within 5mm of origin AND far from center are likely artifacts
        origin_threshold = 5.0  # mm
        outlier_vertices = (distances_from_origin < origin_threshold) & \
                          (distances_from_center > np.percentile(distances_from_center, 95))
        
        # Create a mask of valid vertices
        valid_vertices = ~outlier_vertices
        
        # Create a mapping from old vertex indices to new ones
        vertex_map = np.cumsum(valid_vertices) - 1
        vertex_map[~valid_vertices] = -1
        
        # Filter vertices
        clean_verts = verts[valid_vertices]
        
        # Filter faces: keep only faces where all vertices are valid
        valid_faces = []
        for face in faces:
            if all(valid_vertices[face]):
                new_face = [vertex_map[i] for i in face]
                valid_faces.append(new_face)
        
        clean_faces = np.array(valid_faces)
        
        print(f"  🧹 Removed {np.sum(outlier_vertices)} outlier vertices near origin")
        
        # Write to OBJ
        with open(output_obj_path, 'w') as f:
            f.write("# Clean 3D Mesh - No Spikes\n")
            for v in clean_verts:
                f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
            for face in clean_faces:
                f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")
        
        print(f"  ✅ Saved Clean Mesh: {os.path.basename(output_obj_path)}")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")

# --- 2. BATCH LOOP ---
print(f"🚀 Processing: {parent_dir}")
for folder in os.listdir(parent_dir):
    folder_path = os.path.join(parent_dir, folder)
    if os.path.isdir(folder_path):
        # Processing files starting with ples_lpa
        target_files = [f for f in os.listdir(folder_path) 
                       if f.startswith("wmh") and f.endswith(".nii")]
        
        for filename in target_files:
            input_p = os.path.join(folder_path, filename)
            output_p = os.path.join(folder_path, filename.replace(".nii", ".obj"))
            create_obj_from_nifti(input_p, output_p)

print("\n🎉 Done! These files should now be clean when imported into Blender.")