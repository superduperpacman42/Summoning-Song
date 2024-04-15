import numpy as np
import sounddevice as sd
import soundfile as sf
import queue
import time

samplerate = 44100//5
device = None

stream = None
q = queue.Queue()
sound = None
old_volume = 0
state = None
delay = 0


def init_stream():
    global stream
    try:
        stream = sd.InputStream(
            device=device, channels=1,
            samplerate=samplerate, callback=audio_callback)
        stream.__enter__()
        return True
    except Exception as e:
        print("Audio device not supported")
        return False

def get_devices():
    return sd.query_devices()

def start():
    """Call once to begin audio recording"""
    global old_volume, state, sound, delay
    q.queue.clear()
    sound = np.zeros(0)
    old_volume = 0
    delay = 0
    state = "Waiting"

def stop():
    try:
        stream.__exit__()
    except Exception as e:
        pass

def record(duration, max_delay=0):
    """Call iteratively until recording is finished"""
    global old_volume, state, sound, delay
    if not stream:
        return
    while True:
        try:
            data = q.get_nowait()
            if state == "Waiting":
                delay += len(data)
                volume = np.mean(np.abs(data))
                if not old_volume:
                    old_volume = volume
                elif delay > 0.1 * samplerate and volume / old_volume > 30:
                    state = "Recording"
                elif max_delay and delay > max_delay * samplerate:
                    state = "Timeout"
                    return state, sound
                window = min(delay, samplerate * 0.2)
                old_volume = ((window - len(data)) * old_volume + len(data) * volume) / window
            if state == "Recording":
                sound = np.concatenate((sound, data))
                if len(sound) >= duration * samplerate:
                    sound = sound[:int(duration * samplerate)]
                    state = "Finished"
                    return state, sound
        except queue.Empty:
            return state, sound


def audio_callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print("[ERROR]", status)
    # Fancy indexing with mapping creates a (necessary!) copy:
    downsample = 1
    q.put(indata[::downsample, 0])


def get_transform(sound):
    # sound /= max(np.abs(sound))
    # vol_max = max(np.abs(sound))
    timestep = 0.01 # sec
    freqstep = 4 # Hz
    step = int(samplerate * timestep)
    res = int(samplerate / freqstep)
    n = (len(sound) - res) // step
    transform = np.zeros((res//2+1, n))
    for i in range(n):
        # Compute frequency spectrum
        transform[:, i] = np.abs(np.fft.rfft(sound[step*i:step*i+res]))# / (res / 2)
        # Normalize volume
        # transform[:, i] /= np.linalg.norm(transform[:, i])
        # Filter for silence
        # if np.max(np.abs(sound[step*i:step*i+res])) < vol_max / 100:
        #     transform[:, i] *= 0

    # Smooth frequency
    freq_window = 200 # Hz
    freq_kernel = np.ones(int(freq_window / freqstep))
    freq_kernel /= len(freq_kernel)
    for i in range(transform.shape[1]):
        transform[:, i] = np.convolve(transform[:, i], freq_kernel, 'same')

    # Smooth time
    time_window = 0.2 # sec
    time_kernel = np.ones(int(time_window / timestep))
    time_kernel /= len(time_kernel)
    for i in range(transform.shape[0]):
        transform[i, :] = np.convolve(transform[i, :], time_kernel, 'same')

    return transform


def compare_transforms(t1, t2):
    n = min(t1.shape[1], t2.shape[1])
    t1 = t1[:, :n]
    t2 = t2[:, :n]
    # return np.sum(np.linalg.norm(t1[:, :n]-t2[:, :n], axis=0))
    return np.sum(t1 * t2 / (np.linalg.norm(t1) * np.linalg.norm(t2)))


def plot_transform(transform):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    ax.imshow(transform)
    ax.set_aspect("auto")
    plt.show()


def plot_compare_transforms(t1, t2):
    import matplotlib.pyplot as plt
    fig, (ax1, ax2) = plt.subplots(1, 2)
    ax1.imshow(t1)
    ax1.set_aspect("auto")
    ax2.imshow(t2)
    ax2.set_aspect("auto")
    plt.show()


def load_transform(filename):
    data, fs = sf.read(filename, dtype='float32')
    sd.play(data, fs)
    downsample = fs // samplerate
    return get_transform(data[::downsample]), len(data) / fs

def write(data):
    sf.write(f'sound_{time.time()}.wav', data, samplerate)

def play(data):
    sd.play(data, samplerate)

if __name__ == "__main__":
    init_stream()
    loaded, duration = load_transform("audio/Owl3.wav")
    time.sleep(duration)
    with stream:
        start()
        while 1:
            state_, sound_ = record(duration+.5)
            if state_ == "Recording":
                print("Recording...")
            elif state_ == "Waiting":
                print("Waiting...")
            else:
                print("Finished")
                break
    time.sleep(0.5)
    # write(sound_)
    # sd.play(sound_, samplerate)
    # time.sleep(duration+.5)
    transform = get_transform(sound_)
    print("Alignment:", compare_transforms(transform, loaded))
    plot_compare_transforms(loaded, transform)
