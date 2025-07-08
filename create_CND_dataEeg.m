%% Generate CND files from data segmented and preprocessed in Python
%% Do bad channel rejection here as opposed to Python

%% Init
close all;
clear; clc;

% Add other directories to path
addpath ..\..\MATLAB\cnsp_utils
addpath ..\..\MATLAB\cnsp_utils\cnd
addpath ..\..\MATLAB\NoiseTools
addpath ..\..\MATLAB\eeglab

%% Parameters preprocessing
dataEegFolder = '.\outputs\EEG\seg&pre\';
dataCNDFolder = '.\outputs\CND\';
pre = '1-8Hz';
reref_type = 'Average';
downfreq = 100;

%% General parameters
subjects = {'mb_Aaron', 'QinyuChen', 'Chang'};
dataType = 'EEG';
deviceName = 'CGX';
chanlocs = load([dataCNDFolder, 'chanlocs32.mat']).chanlocs;

for idxSbj = 1:length(subjects)
    subject = subjects{idxSbj};
    disp(['Processing subject ', subject])
    curr_path = [dataEegFolder,pre,'\',reref_type,'\',subject,'\'];

    % Get preprocessing pipeline from csv
    T = readtable([curr_path, 'preprocessing_pipeline.csv']);
    preprocessingPipeline = {['LPF ', T.LPF, 'Hz'], ... 
                            ['HPF ', T.HPF, 'Hz'], ...
                            ['Reref ', T.reref_type], ...
                            ['Down ', downfreq, 'Hz']};

    % Create data struct for this subject
    eeg = struct();
    eeg.dataType = dataType;
    eeg.deviceName = deviceName;
    eeg.chanlocs = chanlocs;
    eeg.extChan{1,1} = struct('description', 'EMG', 'chanlocs', []);
    eeg.fs = downfreq;
    eeg.reRef = T.reref_type;
    eeg.preprocessingPipeline = preprocessingPipeline;
    
    % Fill data structure with trials
    trial_names = dir([curr_path,'\','*.mat']);
    for idxTrial = 1:length(trial_names)
        stim_path = trial_names(idxTrial).name;
        load([curr_path,'\',stim_path]);
        eeg.data{idxTrial} = trial_data';
        eeg.extChan{1,1}.data{idxTrial} = trial_emg';
    end

    % Saving preprocessed data
    eegFolder = [dataCNDFolder, '\', pre, '\', reref_type];
    mkdir(eegFolder)
    eegPreFilename = [eegFolder, '\pre_dataSub', num2str(idxSbj), '.mat'];
    disp(['Saving preprocessed EEG data of subject ' num2str(idxSbj)])
    save(eegPreFilename,'eeg');

end

disp('Done!')