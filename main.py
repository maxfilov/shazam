import os
import numpy as np
from scipy.io import wavfile
import scipy.signal
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application
from tempfile import NamedTemporaryFile
from shazam import find_match


# Function to perform cross-correlation
def perform_cross_correlation(audio1, audio2):
    # Perform cross-correlation
    cross_corr = scipy.signal.correlate(audio1, audio2, mode='full')

    # Get time lag corresponding to the maximum correlation
    time_lag = np.argmax(cross_corr) - (len(audio1) - 1)
    return time_lag


class Shazam(RequestHandler):
    def data_received(self, chunk):
        pass

    async def post(self):
        temp_files = []
        try:
            files = self.request.files.get('file')
            if not files:
                self.set_status(400)
                self.write("Please provide exactly two audio files.")
                return

            temp_dir = "temp_audio"
            os.makedirs(temp_dir, exist_ok=True)

            with NamedTemporaryFile(dir=temp_dir, suffix=".wav", delete=False) as temp_file:
                temp_file.write(files[0]['body'])
                path = temp_file.name
                temp_files.append(temp_file.name)

            # Read audio files
            fs1, audio1 = wavfile.read(path)

            scores = find_match(fs1, audio1)

            self.set_status(200)
            self.write(
                {
                    "scores": scores,
                }
            )
        except Exception as e:
            print(f"failed {e}")
            self.set_status(500)
            self.write(str(e))
        finally:
            for temp_file in temp_files:
                os.remove(temp_file)
            temp_files.clear()


def make_app():
    return Application([
        (r"/shazam", Shazam),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(8000)
    IOLoop.current().start()
