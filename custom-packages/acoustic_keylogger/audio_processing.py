"""
Written by Shoyo Inokuchi (March 2019)

Audio processing scripts for acoustic keylogger project. Repository is located at
https://github.com/shoyo-inokuchi/acoustic-keylogger-research.
"""

import os
from copy import deepcopy

import numpy as np
from scipy.io import wavfile as wav
import matplotlib.pyplot as plt
import sqlalchemy as db
import sqlalchemy.orm as orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import postgresql


# File input (single WAV file path -> sound data encoded as array)

def wav_read(filepath):
    """Return 1D NumPy array of wave-formatted audio data denoted by filename.

    Input should be a string containing the path to a wave-formatted audio file.
    """
    sample_rate, data = wav.read(filepath)
    if type(data[0]) == np.ndarray:
        return data[:, 0]
    else:
        return data


# Sound preprocessing before keystroke detection

def silence_threshold(sound_data, n=5, factor=11, output=True):
    """Return the silence threshold of the sound data.

    The sound data should begin with n-seconds of silence.
    """
    sampling_rate = 44100
    num_samples   = sampling_rate * n
    silence       = sound_data[:num_samples]
    tolerance     = 40
    measured      = np.std(silence)
    if output and measured > tolerance:
        # raise Exception(f'Sound data must begin with at least {n}s of silence.')
        print(f'Initial silence was higher than expected at {measured}, which',
              f' is higher than expected {tolerance}')
    return max(np.amax(silence), abs(np.amin(silence))) * factor


def remove_random_noise(sound_data, threshold=None):
    """Return a copy of sound_data where random noise is replaced with 0's.

    The original sound_data is not mutated.
    """
    threshold = threshold or silence_threshold(sound_data)
    sound_data_copy = deepcopy(sound_data)
    for i in range(len(sound_data_copy)):
        if abs(sound_data_copy[i]) < threshold:
            sound_data_copy[i] = 0
    return sound_data_copy


# Keystroke detection (encoded array -> all keystroke data in array)

def detect_keystrokes(sound_data, sample_rate=44100, output=True):
    """Return slices of sound_data that denote each keystroke present.

    Returned keystrokes are coerced to be the same length by appending trailing
    zeros.

    Current algorithm:
    - Calculate the "silence threshold" of sound_data.
    - Traverse sound_data until silence threshold is exceeded.
    - Once threshold is exceeded, mark that index as "a".
    - Identify the index 0.3s ahead of "a", and mark that index as "b".
    - If "b" happens to either:
          1) denote a value that value exceeds the silence threshold (aka:
             likely impeded on the next keystroke waveform)
          2) exceed the length of sound_data
      then backtrack "b" until either:
          1) it denotes a value lower than the threshold
          2) "b" is 1 greater than "a"
    - Slice sound_data from index "a" to "b", and append that slice to the list
      to be returned. If "b" was backtracked, then pad the slice with trailing
      zeros to make it 0.3s long.

    :type sound_file  -- NumPy array denoting input sound clip
    :type sample_rate -- integer denoting sample rate (samples per second)
    :rtype            -- NumPy array of NumPy arrays
    """
    threshold          = silence_threshold(sound_data, output=output)
    keystroke_duration = 0.3   # seconds
    len_sample         = int(sample_rate * keystroke_duration)

    keystrokes = []
    i = 0
    while i < len(sound_data):
        if abs(sound_data[i]) > threshold:
            a, b = i, i + len_sample
            if b > len(sound_data):
                b = len(sound_data)
            while abs(sound_data[b]) > threshold and b > a:
                b -= 1
            keystroke = sound_data[a:b]
            trailing_zeros = np.array([0 for _ in range(len_sample - (b - a))])
            keystroke = np.concatenate((keystroke, trailing_zeros))
            keystrokes.append(keystroke)
            i = b - 1
        i += 1
    return np.array(keystrokes)


def detect_keystrokes_improved(sound_data, sample_rate=44100):
    """Return slices of sound_data that denote each keystroke present.
    
    Objective:
    - Satisfy same functional requirements as 'detect_keystrokes()', but better
    - Create a more accurate and flexible keystroke detection function
      utilizing more advanced audio processing techniques
    - Calculate MFCC etc. of sound_data to detect relevant peaks in sound
    """
    pass


# Display detected keystrokes (WAV file -> all keystroke graphs)

def visualize_keystrokes(filepath):
    """Display each keystroke detected in WAV file specified by filepath."""
    wav_data = wav_read(filepath)
    keystrokes = detect_keystrokes(wav_data)
    n = len(keystrokes)
    print(f'Number of keystrokes detected in "{filepath}": {n}')
    print('Drawing keystrokes...')
    num_cols = 3
    num_rows = n/num_cols + 1
    plt.figure(figsize=(num_cols * 6, num_rows * .75))
    for i in range(n):
        plt.subplot(num_rows, num_cols, i + 1)
        plt.title(f'Index: {i}')
        plt.plot(keystrokes[i])
    plt.show()


# Data collection (multiple WAV files -> ALL keystroke data)

def collect_keystroke_data(filepath_base='datasets/keystrokes/',
                           keys=None,
                           output=False,
                           ignore=None):
    """Read WAV files and return collected data.

    Arguments:
    base_dir -- directory to search for audio files
    keys     -- list of key types to detect (corresponds to file names)
    output   -- True to display status messages during keystroke detection
    ignore   -- dict of filenames mapped to indices of keystrokes to ignore

    input format  -- WAV files in subdirectories of "base_dir"
    output format -- list of dicts where each dict denotes a single collected
                     keystroke. Formatted like:
                         list(dict(keys: key type, sound digest, sound data))
    """
    alphabet = [letter for letter in 'abcdefghijklmnopqrstuvwxyz']
    other_keys = ['space', 'period', 'enter']
    keys = keys or alphabet + other_keys

    collection = []
    for key in keys:
        filepath = filepath_base + key + '/'
        if output: print(f'> Reading files from {filepath} for key "{key}"')
        for file in os.listdir(filepath):
            if output:
                print(f'  > Detecting keystrokes from "{file}"', end='')
            wav_data = wav_read(filepath + file)
            keystrokes = detect_keystrokes(wav_data, output=False)
            collected = 0
            for i in range(len(keystrokes)):
                if ignore and file in ignore and i in ignore[file]:
                    continue
                else:
                    keystroke = keystrokes[i]
                    data = {
                        'key_type': key,
                        'sound_digest': hash(keystroke[:30].tobytes()),
                        'sound_data': keystroke,
                    }
                    collection.append(data)
                    collected += 1
            if output: print(f' => Collected {collected} keystrokes')
    print('> Done')

    return collection


# Data storage (ALL keystroke data -> store in database)

Base = declarative_base()


class Keystroke(Base):
    """Schema for Keystroke model."""
    __tablename__ = 'keystrokes'

    id = db.Column(db.BigInteger, primary_key=True)
    key_type = db.Column(db.String(32), nullable=False)
    sound_digest = db.Column(db.BigInteger, nullable=False, unique=True)
    sound_data = db.Column(postgresql.ARRAY(db.Integer))

    def __repr__(self):
        return f'<Keystroke(key={self.key_type}, digest={self.sound_digest})>'


class KeystrokeTest(Base):
    """Schema for testing."""
    __tablename__ = 'test_keystrokes'

    id = db.Column(db.BigInteger, primary_key=True)
    key_type = db.Column(db.String(32), nullable=False)
    sound_digest = db.Column(db.BigInteger, nullable=False, unique=True)
    sound_data = db.Column(postgresql.ARRAY(db.Integer))


def connect_to_database(url=os.environ['TEST_DATABASE_URL']):
    """Connect to database and return corresponding engine instance."""
    engine = db.create_engine(url)
    connection = engine.connect()
    return engine


def create_keystroke_table(url=os.environ['TEST_DATABASE_URL']):
    """Create keystroke table and test table in database."""
    engine = connect_to_database(url)
    Base.metadata.create_all(engine)


def drop_keystroke_table(url=os.environ['TEST_DATABASE_URL']):
    """Drop keystroke table in database."""
    engine = connect_to_database(url)
    Keystroke.__table__.drop(engine)


def drop_keystroke_test_table(url):
    """Drop test keystroke table in database. For testing."""
    engine = connect_to_database(url)
    KeystrokeTest.__table__.drop(engine)


def store_keystroke_data(data, url=os.environ['TEST_DATABASE_URL']):
    """Store collected data in database.

    input format  -- output of collect_keystroke_data()
    """
    engine = connect_to_database(url)
    Session = orm.sessionmaker(bind=engine)
    session = Session()
    try:
        for keystroke in data:
            entry = Keystroke(key_type=keystroke['key_type'],
                              sound_digest=keystroke['sound_digest'],
                              sound_data=keystroke['sound_data'])
            session.add(entry)
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def store_keystroke_test_data(data, url):
    """Store collected data in database. For testing."""
    engine = connect_to_database(url)
    Session = orm.sessionmaker(bind=engine)
    session = Session()
    try:
        for keystroke in data:
            entry = KeystrokeTest(key_type=keystroke['key_type'],
                                  sound_digest=keystroke['sound_digest'],
                                  sound_data=keystroke['sound_data'])
            session.add(entry)
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


# Data retrieval

def load_keystroke_data(url=os.environ['TEST_DATABASE_URL']):
    """Retrieve data from database, do relevant formatting, and return it.

    Return a tuple of the form (x, y, z) where
        x denotes an array of each sound data,
        y denotes an array of integer labels (key 'a' denoted by 0, etc.),
        z denotes an array of string labels (key 'a' denoted by 'a', etc.).

        Furthermore, x, y, z are formatted such that for any index 'i',
        x[i], y[i], z[i] correspond to the same keystroke.

    Particularly, tuple (x, y) is formatted so that it can be passed to
    tf.keras.model.fit().
    For details, view documentation at: https://keras.io/models/model/#fit
    """
    engine = connect_to_database(url)
    Session = orm.sessionmaker(bind=engine)
    session = Session()
    keystrokes = session.query(Keystroke).all()
    session.close()

    if keystrokes:
        keytype_id = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6,
            'h': 7, 'i': 8, 'j': 9, 'k': 10, 'l': 11, 'm': 12, 'n': 13, 'o': 14,
            'p': 15, 'q': 16, 'r': 17, 's': 18, 't': 19, 'u': 20, 'v': 21, 'w': 22,
            'x': 23, 'y': 24, 'z': 25, 'space': 26, 'period': 27, 'enter': 28,
        }
        data, labels_int, labels_str = [], [], []
        for row in keystrokes:
            data.append(row.sound_data)
            labels_int.append(keytype_id[row.key_type])
            labels_str.append(row.key_type)
        return np.array(data), np.array(labels_int), np.array(labels_str)

