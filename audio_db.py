import tqdm
import pickle
from scipy.io import wavfile
import typing
import numpy
import shazam


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
        constellation = shazam.create_constellation(audio_input, fs)
        hashes = shazam.create_hashes(constellation, i)
        for hash, time_index_pair in hashes.items():
            if hash not in hash_db:
                hash_db[hash] = []
            hash_db[hash].append(time_index_pair)

    with open("database.pickle", 'wb') as db:
        pickle.dump(hash_db, db, pickle.HIGHEST_PROTOCOL)
    with open("song_index.pickle", 'wb') as song_db:
        pickle.dump(song_index, song_db, pickle.HIGHEST_PROTOCOL)


if __name__ == '__main__':
    import glob

    songs = glob.glob('data/*.wav')
    create_database(songs)
