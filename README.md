# Keelson Processor Panorama

Keelson processor for image processing  

## Get started development environment on your own computer: 

1) Install [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
   - Docker desktop will provide you with an UI for monitoring and controlling docker containers and images along simplified debugging 
   - If you want to learn more about docker and its building blocks of images and containers checkout [Docker quick hands-on in guide](https://docs.docker.com/guides/get-started/)
2) Start up of **Zenoh router** either in your computer or any other computer within your local network
   - See docker compose file [docker-compose.zenoh-router.yml](./docker-compose.zenoh-router.yml)
   - To start the router open an terminal and navigate to folder where the above mentioned docker compose file is located
      ```bash
      # Check that you are in the folder containing the docker-compose.zenoh-router.yml
      ls 

      # Start router with log output 
      docker compose -f docker-compose.zenoh-router.yml up -d 
      ```  
   - Controll that the router has started in docker desktop should be an green indication on a container named  "zenoh-router"
3) Clone this repo in your prefered why, recommeded for UI experinse is to use github desktop 
   [Link to github repository](https://github.com/RISE-Maritime/keelson-processor-panorama)
4) Open project in VScode and start the devcontainer 
   - Devcontainer can be started with inbuilt action comand press **ctrl+sift+p**
   - Select --> Dev container: build and open (or similar action) 
   - Now the devcontaoner should start to build and this can take a few minutes the first time 
   - To learn more about devontatiner read following tuturial [LINK to tutrial](https://code.visualstudio.com/docs/devcontainers/tutorial)
5) Start playbak of MCAP file
   - Keep the data files putside this project so the data is not ending up in the git or being pushed to github 
   - Make or use prexisting foled for all data in this example an local folder named "DB" is used and mcap file lame is "sspa.mcap"
   - Run following commands outside the devontainer in a terminal 
   ```bash 
   # You need to input your system info on all places where <this_text_is>

   # Template  
   docker run --rm --network host --name mcap-replay --volume <path_to_file_dir>:rec ghcr.io/rise-maritime/keelson:0.3.7-pre.55 "mcap-replay --input rec/<name_of_file>.mcap"

   # Example 
   docker run --rm --network host --name mcap-replay --volume E:/EPA_TEMP:rec ghcr.io/rise-maritime/keelson:0.3.7-pre.55 "mcap-replay --input rec/sspa.mcap"
   
   ```

   - if the file is found you shoud se comthing simmilar to following output
   ```bash
   
      2024-09-06 14:38:30,422 INFO mcap-replay Opening Zenoh session...
      2024-09-06 14:38:31,147 INFO mcap-replay Replaying from: rec/sspa.mcap
      2024-09-06 14:38:31,147 INFO mcap-replay ...with 11 channels
      2024-09-06 14:38:31,147 INFO mcap-replay ...with 11591 message
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
6) Run processor
    - Open terminal inside dev container and navigate to the project root folder 
    - Edit the subscription topic "--trigger-sub" to match output from the replay file    
   ```bash
   python3 bin/main.py --log-level 10 -e boatswain --trigger-sub rise/v0/boatswain/pubsub/compressed_image/axis-1 --camera-query rise/v0/boatswain/pubsub/compressed_image/*
   ```

## Quick start

```bash
python3 bin/main.py --log-level 10 -e boatswain --trigger-sub axis-1
```

