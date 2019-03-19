from time import time, sleep
from rq import get_current_job, get_current_connection
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
    connection = get_current_connection()

    # Setup current measurement
    print("Setting up mock sourcemeter")

    # Start the source
    t_start = time()

    # Run the measurement
    t = []
    i = []
    while connection.get(job.key + b':should_stop') != b'1':
        t.append(time() - t_start)
        i.append(np.random.random())
        job.meta['data'] = (t, i)
        job.save_meta()
        print(connection.get(job.key + b':should_stop'))
        sleep(5)
    print("Disabled sourcemeter")

'''
Set the flag from the calling side with queue.connection.set(job.key + b':should_stop', 1, ex=30)
where queue = rq.Queue(...) and job = queue.enqueue(function_to_perform)
The argument queue.key is rq:queue:<queue_name>
'''


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