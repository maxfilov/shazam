# shazam

This is a self-hosted shazam that works with a specific set of audio files.

## How to use

### Install the requirements

```shell
pip3 install -r requirements.txt
```

### Create the database

Put some wav audio files to the [data](./data) directory and then run the database generator
```shell
python3 audio_db.py
```

### Start the server
```shell
python3 server.py --port 8000
```

### Run the test
```shell
./tests/upload_file.sh PATH_TO_AUDIO_EXCERPT
```

# How everything works

Please check [this article](https://michaelstrauss.dev/shazam-in-python) by Michael Strauss and
[this paper](https://www.ee.columbia.edu/~dpwe/papers/Wang03-shazam.pdf) by Avery Li-Chun Wang 
with the science behind the code.
