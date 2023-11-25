import pickle
import tqdm
import numpy
from scipy import signal
from scipy.io import wavfile
import typing


def ensure_mono(data: numpy.ndarray):
    # Check if the audio is already mono
    if len(data.shape) == 1 or data.shape[1] == 1:
        return data

    # Convert stereo to mono by averaging the channels
    # TODO: check what happens if left channel has a sound, but right doesn't
    return numpy.mean(data, axis=1, dtype=data.dtype)


def create_database(audio_files: typing.List[str]):
    song_index: typing.Dict[int, str] = {}
    hash_db: typing.Dict[int, typing.List[typing.Tuple[int, int]]] = {}

    i: int
    filename: str
    for i, filename in enumerate(tqdm.tqdm(sorted(audio_files))):
        song_index[i] = filename

        fs: int
        audio_input: numpy.ndarray
        fs, audio_input = wavfile.read(filename)
        constellation = create_constellation(audio_input, fs)
        hashes = create_hashes(constellation, i)
        for hash, time_index_pair in hashes.items():
            if hash not in hash_db:
                hash_db[hash] = []
            hash_db[hash].append(time_index_pair)

    with open("database.pickle", 'wb') as db:
        pickle.dump(hash_db, db, pickle.HIGHEST_PROTOCOL)
    with open("song_index.pickle", 'wb') as song_db:
        pickle.dump(song_index, song_db, pickle.HIGHEST_PROTOCOL)


def create_hashes(constellation_map, song_id=None):
    upper_frequency = 23_000
    frequency_bits = 10

    hashes = {}
    # assume pre-sorted
    # Iterate the constellation
    for idx, (time, freq) in enumerate(constellation_map):
        # Iterate the next 100 pairs to produce the combinatorial hashes
        for other_time, other_freq in constellation_map[idx: idx + 100]:
            diff = other_time - time
            # If the time difference between the pairs is too small or large
            # ignore this set of pairs
            if diff <= 1 or diff > 10:
                continue

            # Place the frequencies (in Hz) into a 1024 bins
            freq_binned = freq / upper_frequency * (2 ** frequency_bits)
            other_freq_binned = other_freq / upper_frequency * (2 ** frequency_bits)

            # Produce a 32 bit hash
            hash = int(freq_binned) | (int(other_freq_binned) << 10) | (int(diff) << 20)
            hashes[hash] = (time, song_id)
    return hashes


def create_constellation(audio, fs):
    window_length_seconds: float = 0.5
    window_length_samples: int = int(window_length_seconds * fs)
    window_length_samples += window_length_samples % 2

    audio = ensure_mono(audio)
    # Pad the song to divide evenly into windows
    # Example: we have an audio with Fs of 8000 which contains 15500 points
    # then we need to pad it with 500 zeroes at the end, because in order to split
    # into even windows of 8000 length, we need 500 points: 15500 % 8000 == 500
    amount_to_pad = window_length_samples - audio.size % window_length_samples
    song_input = numpy.pad(audio, (0, amount_to_pad))

    # Perform a short time fourier transform
    frequencies, times, stft = signal.stft(
        song_input,
        fs=fs,
        nperseg=window_length_samples,
        nfft=window_length_samples,
        return_onesided=True)

    num_peaks = 15
    constellation_map = []
    for time_idx, window in enumerate(stft.T):
        # Spectrum is by default complex.
        # We want real values only
        spectrum = abs(window)
        # Find peaks - these correspond to interesting features
        # Note the distance - want an even spread across the spectrum
        peaks, props = signal.find_peaks(spectrum, prominence=0, distance=200)

        # Only want the most prominent peaks
        # With a maximum of 15 per time slice
        n_peaks = min(num_peaks, len(peaks))
        # Get the largest peaks from the prominences
        # This is an argpartition
        # Useful explanation: https://kanoki.org/2020/01/14/find-k-smallest-and-largest-values-and-its-indices-in-a-numpy-array/
        largest_peaks = numpy.argpartition(props["prominences"], -n_peaks)[-n_peaks:]
        for peak in peaks[largest_peaks]:
            frequency = frequencies[peak]
            constellation_map.append([time_idx, frequency])

    return constellation_map


database = pickle.load(open('database.pickle', 'rb'))
song_index_lookup = pickle.load(open("song_index.pickle", "rb"))


def score_songs(hashes):
    matches_per_song = {}
    for hash, (sample_time, _) in hashes.items():
        if hash in database:
            matching_occurences = database[hash]
            for source_time, song_index in matching_occurences:
                if song_index not in matches_per_song:
                    matches_per_song[song_index] = []
                matches_per_song[song_index].append((hash, sample_time, source_time))

    scores = {}
    for song_index, matches in matches_per_song.items():
        song_scores_by_offset = {}
        for hash, sample_time, source_time in matches:
            delta = source_time - sample_time
            if delta not in song_scores_by_offset:
                song_scores_by_offset[delta] = 0
            song_scores_by_offset[delta] += 1

        max = (0, 0)
        for offset, score in song_scores_by_offset.items():
            if score > max[1]:
                max = (offset, score)

        scores[song_index] = max

    # Sort the scores for the user
    scores = list(sorted(scores.items(), key=lambda x: x[1][1], reverse=True))

    return scores


def find_match(fs, audio):
    constellation = create_constellation(audio, fs)
    hashes = create_hashes(constellation, None)
    scores = score_songs(hashes)
    return {song_index_lookup[song_index]: score[1] for song_index, score in scores}


if __name__ == '__main__':
    import glob

    songs = glob.glob('data/*.wav')
    create_database(songs)
