# Keelson Processor for Image Processing

## Get started with the development environment on your own computer:

1. Install [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
   - Docker Desktop provides a user interface for monitoring and controlling Docker containers and images, along with simplified debugging.
   - If you want to learn more about Docker and its building blocks of images and containers, check out the [Docker quick hands-on guide](https://docs.docker.com/guides/get-started/).

2. Start up the **Zenoh router** either on your computer or any other computer within your local network.
   - See the Docker Compose file [docker-compose.zenoh-router.yml](./docker-compose.zenoh-router.yml).
   - To start the router, open a terminal and navigate to the folder where the above-mentioned Docker Compose file is located.
     ```bash
     # Check that you are in the folder containing the docker-compose.zenoh-router.yml
     ls

     # Start the router with log output
     docker compose -f docker-compose.zenoh-router.yml up -d
     ```

   - Verify that the router has started in Docker Desktop. There should be a green indication on a container named "zenoh-router".

3. Clone this repository in your preferred way. We recommend using GitHub Desktop.
   [Link to GitHub repository](https://github.com/RISE-Maritime/keelson-processor-panorama)

4. Open the project in VSCode and start the devcontainer.
   - The devcontainer can be started with the built-in action command. Press **Ctrl+Shift+P**.
   - Select "Dev container: build and open" (or a similar action).
   - The devcontainer should start building, which may take a few minutes the first time.
   - To learn more about devcontainers, read the following tutorial: [LINK to tutorial](https://code.visualstudio.com/docs/devcontainers/tutorial)

5. Start playback of the MCAP file.
   - Keep the data files outside this project to prevent them from ending up in the Git repository or being pushed to GitHub.
   - Create or use an existing folder for all data. In this example, a local folder named "DB" is used, and the MCAP file name is "sspa.mcap".
   - Run the following commands outside the devcontainer in a terminal:
     ```bash
     # You need to input your system info in all places where <this_text_is>

     # Template
     docker run --rm --network host --name mcap-replay --volume <path_to_file_dir>:rec ghcr.io/rise-maritime/keelson:0.3.7-pre.55 "mcap-replay --input rec/<name_of_file>.mcap"

     # Example
     docker run --rm --network host --name mcap-replay --volume E:/EPA_TEMP:rec ghcr.io/rise-maritime/keelson:0.3.7-pre.55 "mcap-replay --input rec/sspa.mcap"
     ```

   - If the file is found, you should see something similar to the following output:
     ```bash
     2024-09-06 14:38:30,422 INFO mcap-replay Opening Zenoh session...
     2024-09-06 14:38:31,147 INFO mcap-replay Replaying from: rec/sspa.mcap
     2024-09-06 14:38:31,147 INFO mcap-replay ...with 11 channels
     2024-09-06 14:38:31,147 INFO mcap-replay ...with 11591 messages
     2024-09-06 14:38:31,147 INFO mcap-replay ...with 574 chunks
     2024-09-06 14:38:31,147 INFO mcap-replay ...with 11 schemas
     2024-09-06 14:38:31,147 INFO mcap-replay ...first message at 1718014071523365283
     2024-09-06 14:38:31,147 INFO mcap-replay ...last message at 1718014230169277764
     2024-09-06 14:38:31,147 INFO mcap-replay Declaring publisher for: rise/v0/boatswain/pubsub/flight_controller_telemetry_rawimu/speedybee
     2024-09-06 14:38:31,147 INFO mcap-replay Declaring publisher for: rise/v0/boatswain/pubsub/flight_controller_telemetry_ahrs/speedybee
     2024-09-06 14:38:31,147 INFO mcap-replay Declaring publisher for: rise/v0/boatswain/pubsub/flight_controller_telemetry_vibration/speedybee
     2024-09-06 14:38:31,147 INFO mcap-replay Declaring publisher for: rise/v0/boatswain/pubsub/flight_controller_telemetry_battery/speedybee
     2024-09-06 14:38:31,147 INFO mcap-replay Declaring publisher for: rise/v0/boatswain/pubsub/compressed_image/axis-3
     2024-09-06 14:38:31,148 INFO mcap-replay Declaring publisher for: rise/v0/boatswain/pubsub/point_cloud/ydlidar
     2024-09-06 14:38:31,148 INFO mcap-replay Declaring publisher for: rise/v0/boatswain/pubsub/point_cloud_simplified/ydlidar
     2024-09-06 14:38:31,148 INFO mcap-replay Declaring publisher for: rise/v0/boatswain/pubsub/compressed_image/axis-4
     2024-09-06 14:38:31,148 INFO mcap-replay Declaring publisher for: rise/v0/boatswain/pubsub/compressed_image/axis-2
     2024-09-06 14:38:31,148 INFO mcap-replay Declaring publisher for: rise/v0/boatswain/pubsub/flight_controller_telemetry_vfrhud/speedybee
     2024-09-06 14:38:31,148 INFO mcap-replay Declaring publisher for: rise/v0/boatswain/pubsub/compressed_image/axis-1
     ```

6. Run the processor.
   - Open a terminal inside the devcontainer and navigate to the project root folder.
   - Edit the subscription topic "--trigger-sub" to match the output from the replay file.
     ```bash
     python3 bin/main.py --log-level 10 -e boatswain --trigger-sub rise/v0/boatswain/pubsub/compressed_image/axis-1 --camera-query rise/v0/boatswain/pubsub/compressed_image/*
     ```

## Quick start

```bash
python3 bin/main.py --log-level 10 -e boatswain --trigger-sub axis-1
```

