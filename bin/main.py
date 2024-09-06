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

session = None
args = None
pub_camera_panorama = None


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

    logging.debug(
        f"content {content} received_at: {received_at}, enclosed_at {enclosed_at}")
    Image = CompressedImage.FromString(content)

    img_dic = {
        "timestamp": Image.timestamp.ToDatetime(),
        "frame_id": Image.frame_id,
        "data": Image.data,
        "format": Image.format
    }

    # Convert the image data to a numpy array
    image_data = np.frombuffer(img_dic['data'], dtype=np.uint8)

    # Decode the image data
    decoded_image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)

    # Save the image to disk
    output_image_path = os.path.join("./imgs", "panorama_image.jpg")
    cv2.imwrite(output_image_path, decoded_image)

    # Display the image (FOLLOWING DONT WORK as it is headless - unsure if threr is a workaround? Maybe, if not used in the dev container insted try in a local env)
    # cv2.imshow("Panorama Image", decoded_image)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

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
        session.close()

    atexit.register(_on_exit)
    logging.info(f"Zenoh session established: {session.info()}")

    #################################################
    # Setting up PUBLISHER

    # Camera panorama
    key_exp_pub_camera_pano = keelson.construct_pub_sub_key(
        realm=args.realm,
        entity_id=args.entity_id,
        subject="compressed_image",  # Needs to be a supported subject
        source_id="panorama/" + args.output_id,
    )
    pub_camera_panorama = session.declare_publisher(
        key_exp_pub_camera_pano,
        priority=zenoh.Priority.INTERACTIVE_HIGH(),
        congestion_control=zenoh.CongestionControl.DROP(),
    )
    logging.info(f"Created publisher: {key_exp_pub_camera_pano}")

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

    try:

        # TODO: SUBSCRIPTION initialization for panorama image creation
        if args.trigger_sub is not None:

            key_exp_sub_camera = keelson.construct_pub_sub_key(
                realm=args.realm,
                entity_id=args.entity_id,
                subject="compressed_image",  # Needs to be a supported subject
                source_id=args.trigger_sub,
            )

            logging.info(f"Subscribing to key: {key_exp_sub_camera}")

            # Declaring zenoh publisher
            sub_camera = session.declare_subscriber(
                key_exp_sub_camera, subscriber_camera_publisher
            )

        # TODO: FIXED HZ initialization for panorama image creation
        if args.trigger_hz is not None:
            logging.info(f"Trigger Hz: {args.trigger_hz}")
            while True:
                fixed_hz_publisher()

    except KeyboardInterrupt:
        logging.info("Program ended due to user request (Ctrl-C)")
    except Exception as e:
        logging.error(f"Program ended due to error: {e}")

    # finally:
    #     logging.info("Closing Zenoh session...")
    #     session.close()
    #     logging.info("Zenoh session closed.")
