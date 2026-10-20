import os
import torch 
import torchaudio
from torch.utils.data import Dataset
import torch.nn as nn

# turning the 1D waveform tensor into a mel spectogram

class CustomRobotKWS(Dataset):
    def __init__(self, data_dir, sample_rate, n_mels=64, n_classes=2):
        super.__init__()

        mel_spectogram = torchaudio.transforms.MelSpectrogram(
            sample_rate = self.sample_rate,
            n_fft = 400,
            hop_length = 160,
            n_mels = n_mels
        )

        self.class_to_index_mapping = {'silence': 0, 'unknown': 1, 'recognized': 2}
        self.file_list = []

        # two convolutional layers

        self.conv1 = nn.Sequential(
            nn.Conv2d(1, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2)
        )

        self.conv2 = nn.Sequential(
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2)
        )

        # global average pooling

        self.gap = nn.AdaptiveAvgPool2d((1, 1))

        # classifier

        self.fc = nn.Linear(64, n_classes)

    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.gap(x)
        x = x.view(x.size(0), -1)


    
            
