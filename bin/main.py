import zenoh
from zenoh import QueryTarget
import logging
import warnings
import atexit
import json
import time
import keelson
from terminal_inputs import terminal_inputs
from keelson.payloads.CompressedImage_pb2 import CompressedImage
import cv2
import numpy as np
import os
import pickle
import queue
import threading
import signal

session = None
args = None
pub_camera_panorama = None
image_queue = queue.Queue(maxsize=10)  # Limit the size of the queue to avoid memory issues
stop_event = threading.Event()  # Event to signal worker threads to stop
sub_camera = None  # Handle for Zenoh subscriber

# Load calibration data
calibration_data_path = './bin/Calibration_v2.p'
with open(calibration_data_path, "rb") as f:
    calib_data = pickle.load(f)

mtx = calib_data["mtx"]
dist = calib_data["dist"]
optimal_camera_matrix = calib_data["optimal_camera_matrix"]
roi = calib_data["roi"]
x, y, w, h = roi

# Define the number of worker threads
NUM_WORKERS = 4  # You can adjust this number based on the capacity of your system

def process_image_worker(worker_id):
    """
    Worker thread that processes images from the queue.
    Runs in parallel to the main Zenoh subscriber.
    """
    global pub_camera_panorama
    logging.info(f"Worker {worker_id} started.")
    while not stop_event.is_set() or not image_queue.empty():
        try:
            # Get image from queue (block if no image available, timeout allows thread to check stop event)
            data = image_queue.get(timeout=1)

            if data is None:
                logging.info(f"Worker {worker_id} received stop signal.")
                break  # Stop the thread if we get None (signal to shut down)

            ingress_timestamp, decoded_image, axis = data

            if decoded_image is not None:
                # Apply calibration
                undistorted_image = cv2.undistort(decoded_image, mtx, dist, None, optimal_camera_matrix)
                cropped_image = undistorted_image[y:y+h, x:x+w]

                # Encode the image back to compressed format (JPEG)
                _, compressed_image_data = cv2.imencode('.jpg', cropped_image)

                if compressed_image_data is not None:
                    # Prepare the new image with the updated timestamp
                    new_image = CompressedImage()
                    new_image.timestamp.FromNanoseconds(ingress_timestamp)
                    new_image.data = compressed_image_data.tobytes()
                    new_image.format = 'jpeg'

                    serialized_payload = new_image.SerializeToString()
                    envelope = keelson.enclose(serialized_payload)

                    # Publish the undistorted and cropped image
                    pub_camera_panorama.put(envelope)
                    logging.debug(f'Worker {worker_id} sending undistorted image for axis-{axis}...')
                else:
                    logging.error(f"Worker {worker_id} failed to encode undistorted image")
            else:
                logging.error(f"Worker {worker_id} failed to decode received image")
            
            # Indicate that the task is done
            image_queue.task_done()

        except queue.Empty:
            # Timeout reached, allowing the worker to check if it should stop
            continue
        except Exception as e:
            logging.error(f"Error in worker {worker_id}: {e}")

def stop_workers():
    """
    Stop all worker threads by signaling them and adding None to the queue.
    """
    logging.info("Stopping workers...")
    stop_event.set()  # Signal all threads to stop
    for _ in range(NUM_WORKERS):
        image_queue.put(None)  # Add stop signal to the queue for each worker

    # Wait for all worker threads to finish
    for worker_thread in worker_threads:
        worker_thread.join()

def subscriber_camera_publisher(data):
    """
    Subscriber trigger by camera image incoming.
    Adds images to the processing queue for asynchronous handling.
    """
    if stop_event.is_set():
        return  # Stop adding images to the queue if we are shutting down

    ingress_timestamp = time.time_ns()
    received_at, enclosed_at, content = keelson.uncover(data.payload)

    logging.debug(f"received_at: {received_at}, enclosed_at {enclosed_at}")

    incoming_image = CompressedImage.FromString(content)

    # Extract axis number from the key expression
    axis = str(data.key_expr).split('-')[-1]  # Assuming the key ends with '-1', '-2', etc.
    decoded_image = cv2.imdecode(np.frombuffer(incoming_image.data, dtype=np.uint8), cv2.IMREAD_COLOR)

    try:
        # Add the decoded image to the queue for processing
        image_queue.put_nowait((ingress_timestamp, decoded_image, axis))
    except queue.Full:
        logging.error("Image processing queue is full. Dropping frame.")

def signal_handler(sig, frame):
    """
    Handle SIGINT (Ctrl + C) to stop workers and exit cleanly.
    """
    logging.info("Received interrupt signal (Ctrl + C).")
    if sub_camera:
        sub_camera.undeclare()  # Stop Zenoh subscription
    stop_workers()
    _on_exit()
    exit(0)

"""
Processor stitching panorama image 

Start with either: 
    - Subscriptions Camera  
    - Fixed Hz  
"""
if __name__ == "__main__":
    # Input arguments and configurations
    args = terminal_inputs()

    # Setup logger
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s %(message)s", level=args.log_level
    )
    logging.captureWarnings(True)
    warnings.filterwarnings("once")

    # Construct session
    logging.info("Opening Zenoh session...")
    conf = zenoh.Config()

    if args.connect is not None:
        conf.insert_json5(zenoh.config.CONNECT_KEY, json.dumps(args.connect))
    session = zenoh.open(conf)

    def _on_exit():
        logging.info("Closing Zenoh session...")
        session.close()
        logging.info("Zenoh session closed.")

    atexit.register(_on_exit)
    logging.info(f"Zenoh session established: {session.info()}")

    #################################################
    # Setting up PUBLISHER

    key_exp_pub_camera_pano = keelson.construct_pub_sub_key(
        realm=args.realm,
        entity_id=args.entity_id,
        subject="compressed_image",  # Needs to be a supported subject
        source_id="undistorted_image"
    )
    pub_camera_panorama = session.declare_publisher(
        key_exp_pub_camera_pano,
        priority=zenoh.Priority.INTERACTIVE_HIGH(),
        congestion_control=zenoh.CongestionControl.DROP(),
    )
    logging.info(f"Created publisher: {key_exp_pub_camera_pano}")

    # Start the image processing worker threads
    worker_threads = []
    for i in range(NUM_WORKERS):
        worker_thread = threading.Thread(target=process_image_worker, args=(i,), daemon=True)
        worker_threads.append(worker_thread)
        worker_thread.start()

    # Register the signal handler for Ctrl + C
    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Subscribe to both axis-1 and axis-2
        if args.trigger_sub is not None:
            key_exp_sub_camera = args.trigger_sub
            logging.info(f"Subscribing to key: {key_exp_sub_camera}")

            # Declaring subscriber
            sub_camera = session.declare_subscriber(
                key_exp_sub_camera, subscriber_camera_publisher
            )

        input("Press Enter to exit...\n")
        sub_camera.undeclare()  # Stop Zenoh subscription on Enter key press
        stop_workers()  # Stop workers when Enter is pressed
    except Exception as e:
        logging.error(f"Program ended due to error: {e}")
        stop_workers()  # Ensure workers stop on exception
    finally:
        _on_exit()
        