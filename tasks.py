from time import time, sleep
from rq import get_current_job
import numpy as np

def current_measurement_task(sourcemeter, voltage):
    # Get a reference to the job
    job = get_current_job()

    # Setup current measurement
    sourcemeter.setup_current_measurement(voltage, 1)

    # Start the source
    sourcemeter.enable()
    t_start = time()

    # Run the measurement
    t = []
    i = []
    try:
        while True:
            t.append(time() - t_start)
            i.append(sourcemeter.get_current())
            job.meta['data'] = (t, i)
            job.save_meta()
    finally:
        sourcemeter.disable()


def mock_current_measurement(voltage):
    # Get a reference to the job
    job = get_current_job()

    # Setup current measurement
    print("Setting up mock sourcemeter")

    # Start the source
    t_start = time()

    # Run the measurement
    t = []
    i = []
    job.meta['should_stop'] = False
    while not job.meta['should_stop']:
        t.append(time() - t_start)
        i.append(np.random.random())
        job.meta['data'] = (t, i)
        job.save_meta()
        sleep(5)
    print("Disabled sourcemeter")


def example(seconds):
    job = get_current_job()
    print('Starting task')
    for i in range(seconds):
        job.meta['progress'] = 100.0 * i / seconds
        job.save_meta()
        print(i)
        sleep(1)
    job.meta['progress'] = 100
    job.save_meta()
    print('Task completed')