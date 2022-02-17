"""
Program to detect and extract faces in images
"""
# =====================================================================
# Import modules
# =====================================================================

# import internal modules
from typing import List, Set, Dict, TypedDict, Tuple, Optional, Union
from pathlib import Path
import glob
import os


# import 3rd-party modules
import cv2
import numpy as np


# import local modules
from core.utils.image_pather import get_img_paths

# =====================================================================
# Define functions
# =====================================================================

def detect_face(input_dir, output_dir, bbox_width=12, bbox_height=16):
    """
    Function to detect and extract faces in images
    """
    # import classifier
    face_cascade = cv2.CascadeClassifier("core/utils/face_detector/models/haarcascade_frontalface_default.xml")

    # get image paths
    img_paths = get_img_paths(input_dir)

    # initialize empty list & counter
    imgs = []
    count = 0

    # loop over each image path
    for img_path in img_paths:

        # read image
        img = cv2.imread(img_path)

        # convert image to grayscale & equalize histogram (ToSearch: to improve classifier performance?)
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img_gray = cv2.equalizeHist(img_gray)

        # detect faces (bounding boxes)
        faces = face_cascade.detectMultiScale(img_gray, scaleFactor=1.3, minNeighbors=10, minSize=(350, 350), flags=cv2.CASCADE_SCALE_IMAGE)
        
        # loop over each detected face bounding box
        for (x, y, w, h) in faces:

            # get region of interest (part of image within the bounding box)
            roi = img[y:y+h, x:x+w]

            # resize region of interest
            out_img = cv2.resize(roi, (bbox_width, bbox_height))

            # append image to list of images
            imgs.append(out_img)

            # convert to Path if input_dir is a string
            if isinstance(output_dir, str):
                output_dir = Path(output_dir)
            
            # set output image path
            out_path = str(output_dir / f"face_{count:05d}.jpg")
            
            # save image on disk
            cv2.imwrite(out_path, out_img)

            # increment counter by 1
            count += 1

    return np.stack(imgs)


# =====================================================================
# Run demo
# =====================================================================

# run demo if this py file is run
if __name__ == "__main__":

    # declare constants & variables
    BBOX_WIDTH = 12
    BBOX_HEIGHT = 16

    # set input directory
    input_dir = Path("")

    # set directory where to save the images
    output_dir = Path("/Users/derrickvanfrausum/BeCode_AI/git-repos/coding-art/core/assets/images/pexels/small_faces")

    # make directory if doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # extract faces
    imgs = detect_face(input_dir, output_dir, BBOX_WIDTH, BBOX_HEIGHT)