import PySpin
import os
import io
import timeit
import datetime
import numpy as np
from cv2 import resize as resizeImage
import cv2
import sys
import requests, json
'''
Used during fly days to test capture & preprocesing times and transmission times.
    Flags:
        apply_downscale: Should the image be downscaled?
        framerate: Capturing framerate
        num_images: Number of images to capture
        image_dir: Image output directory
'''
IMAGE_DIR = "./"
IP_ADDRESS = "http://172.31.138.108:8080"
USERNAME = "drone"
PASSWORD = "ruautonomous"
token_label = "Authorization"
access_token = None

def capture(cam, apply_downscale, framerate, num_images):

    cam.Init() # start camera
    cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous) # set acquisition mode to continuous
    cam.AcquisitionFrameRateEnable.SetValue(True)
    cam.AcquisitionFrameRate.SetValue(int(framerate))
    cam.BeginAcquisition()
    for i in range(int(num_images)):
        start = timeit.default_timer() # start downscale timer
        image = cam.GetNextImage() # acquire image
        if image.IsIncomplete():
            print("Image incomplete with image status %d..." % image.GetImageStatus())
        else: 
            image_array = image.Convert(PySpin.PixelFormat_RGB8, PySpin.NEAREST_NEIGHBOR).GetNDArray() # turn image into ND array
            if(apply_downscale == 'True'):
                image_result = resizeImage(image_array, (500,500)) # downscale image
            else:
                image_result = resizeImage(image_array, (1000,1000)) 
            # print runtime
            stop = timeit.default_timer()
            print('Processing Time: ', stop - start)
            img_encoded = cv2.imencode('.jpg', image_result)[1]

            start = timeit.default_timer() # start transmission timer
            access_token = connect()
            headers = {token_label : access_token}
            files = {"image": img_encoded.tostring()}
            # while True:
            #     try:
            #         with open("D:/Downloads/75380261_1573374882801635_2123551660729958400_n.jpg", 'rb') as f:
            #             contents = f.read()
            #         files = {"image": contents}
            #         break
            #     except Exception as e:
            #         continue
            
            telem_data = {name: (None,"1") for name in ["pitch", "roll", "lat", "lon", "alt", "rel_alt", "yaw", "hdg"]}
            telem_data["time_saved"] = datetime.datetime.now().strftime("%H:%M:%S")
            telem_data["time_sent"] = datetime.datetime.now().strftime("%H:%M:%S")
            print(telem_data)
            response = requests.post(IP_ADDRESS + "/drone/postImage", headers = headers, files = files, data = telem_data)
            done = response.status_code
            if done == 200:
                stop = timeit.default_timer()
                print('Transmission Time: ', stop - start)    
            else:
                print('Transmission error: ' + str(done))         

    # deinitialize camera   
    cam.EndAcquisition()
    cam.DeInit()
    del cam

def connect():
    logged_in = False
    endpoint = IP_ADDRESS + "/drone/login"
    headers = {"Content-Type": "application/json; charset=UTF-8"}
    data = {"password": PASSWORD, "username": USERNAME}

    while logged_in == False:
        try:
            response = requests.post(endpoint, headers = headers, data = json.dumps(data))

            if response.status_code == 200:
                access_token = "JWT " + response.json()["token"]
                logged_in = True
        # except TypeError:
        #     # the JWT returned by the CCS sometimes is not correct Base64, thus we keep trying until we get a valid one
        #     pass
        except KeyboardInterrupt:
            return

    print("DEBUG: Successfully logged in to " + endpoint + " at " + str(datetime.datetime.now().time()))
    return access_token

def main(apply_downscale, framerate, num_images):
    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras() # get list of cameras
    if cam_list.GetSize() == 0: # exit if no cameras detected
        cam_list.Clear()
        system.ReleaseInstance()
        print("No cameras")
        input("Done! Press Enter to exit...")
        return False
    cam = cam_list.GetByIndex(0) # get camera
    capture(cam, apply_downscale, framerate, num_images)
    # shut down
    cam_list.Clear()
    del cam
    system.ReleaseInstance()

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
