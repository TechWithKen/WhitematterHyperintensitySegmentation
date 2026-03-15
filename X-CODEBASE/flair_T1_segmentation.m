% Initialize SPM
spm('defaults', 'fmri');
spm_jobman('initcfg');

% 1. Define the root directory
baseDir = '/Users/alert/Downloads/WMH_EXPERIMENT_UTRECHT/SPM_UTRECHT/T1_FLAIR';

% 2. Get a list of all subject folders (UTRECHT_01, UTRECHT_02, etc.)
subFolders = dir(fullfile(baseDir, 'UTRECHT_*'));

% 3. Loop through each folder
for i = 1:length(subFolders)
    subName = subFolders(i).name;
    subPath = fullfile(baseDir, subName, 'T1_FLAIR');
    
    fprintf('Processing: %s\n', subName);
    
    % Construct the file paths
    % Note: LST expects the ',1' suffix for NIfTI volumes
    t1File = fullfile(subPath, 'T1.nii,1');
    flairFile = fullfile(subPath, [subName, '.nii,1']); % Matches UTRECHT_xx.nii
    
    % Check if files exist before trying to run
    if exist(fullfile(subPath, 'T1.nii'), 'file') && exist(fullfile(subPath, [subName, '.nii']), 'file')
        
        clear matlabbatch; % Clear previous subject's job
        
        % Define the Job for this specific subject
        matlabbatch{1}.spm.tools.LST.lga.data_T1 = {t1File};
        matlabbatch{1}.spm.tools.LST.lga.data_F2 = {flairFile};
        
        % Set Parameters (Kappa = 0.3 or 0.4 usually works best)
        matlabbatch{1}.spm.tools.LST.lga.opts_lga.initial = 0.4; % Set Kappa directly here
        matlabbatch{1}.spm.tools.LST.lga.opts_lga.mrf = 1;
        matlabbatch{1}.spm.tools.LST.lga.opts_lga.maxiter = 50;
        matlabbatch{1}.spm.tools.LST.lga.html_report = 1;
        
        % RUN the job
        try
            spm_jobman('run', matlabbatch);
        catch ME
            fprintf('Error processing %s: %s\n', subName, ME.message);
        end
        
    else
        fprintf('Skipping %s: Files not found.\n', subName);
    end
end

fprintf('Batch processing complete!\n');

