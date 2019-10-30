import PySpin
import os
import imgurUrlGenerator
import timeit
from PIL import Image
import numpy as np
from skimage import transform 
import imageio
import sys, getopt
import argparse

NUM_IMAGES = 1
save_folder = "D:\Documents\AIAA"

def capture(cam, apply_downscale, framerate, num_images):
    cam.Init() # start camera

    cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous) # set acquisition mode to continuous
    cam.AcquisitionFrameRateEnable.SetValue(True)
    cam.AcquisitionFrameRate.SetValue(int(framerate))
    cam.BeginAcquisition()

    for i in range(int(num_images)):
    # while(True):
        start = timeit.default_timer()
        image = cam.GetNextImage() # acquire image

        if image.IsIncomplete():
            print("Image incomplete with image status %d..." % image.GetImageStatus())
        else: 
            if(apply_downscale):
                image_array = image.Convert(PySpin.PixelFormat_RGB8, PySpin.NEAREST_NEIGHBOR).GetNDArray() # turn image into ND array
                image_result = transform.downscale_local_mean(image_array, (5, 5, 1)).astype(np.uint8) # downscale image
                 # print runtime
                stop = timeit.default_timer()
                print('Time: ', stop - start) 
                imageio.imsave('{}/image{}.jpg'.format(save_folder, i), image_result) # save image
            else:
                image_result = image.Convert(PySpin.PixelFormat_RGB8, PySpin.NEAREST_NEIGHBOR)
                 # print runtime
                stop = timeit.default_timer()
                print('Time: ', stop - start) 
                qual = PySpin.JPEGOption()
                qual.quality = 100
                image_result.Save('{}/image{}.jpg'.format(save_folder, i), qual)
            

    # deinitialize camera   
    cam.EndAcquisition()
    cam.DeInit()
    del cam

def main(apply_downscale, framerate, num_images):
    # parse arguments
    # parser = argparse.ArgumentParser()
    # parser.add_argument("apply_downscale")
    # parser.add_argument("framerate")

    # args = parser.parse_args()
    # apply_downscale = str(args.apply_downscale)
    # framerate = str(args.framerate)

    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras() # get list of cameras
    if cam_list.GetSize() == 0: # exit if no cameras detected
        cam_list.Clear()

        system.ReleaseInstance()
        print("No cameras")
        input("Done! Press Enter to exit...")
        return False
    
    cam = system.GetCameras().GetByIndex(0) # get camera
    # configure_custom_image_settings(cam) # configure camera settings
    capture(cam, apply_downscale, framerate, num_images)

    # shut down
    cam_list.Clear()
    del cam
    system.ReleaseInstance()

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
