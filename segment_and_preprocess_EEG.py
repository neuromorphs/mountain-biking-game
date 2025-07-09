################
## Imports
################
import mne
import os
import glob
import numpy as np
import pandas as pd
from scipy.io import savemat
# import matplotlib.pyplot as plt

################
## Parameters
################
# General
# General
root_dir = "/mnt/c/Users/gcantisani/Documents/EEG_experiments/pygame-logitechG29_wheel/results/"
output_base = './outputs/EEG/seg&pre/'
output_feat = './outputs/features/'
os.makedirs(output_base, exist_ok=True)
os.makedirs(output_feat, exist_ok=True)

csv_pre = 'preprocessing_pipeline.csv'
FPS_feat = 100 # Hz	
NR_TRIALS = 10
duration_seconds = 120
plot = False
subjects_to_process = ['mb_Aaron', 'QinyuChen', 'Chang'] # , 'Chang' QinyuChen[]  # could save only trial 2, 3, 4, 6, 10 for Rej
trial_to_process = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] #[2, 3, 4, 6, 10]

# Preprocessing
# Notch filtering
notch_applied = True
freq_notch = 60

# Bandpass filtering
bpf_applied = True
bandpass = '1-8Hz'
freq_low   = 1
freq_high  = 8
ftype = 'butter'
order = 3

# Spherical interpolation
int_applied = False
interpolation = 'spline'

# Rereferencing using average of mastoids electrodes
reref_applied = False
reref_type = 'Average'  #Mastoids #Average

# Downsampling
down_applied = True
downfreq = FPS_feat

############################################################################
## Loop over .bdf recordings
############################################################################
# Find BioSemi files in root_dir and itrate over them
files = glob.glob(os.path.join(root_dir, '**', '*.bdf'), recursive=True) + \
        glob.glob(os.path.join(root_dir, '**', '*.vhdr'), recursive=True)
print(root_dir)
print(files)
# files = [file for file in files if subjects_to_process.any() in file]
for idx, file in enumerate(files):
    if file.split('/')[-1].split('.')[0] not in subjects_to_process:
        continue
    print(idx, file.split('/')[-1])

    # Select which file to open
    # idx_file_to_open = input('Enter idx of subject to open: ')
    # file_to_open = files[int(idx_file_to_open)]
    file_to_open = file

    # Create output folder
    name_subject = file_to_open.split('/')[-1].split('.')[0]
    output_dir = os.path.join(output_base, bandpass, reref_type, name_subject)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Create file that keeps track of the preprocessing
    df_pre = pd.DataFrame()

    ############################################################################
    ## Load EEG data
    ############################################################################
    # Load raw
    if '.bdf' in file_to_open:
        raw = mne.io.read_raw_bdf(file_to_open, eog=None, misc=None, stim_channel='auto', 
                                infer_types=False, preload=False, verbose=None)
        N_start_events = mne.find_events(raw)
        N_start_events = N_start_events[N_start_events[:, 2] == 32768]
        N_start_events = N_start_events[:len(trial_to_process), 0]
    elif '.vhdr' in file_to_open:
        raw = mne.io.read_raw_brainvision(vhdr_fname=file_to_open, preload=False, verbose=None)
        N_start_events = mne.events_from_annotations(raw)
        N_start_events = N_start_events[0][N_start_events[0][:, 2] == 10001]
        N_start_events = N_start_events[1:-2, 0]

    print(raw)
    raw.load_data()

    # Check metadata
    n_time_samps = raw.n_times
    time_secs = raw.times
    ch_names = raw.ch_names
    n_chan = len(ch_names) 
    print('the (cropped) sample data object has {} time samples and {} channels.'
        ''.format(n_time_samps, n_chan))
    print('The last time sample is at {} seconds.'.format(time_secs[-1]))
    print('The first few channel names are {}.'.format(', '.join(ch_names[:3])))
    print('bad channels:', raw.info['bads'])  # chs marked "bad" during acquisition
    print(raw.info['sfreq'], 'Hz')            # sampling frequency
    print(raw.info['description'], '\n')      # miscellaneous acquisition info
    print(raw.info)
    if plot:
        raw.plot(start=100, duration=10)

    ############################################################################
    ## Find events in trigger channel
    ############################################################################
    # # Find starting sample of events in the trigger channel

    # # Select only relevant events
    # N_start_events = N_start_events[N_start_events[:, 2] == 32768]
    # # N_start_events = N_start_events[0][N_start_events[0][:, 2] == 10001]

    # # Get starting samples of events
    # N_start_events = N_start_events[:len(trial_to_process), 0]
    # # N_start_events = N_start_events[1:-2, 0]

    # Get corresponding time
    T_start_events = N_start_events / raw.info['sfreq']

    # Check there are as many triggers as the listened stimuli
    assert len(N_start_events) == len(trial_to_process)

    ############################################################################
    ## Segment and then process EEG data
    ############################################################################
    print(N_start_events)
    for idx_trial, name_trial in enumerate(trial_to_process):
        print(idx_trial, name_trial) 

        ###############################
        ## Get features
        ###############################
        df_feat = pd.read_csv(os.path.join(root_dir, name_subject, name_subject + '_trial_' + str(name_trial) + '.csv'), skiprows=1, encoding = "ISO-8859-1", low_memory=False)
        print(df_feat.keys())
        times = df_feat['time(s)'].values
        time0 = times[0]
        sample0 = int(time0/FPS_feat)
        samples = np.array([int(t)*FPS_feat for t in times])
        print(samples[0], samples[-1])
        print(times[0], times[-1])
        print(time0, sample0)

        curr_feat_dir = os.path.join(output_feat, name_subject)
        os.makedirs(curr_feat_dir, exist_ok=True)
        for name_feat in df_feat.keys():
            feat = df_feat[name_feat].values
            np.save(os.path.join(curr_feat_dir, str(name_trial) + '_' + name_feat +'.npy'), feat)
            savemat(os.path.join(curr_feat_dir, str(name_trial) + '_' + name_feat +'.mat'), {'feature': feat})

        ###############################
        ## Crop data
        ###############################
        duration_seconds = len(feat)/FPS_feat
        onset_seconds = T_start_events[idx_trial]
        eeg = raw.copy().crop(tmin=onset_seconds, tmax=onset_seconds+duration_seconds)
        ###############################
        ## Preprocessing
        ###############################
        ## -------------
        ## Select channels
        ## -------------
        eeg_channels = ch_names[0:]
        eeg = eeg.pick_channels(eeg_channels)
        if plot:
            eeg.plot(start=100, duration=10, n_channels=len(raw.ch_names))

        ## -------------
        ## Notch filtering
        ## -------------
        df_pre['notch_applied'] = [notch_applied]
        if notch_applied:
            eeg = eeg.notch_filter(freqs=freq_notch)
            df_pre['notch'] = [freq_notch]
            if plot:
                eeg.plot()

        ## -------------
        ## BPFiltering
        ## -------------
        df_pre['bpf_applied'] = [bpf_applied]
        if bpf_applied:
            iir_params = dict(order=order, ftype=ftype)
            filter_params = mne.filter.create_filter(eeg.get_data(), eeg.info['sfreq'], 
                                                    l_freq=freq_low, h_freq=freq_high, 
                                                    method='iir', iir_params=iir_params)

            eeg = eeg.filter(l_freq=freq_low, h_freq=freq_high, method='iir', iir_params=iir_params)
            df_pre['bandpass'] = [iir_params]
            df_pre['HPF'] = [freq_low]
            df_pre['LPF'] = [freq_high]
            if plot:
                eeg.plot()

        ## -------------
        ## Intrpolation
        ## -------------
        df_pre['int_applied'] = [int_applied]
        if int_applied: 
            eeg = eeg.interpolate_bads(reset_bads=False)  #, method=interpolation

            # Get the indices and names of the interpolated channels
            interp_inds = eeg.info['bads']
            interp_names = [eeg.info['ch_names'][i] for i in interp_inds]

            # Print the number and names of the interpolated channels
            print(f'{len(interp_inds)} channels interpolated: {interp_names}')

            df_pre['interpolation'] = [interpolation]
            df_pre['interp_inds'] = [interp_inds]
            df_pre['interp_names'] = [interp_names]

            if plot:
                eeg.plot()

        ## -------------
        ## Rereferencing
        ## -------------
        df_pre['reref_applied'] = [reref_applied]
        if reref_applied:
            # Set electrodes for rereferencing
            if reref_type == 'Mastoids':
                reref_channels = ['M1', 'M2']   
            else:
                reref_channels = 'average'           

            # Actually r-referencing signals
            eeg = eeg.set_eeg_reference(ref_channels=reref_channels)
            df_pre['reref_type'] = [reref_type]
            df_pre['reref_channels'] = [reref_channels]
            if plot:
                eeg.plot()
        else:
            df_pre['reref_type'] = [None]
            df_pre['reref_channels'] = [None]

        ## -------------
        ## Resampling
        ## -------------
        df_pre['down_applied'] = [down_applied]
        if down_applied:
            eeg = eeg.resample(sfreq=downfreq)
            df_pre['downfreq'] = [downfreq]
            print(eeg.info)
            if plot:
                eeg.plot()

        ## -------------
        ## Save preprocessing stages
        ## -------------
        df_pre.to_csv(os.path.join(output_dir, csv_pre), index=False)

        # Get only data matrix
        eeg = eeg.get_data()
        print(eeg.shape, len(feat))
        channels, samples = eeg.shape
        assert samples == len(feat)
        
        # Save file to mupy in the subject's folder
        print('Saving EEG responses to ', str(name_trial), eeg.shape)
        savemat(os.path.join(output_dir, str(name_trial) + '.mat'), {'trial_data': eeg[0:29, :], 
                                                                     'trial_emg': eeg[30:31, :]})
        