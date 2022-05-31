""""
Module to define helper functions
"""
# =====================================================================
# Import modules
# =====================================================================

# Import internal modules
# import math
from pathlib import Path
# import random
from typing import Dict, List, Optional, Set, Tuple, TypedDict

# Import 3rd party modules
import cv2
import numpy as np
from scipy.interpolate import interp1d
import tensorflow as tf
from matplotlib import colors

# Import local modules
from pose_estimation.play_with_particles.particle import Particle
from core.utils.renderer.get_resize_interpolation import get_interpolation

# =====================================================================
# Define functions
# =====================================================================

def get_line_range_iterator(start_xy:tuple, end_xy:tuple, interpolation_kind:Optional[str]='linear'):
    """
    Function to get line range iterator from start xy coords and end xy coords
    """
    start_x, start_y = start_xy
    end_x, end_y = end_xy
    
    if start_x > end_x:
        start_x, end_x = end_x, start_x
    if start_y > end_y:
        start_y, end_y = end_y, start_y

    delta_x = np.abs(end_x - start_x)
    delta_y = np.abs(end_y - start_y)

    if delta_x >= delta_y:

        # get range of integers
        X = np.arange(start_x, end_x + 1, dtype=np.uint64)

        # get y range with same number of data points as in x range
        Y = np.linspace(start_y, end_y, delta_x + 1, dtype=np.uint64)

        # create interpolate object
        interp1d_fct= interp1d(X, Y, kind = interpolation_kind)

        # get interpolated data
        Y = interp1d_fct(X)

    else:

        # get range of integers
        Y = np.arange(start_y, end_y + 1, dtype=np.uint64)

        # get x range with same number of data points as in y range
        X = np.linspace(start_x, end_x, delta_y + 1, dtype=np.uint64)
        
        # create interpolate object
        interp1d_fct= interp1d(Y, X, kind = interpolation_kind)

        # get interpolated data
        X = interp1d_fct(Y)
        
    # return line range of xy points
    return zip(X, Y)

def draw_keypoints(frame, keypoints, confidence_threshold, radius=4, color=(0,255,0), thickness=-1):
    """
    Function to draw only keypoints above a confidence threshold
    """
    # get frame height & width
    height, width = frame.shape[:2]
    
    # get keypoints coordinates in actual position in the frame & prediction confidence
    shaped = np.squeeze(np.multiply(keypoints, [height, width, 1]))
    
    # loop through each keypoint
    for ky, kx, kp_conf in shaped:
        
        # draw keypoint if confidence above threshold
        if kp_conf > confidence_threshold:
            cv2.circle(frame, (int(kx), int(ky)), radius, color, thickness, lineType=cv2.LINE_AA)
            
def draw_connections(frame, keypoints, edges, confidence_threshold, size_px, particle_mass, color, thickness=2, draw=True):
    """
    Function to draw connections between keypoints

    toTry:  cv2.polylines
    """
    # get frame height & width
    height, width = frame.shape[:2]
    
    # get keypoints coordinates in actual position in the frame & prediction confidence
    shaped = np.squeeze(np.multiply(keypoints, [height, width, 1]))

    line_particles = []
    
    # loop through each connection
    for edge, color in edges.items():
        
        # unpack keypoint numbers in connection tuple
        p1, p2 = edge
        
        # get color bgr values
        color_bgr = np.array(colors.to_rgb(color)[::-1])*255
        
        # unpack keypoints coords & prediction confidences
        y1, x1, c1 = shaped[p1]
        y2, x2, c2 = shaped[p2]

        x1, y1 = int(x1), int(y1)
        x2, y2 = int(x2), int(y2)
        
        if draw:
            # draw line if both confidences are above thresholds
            if (c1 > confidence_threshold) & (c2 > confidence_threshold):
                cv2.line(frame, (x1, y1), (x2, y2), color_bgr, thickness=2)
        
        try:
            # convert each pixel from pose connection to particles
            for x_px,y_px in get_line_range_iterator((x1, y1), (x2, y2)):

                x_px, y_px = int(x_px), int(y_px)
                
                # # set color to particles: mean of region of interest in frame (position where particles initially start)
                # # get roi in frame
                # roi = first_frame[y_px - size_px//2:y_px + size_px//2, x_px - size_px//2:x_px + size_px//2]
                # # get mean of roi
                # roi_mean = cv2.mean(roi)[:-1]
                
            # for line_particle in np.arange(0, world.width_px, dtype=int):
                line_particle = Particle(
                    f"{x_px},{y_px}",
                    (x_px, y_px),
                    size_px=size_px,
                    mass=particle_mass, # ToDo: play with color intensity to represent mass
                    color=color, # color=roi_mean,
                    thickness=thickness
                    ) 
                line_particles.append(line_particle)
        except:
            print("fail for:", (x1, y1), (x2, y2))
            
    return line_particles

def draw_mediapipe_connections(frame, lines, size_px, particle_mass, thickness=2, draw=True, color='b'):
    """
    Function to draw connections between keypoints

    toTry:  cv2.polylines
    """
    
    line_particles = []
    
    # loop through each connection
    for edge in lines:
        
        # unpack keypoint numbers in connection tuple
        p1, p2 = edge
        
        # get color bgr values
        color_bgr = np.array(colors.to_rgb(color)[::-1])*255
        
        # unpack keypoints coords
        x1, y1 = p1
        x2, y2 = p2

        x1, y1 = int(x1), int(y1)
        x2, y2 = int(x2), int(y2)
        
        if draw:
            # draw line if both confidences are above thresholds
            cv2.line(frame, (x1, y1), (x2, y2), color_bgr, thickness=thickness)
        
        try:
            # convert each pixel from pose connection to particles
            for x_px,y_px in get_line_range_iterator((x1, y1), (x2, y2)):

                x_px, y_px = int(x_px), int(y_px)
                
                # # set color to particles: mean of region of interest in frame (position where particles initially start)
                # # get roi in frame
                # roi = first_frame[y_px - size_px//2:y_px + size_px//2, x_px - size_px//2:x_px + size_px//2]
                # # get mean of roi
                # roi_mean = cv2.mean(roi)[:-1]
                
            # for line_particle in np.arange(0, world.width_px, dtype=int):
                line_particle = Particle(
                    f"{x_px}{y_px}",
                    (x_px, y_px),
                    size_px=size_px,
                    mass=particle_mass, # ToDo: play with color intensity to represent mass
                    color=color, # color=roi_mean,
                    thickness=thickness
                    ) 
                line_particles.append(line_particle)
        except:
            print("fail for:", (x1, y1), (x2, y2))
            
    return line_particles

def blend_transparent(face_img, overlay_t_img):
    # Split out the transparency mask from the colour info
    overlay_img = overlay_t_img[:,:,:3] # Grab the BRG planes
    overlay_mask = overlay_t_img[:,:,3:]  # And the alpha plane

    # Again calculate the inverse mask
    background_mask = 255 - overlay_mask

    # Turn the masks into three channel, so we can use them as weights
    overlay_mask = cv2.cvtColor(overlay_mask, cv2.COLOR_GRAY2BGR)
    background_mask = cv2.cvtColor(background_mask, cv2.COLOR_GRAY2BGR)

    # Create a masked out face image, and masked out overlay
    # We convert the images to floating point in range 0.0 - 1.0
    face_part = (face_img * (1 / 255.0)) * (background_mask * (1 / 255.0))
    overlay_part = (overlay_img * (1 / 255.0)) * (overlay_mask * (1 / 255.0))

    # And finally just add them together, and rescale it back to an 8bit integer image    
    return np.uint8(cv2.addWeighted(face_part, 255.0, overlay_part, 255.0, 0.0))


def detect(frame, interpreter, tensor_dtype=tf.float32):
    """
    Function to infer predictions using tflite models
    """
    # 1. reshape frame to model input shape 
    # copy frame
    img = frame.copy()
    
    # expand dimension (to add the batch size, here it would be 1) & resize with padding
#     img = tf.image.resize_with_pad(np.expand_dims(img, axis=0), 192, 192)
    img = tf.image.resize_with_pad(np.expand_dims(img, axis=0), 256, 256)
    
    # convert image into a tensor
    input_image = tf.cast(img, dtype=tensor_dtype)
    
    # 2. get input & output details
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    # 3. make predictions
    # set index of input details to the image
    interpreter.set_tensor(input_details[0]['index'], np.array(input_image))
    
    # invoke predictions
    interpreter.invoke()
    
    # get predictions (from index of output_details): keypoints_with_scores
    return interpreter.get_tensor(output_details[0]['index'])

def draw_particle(particle, frame, transparent_img=None):
    """
    Function to draw particle or put transparent images instead

    # toAdd: rotation of transparent image
    """
    x, y = int(particle.x_px), int(particle.y_px)

    # by default, draw circle
    if transparent_img is None:
        frame = cv2.circle(frame, (x, y), particle.size_px, particle.color, particle.thickness, lineType=cv2.LINE_AA)

    else:
        # resize transparent_img to particle size
        interpolation = get_interpolation(transparent_img.shape, out_img_shape=(particle.size_px,particle.size_px))
        transparent_img = cv2.resize(transparent_img, (particle.size_px*2,particle.size_px*2), interpolation=interpolation)

        transparent_img_height, transparent_img_width = transparent_img.shape[:2]

        # get center of image
        center_x, center_y = (transparent_img_height // 2, transparent_img_width // 2)

        # rotate our image by given degrees around the center of the image
        M = cv2.getRotationMatrix2D((center_x, center_y), particle.angle, 1.0)
        transparent_img = cv2.warpAffine(transparent_img, M, (transparent_img_width, transparent_img_height))
        
        y_lower = y - transparent_img_height//2
        y_upper = y + transparent_img_height//2
        x_lower = x - transparent_img_width//2
        x_upper = x + transparent_img_width//2

        frame_height, frame_width = frame.shape[:2]
        delta_y_upper, delta_y_lower, delta_x_upper, delta_x_lower = 0,0,0,0
        if y_upper > frame_height:
            delta_y_upper = y_upper - frame_height
            y_upper = frame_height

        if y_lower < 0:
            delta_y_lower = - y_lower
            y_lower = 0
        
        if x_upper > frame_width:
            delta_x_upper = x_upper - frame_width
            x_upper = frame_width

        if x_lower < 0:
            delta_x_lower = - x_lower
            x_lower = 0


        # get region of interest in frame (where to place transparent img)
        roi = frame[y_lower:y_upper, x_lower:x_upper]

        roi_height, roi_width = roi.shape[:2]

        t_img_y_lower = delta_y_lower
        t_img_y_upper = transparent_img_height - delta_y_upper
        t_img_x_lower = delta_x_lower
        t_img_x_upper = transparent_img_width - delta_x_upper

        # if transparent image has not completely disappear from frame, draw it
        if t_img_y_upper > t_img_y_lower and t_img_x_upper > t_img_x_lower:

            # add transparent img in roi
            roi = blend_transparent(roi, transparent_img[t_img_y_lower:t_img_y_upper, t_img_x_lower:t_img_x_upper, :]) # crop t img if particle exceeds frame borders
            frame[y_lower:y_upper, x_lower:x_upper] = roi    

    return frame