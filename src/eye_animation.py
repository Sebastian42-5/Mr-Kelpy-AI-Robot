from PIL import Image, ImageTk, ImageSequence
from pathlib import Path
import tkinter as tk
import time

root_dir = Path('src/animation_frames')

idle_image_frame_paths = []
thinking_image_frame_paths = []
talking_image_frame_paths = []
happy_image_frame_paths = []

animations = [idle_image_frame_paths, thinking_image_frame_paths, talking_image_frame_paths, happy_image_frame_paths]


for path in root_dir.rglob('*'):
    if path.is_file() and 'idle' in path.name:
        idle_image_frame_paths.append(path)
        idle_image_frame_paths.sort()
    elif path.is_file() and 'thinking' in path.name:
        thinking_image_frame_paths.append(path)
        thinking_image_frame_paths.sort()
    elif path.is_file() and 'talking' in path.name:
        talking_image_frame_paths.append(path)
        talking_image_frame_paths.sort()
    elif path.is_file() and 'happy' in path.name:
        happy_image_frame_paths.append(path)
        happy_image_frame_paths.sort()


fps = 15
frame_duration = int(1000 / fps)

for title, animation in zip(('idle', 'thinking', 'talking', 'happy'), animations):
    frames = [Image.open(path) for path in animation]
    

    frames[0].save(
        f'{title}-animation.gif',
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

        self.cancel_id = self.root.after(next_delay, self.play_gif)

    def stop_gif(self):
        if self.cancel_id:
            self.root.after_cancel(self.cancel_id)
            self.cancel_id = None

    def switch_gif(self, new_path, frame_delay, loop_delay):
        self.stop_gif()

        self.counter = 0
        self.img = Image.open(new_path)
        self.frames = [ImageTk.PhotoImage(frame.copy().convert('RGBA')) for frame in ImageSequence.Iterator(self.img)]
        self.frame_delay = frame_delay
        self.loop_delay = loop_delay
        
        self.play_gif()

if __name__ == "__main__":
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    player = GIFPlayer(root, 'idle-animation.gif', 67, 500)
    
    root.after( 5000, lambda: player.switch_gif('thinking-animation.gif', 67, 500))
    root.after( 10000, lambda: player.switch_gif('talking-animation.gif', 67, 500))
    root.after( 15000, lambda: player.switch_gif('happy-animation.gif', 67, 500))
    
    root.mainloop()