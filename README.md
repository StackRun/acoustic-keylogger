#  Keyboard Acoustic Emanations Attack - Research

[![CircleCI](https://circleci.com/gh/shoyo/acoustic-keylogger/tree/master.svg?style=shield)](https://circleci.com/gh/shoyo/acoustic-keylogger/tree/master)

## Overview
A *keyboard acoustic emanations attack* is a form of a [side-channel
attack](https://en.wikipedia.org/wiki/Side-channel_attack) where an attacker
extracts what a victim typed on his or her keyboard using just the audio signal
of the typing. Such a keylogging attack can result in passwords and
confidential information being stolen from just a compromised microphone, and
thus has severe security implications. I believe that many of the techniques that
have become de facto in fields such as voice recognition and natural language
processing can translate over to an implementation of an audio-based keylogging
attack. With the advent of several open-sourced machine learning libraries in
the past decade, I believe that such an attack is becoming increasingly
accessible to implement, and should therefore receive more awareness from the
general public.

### Objective
Evaluate the threat of a *keyboard acoustic emanations attack* in the current
machine learning landscape by creating a proof-of-concept pipeline for
executing such an attack and measuring its __accuracy__, __practicality__, and
__accessibility__.
* __Accuracy__: How well does the pipeline approximate typed keys?
* __Practicality__: How robust is the pipeline under realistic conditions?
* __Accessibility__: How easily can the pipeline be built? (with regards to
  prerequisite knowledge and used technology)

### Current Progress
An essential component of the pipeline is the ability to distinguish the
difference between key sounds emitted by each key on a keyboard. There must be
quantitative evidence that keys (or groups of keys) emit different sounds, and
they do so consistently under regular conditions. I have been able to verify
for certain keyboards and certain typing patterns that key sounds emitted can
be clustered and identified. This result has __not__ yet been verified on a
more diverse dataset.

![alt text](https://github.com/shoyo-inokuchi/acoustic-keylogger-research/blob/master/lab/figs/vp3-brown.png)
*t-SNE clusters formed by keystroke sounds generated by a VP3 mechanical keyboard
with Cherry MX Brown switches*

![alt text](https://github.com/shoyo-inokuchi/acoustic-keylogger-research/blob/master/lab/figs/macbook2016.png)
*t-SNE clusters formed by keystroke sounds generated by a Macbook Pro 2016 with
Apple butterfly switches*


## The Pipeline
This is the pipeline that is currently being implemented. Each component is
modular, such that any component can be swapped out for an enhanced version of
itself with minimal effort. This prevents this project from being monolithic
and allows more incremental improvements to be made.

* __Data Collection__ - Gathering a diverse dataset of typing sounds recorded
under realistic conditions

* __Keystroke Detection__ - Identifying all of the keystroke sounds in a given
audio file

* __Keystroke Feature Extraction__ - Preprocessing each keystroke sound for
further analysis

* __Clustering__ - Forming clusters with the preprocessed keystroke data

* __Predictive Cluster Labeling__ - Identifying which clusters correspond to
which key type

* __Iterative Pseudo-labeled Supervised Training__ - Training a classifier
using the predicted labels and iterating

This pipeline is modeled after the research described in [*Keyboard Acoustic Emanations Revisited* by L. Zhuang, F. Zhou, J. D. Tygar in 2005](https://www.cs.cornell.edu/~shmat/courses/cs6431/zhuang.pdf).


## Setting up
### Option 1 - Docker
This project uses a Python 3.6 development environment and a PostgreSQL database
to manage various audio data. This option conveniently spins up these
environments with Docker Compose.  

* Install [Docker](https://www.docker.com/products/docker-desktop).  
* Build images with `$ docker-compose build`. This is only required the first
time or whenever Docker settings are changed.

This step will install all dependencies for env (such as Jupyter, Tensorflow,
NumPy etc.) and mount your local file system with the file system within the
"env" Docker container.

* Spin up the database and development environment with `$ docker-compose up`.

This should open up the database for connections and connect __http://localhost:8888__ to the Jupyter notebook.

### Option 2 - No Docker
In exchange for containerization and seamless setup, Docker requires more
overhead memory and comes with little quirks in the development environment
with the current setup (like having to manually open the Jupyter notebook). I
find that a lot of times using Docker for small tweaks is a bit overkill, so
I'm leaving this option here.

* Install Python version 3.6. To downgrade from Python 3.7+ without overriding
your current version, I recommend installing [conda](https://www.anaconda.com/distribution/)
and running

        $ conda install python=3.6.8

* Set up a virtual environment. I recommend virtualenvwrapper for managing
multiple environments.   

* Install dependencies with

        $ pip3 install -r requirements.txt  

* Make sure Python can find custom packages for this repository with

        $ export PYTHONPATH=/path/to/repo/acoustic-keylogger-research/custom-packages

  and can connect to the test database with

        $ export TEST_DATABASE_URL=postgresql+psycopg2://postgres@acoustic-keylogger-research_db_1:5432

  I recommend adding these commands to your `~/.bash_profile` or `~/.bashrc` so
  that it gets loaded between terminal sessions.

* Open Jupyter notebook with

        $ jupyter notebook


This option can be simpler if you're unfamiliar with Docker or you don't need
to access the database. (Though the latter should still be possible using local
postgres commands)


## Testing [![CircleCI](https://circleci.com/gh/shoyo/acoustic-keylogger/tree/master.svg?style=shield)](https://circleci.com/gh/shoyo/acoustic-keylogger/tree/master)

Tests are being implemented for the __custom_packages/acoustic_keylogger__
package, which contains various functions for audio processing and data
management. These tests are contained in __tests/test_acoustic_keylogger__.

To run tests with the Docker configuration (Option 1), execute:

    $ docker-compose run env pytest -q tests

To run tests with no Docker configuration (Option 2), execute:

    $ python3.6 -m pytest -q tests

__Note:__ Both of the commands above are assumed to be executed from the root
directory of this repository.


## Relevant Research Papers
Many research papers were published in the mid-2000s concerning the topic of
keyboard acoustic emanations attacks. Some research, such as [*Keyboard
Acoustic Emanations Revisited* by L. Zhuang, F. Zhou, J. D. Tygar in
2005](https://www.cs.cornell.edu/~shmat/courses/cs6431/zhuang.pdf),
demonstrated extremely accurate results (96% chars recovered from 10 minute
sound recording) even without labeled training data.

### Supervised Methods
  * [*Keyboard acoustic emanations*](https://ieeexplore.ieee.org/document/1301311)
    by D. Asonov, R. Agrawal. 2004.

### Unsupervised Methods
  * [*Keyboard Acoustic Emanations Revisited*](https://www.cs.cornell.edu/~shmat/courses/cs6431/zhuang.pdf)
  by L. Zhuang, F. Zhou, J. D. Tygar. 2005.
  * [*Dictionary Attacks Using Keyboard Acoustic Emanations*](https://www.eng.tau.ac.il/~yash/p245-berger.pdf)
  by Y. Berger, A. Wool, A. Yeredor. 2006.
