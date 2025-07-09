%% Init
close all;
clear; clc;

% Paths
dataCNDFolder = '.\outputs\CND\';
dataStimFolder = '.\outputs\features\';

% Add other directories to path
addpath ..\..\MATLAB\cnsp_utils
addpath ..\..\MATLAB\cnsp_utils\cnd

%% General parameters
subjects = {'mb_Aaron', 'QinyuChen', 'Chang'};
fs_down = 100;
NTRIALS = 10;
feature_names = {'trail_pos', ' steering11', 'error'};
additionalDetails = {'trail_pos', ' steering11', 'error'};
% feat2transpose = {'DREX_f0_surprisal', };

%% Generate data stim for each condition
for idxSbj = 1:length(subjects)
    subject = subjects{idxSbj};
    disp(['Processing subject ', subject])
    curr_path = [dataStimFolder,'\',subject,'\'];
    stim_file_names = dir([curr_path,'*.mat']);

    stim = struct();
    stim.fs = fs_down;
    stim.subject = idxSbj;
    for idx_stim = 1:NTRIALS
        for idx_feat = 1:length(feature_names)
            feature_name = feature_names{idx_feat};
            disp(feature_name)
            disp(num2str(idx_stim))
            disp(curr_path)
            
            stim.names{idx_feat} = feature_name;
            stim.additionalDetails{idx_feat} = additionalDetails{idx_feat};

            stim_path = [curr_path, num2str(idx_stim), '_' feature_name, '.mat'];

            % Save feature data in cell array
            load(stim_path,'feature')
            stim.data{idx_feat, idx_stim} = feature';
        end

    end

    curr_folder = [dataCNDFolder, '/feature/', num2str(idxSbj)];
    if ~exist(curr_folder, 'dir')
        % Create the folder
        mkdir(curr_folder);
        disp('Folder created successfully.');
    else
        disp('Folder already exists.');
    end

    outputFilename = [curr_folder, '/dataStim.mat'];
    disp(['Saving data stim for subject ', subject])
    save(outputFilename,'stim')
end
 
