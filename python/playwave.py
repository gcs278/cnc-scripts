import pyaudio
import wave
import sys
import os.path


class AudioFile:
    chunk = 1024

    def __init__(self, file):
        """ Init audio stream """ 
        self.wf = wave.open(file, 'rb')
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format = self.p.get_format_from_width(self.wf.getsampwidth()),
            channels = self.wf.getnchannels(),
            rate = self.wf.getframerate(),
            output = True
        )

    def play(self):
        """ Play entire file """
        data = self.wf.readframes(self.chunk)
        while data != '':
            self.stream.write(data)
            data = self.wf.readframes(self.chunk)

    def close(self):
        """ Graceful shutdown """ 
        self.stream.close()
        self.p.terminate()

# Usage example for pyaudio
if len(sys.argv) != 2:
    print "ERROR: Need at least 1 argument"
    quit()

fileName = sys.argv[1]
if not os.path.isfile(fileName):
    print "ERROR: The given file doesn't exist"
    quit()

a = AudioFile(fileName)
a.play()
a.close()
quit()