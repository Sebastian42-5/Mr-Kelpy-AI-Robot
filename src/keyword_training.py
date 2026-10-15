import os
import torch 
import torchaudio
from torch.utils.data import Dataset

# turning the 1D waveform tensor into a mel spectogram

class CustomRobotKWS(Dataset):
    def __init__(self, data_dir, sample_rate, n_mels=64):
        mel_spectogram = torchaudio.transforms.MelSpectrogram(
            sample_rate = self.sample_rate,
            n_fft = 400,
            hop_length = 160,
            n_mels = n_mels
        )

        self.class_to_index_mapping = {'silence': 0, 'unknown': 1, 'recognized': 2}
        self.file_list = []

        for category in self.class_to_index_mapping.keys():
            
