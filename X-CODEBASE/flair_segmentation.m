% Initialize SPM
spm('defaults', 'fmri');
spm_jobman('initcfg');

% 1. Define Root Directory - DOUBLE CHECK THIS PATH
baseDir = '/Users/alert/Downloads/WMH_EXPERIMENT_UTRECHT/SPM_UTRECHT/FLAIR';

% 2. Get list of all UTRECHT_* folders
subFolders = dir(fullfile(baseDir, 'UTR_*'));

% Safety Check
if isempty(subFolders)
    error('No UTRECHT folders found! Check your baseDir path.');
end

for i = 1:length(subFolders)
    subName = subFolders(i).name;
    subPath = fullfile(baseDir, subName);
    t 
    % Find the .nii file (FLAIR)
    niiFiles = dir(fullfile(subPath, '*.nii'));
    
    if ~isempty(niiFiles)
        targetFile = fullfile(subPath, [niiFiles(1).name, ',1']);
        fprintf('\n=== PROCESSING: %s ===\n', subName);
        
        clear matlabbatch;
        
        % --- MODULE 1: SPM SEGMENTATION (The Tissue Fix) ---
        matlabbatch{1}.spm.spatial.preproc.channel.vols = {targetFile};
        matlabbatch{1}.spm.spatial.preproc.channel.biasreg = 0.0001;
        matlabbatch{1}.spm.spatial.preproc.channel.biasfwhm = 60;
        matlabbatch{1}.spm.spatial.preproc.channel.write = [1 1]; % Writes bias-corrected image
        
        % Tissue Probability Map path
        tpmPath = '/Users/alert/Documents/MATLAB/spm/tpm/TPM.nii';
        
        % Set up the 6 tissue classes
        ngaus_vals = [1 1 2 3 4 2];
        for t = 1:6
            matlabbatch{1}.spm.spatial.preproc.tissue(t).tpm = {[tpmPath, ',', num2str(t)]};
            matlabbatch{1}.spm.spatial.preproc.tissue(t).ngaus = ngaus_vals(t);
            % Class 1 (GM), 2 (WM), 3 (CSF) are set to save in native space [1 0]
            if t <= 3
                matlabbatch{1}.spm.spatial.preproc.tissue(t).native = [1 0]; 
            else
                matlabbatch{1}.spm.spatial.preproc.tissue(t).native = [0 0];
            end
            matlabbatch{1}.spm.spatial.preproc.tissue(t).warped = [0 0];
        end
        
        matlabbatch{1}.spm.spatial.preproc.warp.mrf = 1;
        matlabbatch{1}.spm.spatial.preproc.warp.cleanup = 1;
        matlabbatch{1}.spm.spatial.preproc.warp.reg = [0 0 0.1 0.01 0.04];
        matlabbatch{1}.spm.spatial.preproc.warp.affreg = 'mni';
        matlabbatch{1}.spm.spatial.preproc.warp.samp = 3;
        matlabbatch{1}.spm.spatial.preproc.warp.write = [0 0];

        % --- MODULE 2: LST LPA (The Lesion & HTML Fix) ---
        matlabbatch{2}.spm.tools.LST.lpa.data_F2 = {targetFile};
        matlabbatch{2}.spm.tools.LST.lpa.data_coreg = {''};
        matlabbatch{2}.spm.tools.LST.lpa.html_report = 1; % Force the HTML summary

        % Run the job
        try
            spm_jobman('run', matlabbatch);
            fprintf('SUCCESS: %s processed. Check folder for c1, c2, c3 and HTML.\n', subName);
        catch ME
            fprintf('FAILED: %s - Error: %s\n', subName, ME.message);
        end
        
    else
        fprintf('SKIPPED: %s - No .nii file found.\n', subName);
    end
end
fprintf('\n--- ALL SUBJECTS FINISHED ---\n');