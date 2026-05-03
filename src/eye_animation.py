from PIL import Image, ImageTk, ImageSequence
from pathlib import Path
import tkinter as tk

root_dir = Path('animation_frames/idle')

idle_image_frame_paths = []

for path in root_dir.rglob('*'):
    if path.is_file() and 'idle' in path.name:
        idle_image_frame_paths.append(path)

frames = [Image.open(path) for path in idle_image_frame_paths]

fps = 15
frame_duration = int(1000 / fps)

frames[0].save(
    'idle-animation.gif',
    save_all=True,
    append_images=frames[1:],
    duration=frame_duration,
    loop=0
)


class GIFPlayer:
    def __init__(self, root, path, frame_delay, loop_delay):
        self.root = root 
        self.img = Image.open(path)

        self.frames = [ImageTk.PhotoImage(frame.copy().convert('RGBA')) for frame in ImageSequence.Iterator(self.img)]

        self.label = tk.Label(root)
        self.label.pack()
        self.frame_delay = frame_delay 
        self.loop_delay = loop_delay

        self.counter = 0
        self.play_gif()

    def play_gif(self):
        frame = self.frames[self.counter]
        self.label.configure(image=frame)

        if self.counter == len(self.frames) - 1:
            next_delay = self.loop_delay
            self.counter = 0
        else:
            next_delay = self.frame_delay
            self.counter += 1

        self.root.after(next_delay, self.play_gif)


root = tk.Tk()
root.attributes('-fullscreen', True)
player = GIFPlayer(root, 'idle-animation.gif', 67, 500)
root.mainloop()