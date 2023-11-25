import argparse
import logging
import os
import sys
from scipy.io import wavfile
from pythonjsonlogger import jsonlogger

import tornado
import tornado.ioloop
import tornado.web
import tempfile
import shazam


class Shazam(tornado.web.RequestHandler):
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

            with tempfile.NamedTemporaryFile(dir=temp_dir, suffix=".wav", delete=False) as temp_file:
                temp_file.write(files[0]['body'])
                path = temp_file.name
                temp_files.append(temp_file.name)

            # Read audio files
            fs, audio = wavfile.read(path)

            scores = shazam.find_match(fs, audio)

            self.set_status(200)
            self.write(
                {
                    "scores": scores,
                }
            )
        except Exception as e:
            logging.error(f"request failed: {e}")
            self.set_status(500)
            self.write(str(e))
        finally:
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                except Exception as e:
                    logging.info(f"can not delete file {e}")
            temp_files.clear()


def make_app():
    return tornado.web.Application([
        (r"/shazam", Shazam),
    ])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    logger = logging.getLogger()

    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        '%(levelname)8s %(name)s %(message)s %(filename)s %(lineno)d %(asctime)'
    )
    logHandler.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(logHandler)

    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000, help='port to listen on')
    args = parser.parse_args(sys.argv[1:])
    app = make_app()
    logging.info(f'started server on {args.port}')
    app.listen(args.port)
    tornado.ioloop.IOLoop.current().start()
