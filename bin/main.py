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
from keelson.payloads.RawImage_pb2 import RawImage
import cv2
import numpy as np
import os
import pickle
from google.protobuf import timestamp_pb2
from keelson.payloads.CompressedImage_pb2 import CompressedImage



from keelson import enclose, construct_pub_sub_key

session = None
args = None
pub_camera_panorama = None


# Load calibration data
calibration_data_path = './bin/Calibration_v2.p'
with open(calibration_data_path, "rb") as f:
    calib_data = pickle.load(f)

mtx = calib_data["mtx"]
dist = calib_data["dist"]
optimal_camera_matrix = calib_data["optimal_camera_matrix"]
roi = calib_data["roi"]
x, y, w, h = roi




# def query_panorama(query):
#     """
#     Query for panorama image

#     Args:
#         query (zenoh.Query): Zenoh query object
#     Returns:
#         envelope (bytes) with compressed image payload
#     """

#     ingress_timestamp = time.time_ns()

#     query_key = query.selector
#     logging.debug(f">> [Query] Received query key {query_key}")

#     query_payload = query.value.payload
#     logging.debug(f">> [Query] Received query payload {query_payload}")

#     # Expecting not a payload

#     # Triggering get requests for camera images

#     # Camera image getter
#     replies = session.get(
#         args.camera_query,
#         zenoh.Queue(),
#         target=QueryTarget.BEST_MATCHING(),
#         consolidation=zenoh.QueryConsolidation.NONE(),
#     )

#     arrImages = []

#     for reply in replies.receiver:

#         try:
#             print(
#                 ">> Received ('{}': '{}')".format(reply.ok.key_expr, reply.ok.payload)
#             )
#             # Unpacking image
#             received_at, enclosed_at, content = keelson.uncover(reply.ok.payload)
#             logging.debug(f"content {content} received_at: {received_at}, enclosed_at {enclosed_at}")

#             Image = CompressedImage.FromString(content)

#             img_dic = {
#                 "timestamp": Image.timestamp.ToDatetime(),
#                 "frame_id": Image.frame_id,
#                 "data": Image.data,
#                 "format": Image.format
#             }

#             arrImages.append(img_dic)

#         except:
#             print(">> Received (ERROR: '{}')".format(reply.err.payload))


#     ##########################
#     # TODO: STITCHING HERE
#     ##########################


#     # Packing panorama created
#     newImage = CompressedImage()
#     newImage.timestamp.FromNanoseconds(ingress_timestamp)
#     newImage.frame_id = "foxglove_frame_id"
#     newImage.data = b"binary_image_data" # Binary image data
#     newImage.format = "jpeg" # supported formats `webp`, `jpeg`, `png`
#     serialized_payload = newImage.SerializeToString()
#     envelope = keelson.enclose(serialized_payload)

#     # Replaying on the query with the panorama image in an keelson envelope
#     query.reply(zenoh.Sample(str(query.selector), envelope))
#     # query.reply(zenoh.Sample(str(query.selector), "OK")) # Simple response for testing


def subscriber_camera_publisher(data):
    """
    Subscriber trigger by camera image incoming
    """

    ingress_timestamp = time.time_ns()
    received_at, enclosed_at, content = keelson.uncover(data.payload)
    logging.debug(f"content {content} received_at: {received_at}, enclosed_at {enclosed_at}")

    # Extract axis number from the key expression
    axis = data.key_expr.split('-')[-1]  # Assuming the key ends with '-1', '-2', etc.
    decoded_image = cv2.imdecode(np.frombuffer(content, dtype=np.uint8), cv2.IMREAD_COLOR)

    if decoded_image is not None:
        undistorted_image = cv2.undistort(decoded_image, mtx, dist, None, optimal_camera_matrix)
        cropped_image = undistorted_image[y:y+h, x:x+w]
        _, compressed_image_data = cv2.imencode('.jpg', cropped_image)
        if compressed_image_data is not None:
            new_image = CompressedImage()
            now = timestamp_pb2.Timestamp()
            now.GetCurrentTime()
            new_image.timestamp.CopyFrom(now)
            new_image.data = compressed_image_data.tobytes()
            new_image.format = 'jpeg'  # Ensure this format matches one of the acceptable formats

            # Dynamically determine the topic based on the axis
            topic = f'rise/v0/boatswain/pubsub/undistorted_image/axis-{axis}'
            
            # Use the pre-defined publishers dictionary to publish the image
            if int(axis) in undistorted_image_publishers:
                undistorted_image_publishers[int(axis)].put(new_image.SerializeToString())
                logging.info(f"Published undistorted image for axis {axis}")
            else:
                logging.error(f"No publisher found for axis {axis}")
        else:
            logging.error("Failed to encode undistorted image")
    else:
        logging.error("Failed to decode received image")     
    

    # img_dic = {
    #     "timestamp": Image.timestamp.ToDatetime(),
    #     "frame_id": Image.frame_id,
    #     "data": Image.data,
    #     "format": Image.format
    # }

    # Save the image to disk
    # output_image_path = os.path.join("./imgs", "test_image.jpg")
    # cv2.imwrite(output_image_path, decoded_image)

    # Display the image (FOLLOWING DONT WORK as it is headless - unsure if threr is a workaround? Maybe, if not used in the dev container insted try in a local env)
    # cv2.imshow("Panorama Image", decoded_image)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    ##########################
    # TODO: STITCHING HERE
    ##########################

    # Packing panorama created
    # newImage = CompressedImage()
    # newImage.timestamp.FromNanoseconds(ingress_timestamp)
    # newImage.frame_id = "foxglove_frame_id"
    # newImage.data = b"binary_image_data"  # Binary image data
    # newImage.format = "jpeg"  # supported formats `webp`, `jpeg`, `png`
    # serialized_payload = newImage.SerializeToString()
    # envelope = keelson.enclose(serialized_payload)
    # pub_camera_panorama.put(envelope)


def fixed_hz_publisher():

    ingress_timestamp = time.time_ns()

    # Camera image getter
    replies = session.get(
        args.camera_query,
        zenoh.Queue(),
        target=QueryTarget.BEST_MATCHING(),
        consolidation=zenoh.QueryConsolidation.NONE(),
    )

    for reply in replies.receiver:
        try:
            print(
                ">> Received ('{}': '{}')".format(
                    reply.ok.key_expr, reply.ok.payload)
            )
            # Unpacking image
            received_at, enclosed_at, content = keelson.uncover(
                reply.ok.payload)
            logging.debug(
                f"content {content} received_at: {received_at}, enclosed_at {enclosed_at}")
            Image = CompressedImage.FromString(content)

            img_dic = {
                "timestamp": Image.timestamp.ToDatetime(),
                "frame_id": Image.frame_id,
                "data": Image.data,
                "format": Image.format
            }

        except:
            print(">> Received (ERROR: '{}')".format(reply.err.payload))

    ##########################
    # TODO: STITCHING HERE
    ##########################

    # Packing panorama created
    newImage = CompressedImage()
    newImage.timestamp.FromNanoseconds(ingress_timestamp)
    newImage.frame_id = "foxglove_frame_id"
    newImage.data = b"binary_image_data"  # Binary image data
    newImage.format = "jpeg"  # supported formats `webp`, `jpeg`, `png`
    serialized_payload = newImage.SerializeToString()
    envelope = keelson.enclose(serialized_payload)
    pub_camera_panorama.put(envelope)
    time.sleep(1 / args.fixed_hz)


#####################################################
"""
# Processor stitching panorama image 

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

    # # Camera panorama
    # key_exp_pub_camera_pano = keelson.construct_pub_sub_key(
    #     realm=args.realm,
    #     entity_id=args.entity_id,
    #     subject="compressed_image",  # Needs to be a supported subject
    #     source_id="panorama/" + args.output_id,
    # )
    # pub_camera_panorama = session.declare_publisher(
    #     key_exp_pub_camera_pano,
    #     priority=zenoh.Priority.INTERACTIVE_HIGH(),
    #     congestion_control=zenoh.CongestionControl.DROP(),
    # )
    # logging.info(f"Created publisher: {key_exp_pub_camera_pano}")

    #################################################
    # Setting up Querible

    # Camera panorama
    # key_exp_query_camera_pano = keelson.construct_req_rep_key(
    #     realm=args.realm,
    #     entity_id=args.entity_id,
    #     responder_id="panorama",
    #     procedure="get_panorama",
    # )
    # query_camera_panorama = session.declare_queryable(
    #     key_exp_query_camera_pano,
    #     query_panorama
    # )
    # logging.info(f"Created queryable: {key_exp_query_camera_pano}")

    #################################################

    # Setup publishers for undistorted images
    undistorted_image_publishers = {}
    for axis in range(1, 5):  # Assuming axes 1 through 4
        topic = f"rise/v0/boatswain/pubsub/undistorted_image/axis-{axis}"
        undistorted_image_publishers[axis] = session.declare_publisher(topic, priority=zenoh.Priority.INTERACTIVE_HIGH())
        logging.info(f"Created publisher for undistorted images: {topic}")

    # Define a subscriber handling function for each camera axis
    def handle_camera_feed(axis):
        def subscriber_handler(data):
            subscriber_camera_publisher(data, undistorted_image_publishers[axis], axis)
        return subscriber_handler

    # Declare subscribers for each camera feed based on axis
    for axis in range(1, 5):
        topic = f"rise/v0/boatswain/pubsub/compressed_image/axis-{axis}"
        subscriber_handler = handle_camera_feed(axis)
        session.declare_subscriber(topic, subscriber_handler)
        logging.info(f"Declared subscriber for {topic}")

    try:
        # # TODO: SUBSCRIPTION initialization for panorama image creation
        # if args.trigger_sub is not None:

        #     key_exp_sub_camera = keelson.construct_pub_sub_key(
        #         realm=args.realm,
        #         entity_id=args.entity_id,
        #         subject="compressed_image",  # Needs to be a supported subject
        #         source_id=args.trigger_sub,
        #     )

        #     logging.info(f"Subscribing to key: {key_exp_sub_camera}")

        #     # Declaring zenoh publisher
        #     sub_camera = session.declare_subscriber(
        #         key_exp_sub_camera, subscriber_camera_publisher
        #     )

        # # TODO: FIXED HZ initialization for panorama image creation
        # if args.trigger_hz is not None:
        #     logging.info(f"Trigger Hz: {args.trigger_hz}")
        #     while True:
        #         fixed_hz_publisher()


        input("Press Enter to exit...\n")
    except KeyboardInterrupt:
        logging.info("Program ended due to user request (Ctrl-C)")
    except Exception as e:
        logging.error(f"Program ended due to error: {e}")
    finally:
        _on_exit()
