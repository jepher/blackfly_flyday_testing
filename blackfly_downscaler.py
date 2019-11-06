import PySpin
import os
import io
import timeit
from PIL import Image
import numpy as np
from cv2 import resize as resizeImage
import cv2
import sys, getopt
import argparse
import requests

'''
Used during fly days to test capture & preprocesing times and transmission times.
    Flags:
        apply_downscale: Should the image be downscaled?
        framerate: Capturing framerate
        num_images: Number of images to capture
        image_dir: Image output directory
'''
IMAGE_DIR = "./"
IP_ADDRESS = "http://192.168.1.127:8000";

def sendtoserver(frame):
    imencoded = cv2.imencode(".jpg", frame)[1]
    headers = {"Content-type": "text/plain"}
    try:
        conn.request("POST", "/", imencoded.tostring(), headers)
        response = conn.getresponse()
    except conn.timeout as e:
        print("timeout")


    return response

def capture(cam, apply_downscale, framerate, num_images):

    cam.Init() # start camera
    cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous) # set acquisition mode to continuous
    cam.AcquisitionFrameRateEnable.SetValue(True)
    cam.AcquisitionFrameRate.SetValue(int(framerate))
    cam.BeginAcquisition()
    for i in range(int(num_images)):
        start = timeit.default_timer()
        image = cam.GetNextImage() # acquire image
        if image.IsIncomplete():
            print("Image incomplete with image status %d..." % image.GetImageStatus())
        else: 
            if(apply_downscale == 'True'):
                image_array = image.Convert(PySpin.PixelFormat_RGB8, PySpin.NEAREST_NEIGHBOR).GetNDArray() # turn image into ND array
                image_result = resizeImage(image_array, (500,500)) # downscale image
                # print runtime
                stop = timeit.default_timer()
                print('Processing Time: ', stop - start)
                buff = io.BytesIO()
                start = timeit.default_timer()
                img_encoded = cv2.imencode('.jpg', image_result)[1]
                response = requests.post(IP_ADDRESS, data=img_encoded.tostring())
                done = response.status_code
                stop = timeit.default_timer()
                print('Transmission Time: ', stop - start)
            else:
                image_array = image.Convert(PySpin.PixelFormat_RGB8, PySpin.NEAREST_NEIGHBOR).GetNDArray()
                image_result = resizeImage(image_array, (1000,1000)) # downscale image
                stop = timeit.default_timer()
                print('Processing Time: ', stop - start)
                buff = io.BytesIO()
                start = timeit.default_timer()
                img_encoded = cv2.imencode('.jpg', image_result)[1]
                response = requests.post(IP_ADDRESS, data=img_encoded.tostring())
                done = response.status_code
                stop = timeit.default_timer()
                print('Transmission Time: ', stop - start)
                #qual = PySpin.JPEGOption()
                #qual.quality = 100
                #filename = os.path.join("/home/nvidia/trial/image{}.jpg".format(i))
                #print(filename)
                #image_result.Save(filename, qual)
            

    # deinitialize camera   
    cam.EndAcquisition()
    cam.DeInit()
    del cam

def main(apply_downscale, framerate, num_images, image_dir):
    IMAGE_DIR = image_dir
    print(IMAGE_DIR)
    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras() # get list of cameras
    if cam_list.GetSize() == 0: # exit if no cameras detected
        cam_list.Clear()
        system.ReleaseInstance()
        print("No cameras")
        input("Done! Press Enter to exit...")
        return False
    cam = cam_list.GetByIndex(0) # get camera
    # configure_custom_image_settings(cam) # configure camera settings
    capture(cam, apply_downscale, framerate, num_images)
    # shut down
    cam_list.Clear()
    del cam
    system.ReleaseInstance()

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
