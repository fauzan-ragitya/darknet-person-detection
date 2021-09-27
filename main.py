from ctypes import *
import random
import os
import cv2
import time
import darknet
import argparse
from threading import Thread, enumerate
from queue import Queue
from adafruit_servokit import ServoKit
import board
import busio

def parser():
    parser = argparse.ArgumentParser(description="YOLO Object Detection")
    parser.add_argument("--input", type=str, default=0,
                        help="video source. If empty, uses webcam 0 stream")
    parser.add_argument("--out_filename", type=str, default="",
                        help="inference video name. Not saved if empty")
    parser.add_argument("--weights", default="custom-yolov4-tiny-detector_best.weights",
                        help="yolo weights path")
    parser.add_argument("--dont_show", action='store_true',
                        help="windown inference display. For headless systems")
    parser.add_argument("--ext_output", action='store_true',
                        help="display bbox coordinates of detected objects")
    parser.add_argument("--config_file", default="./cfg/custom-yolov4-tiny-detector.cfg",
                        help="path to config file")
    parser.add_argument("--data_file", default="./cfg/obj.data",
                        help="path to data file")
    parser.add_argument("--thresh", type=float, default=.25,
                        help="remove detections with confidence below this value")
    return parser.parse_args()


def str2int(video_path):
    """
    argparse returns and string althout webcam uses int (0, 1 ...)
    Cast to int if needed
    """
    try:
        return int(video_path)
    except ValueError:
        return video_path


def check_arguments_errors(args):
    assert 0 < args.thresh < 1, "Threshold should be a float between zero and one (non-inclusive)"
    if not os.path.exists(args.config_file):
        raise(ValueError("Invalid config path {}".format(os.path.abspath(args.config_file))))
    if not os.path.exists(args.weights):
        raise(ValueError("Invalid weight path {}".format(os.path.abspath(args.weights))))
    if not os.path.exists(args.data_file):
        raise(ValueError("Invalid data file path {}".format(os.path.abspath(args.data_file))))
    if str2int(args.input) == str and not os.path.exists(args.input):
        raise(ValueError("Invalid video path {}".format(os.path.abspath(args.input))))


def set_saved_video(input_video, output_video, size):
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    fps = int(input_video.get(cv2.CAP_PROP_FPS))
    video = cv2.VideoWriter(output_video, fourcc, fps, size)
    return video

def lepton_pipeline():
    return "v4l2src device=/dev/video0 ! video/x-raw, format= GRAY8 ! videoconvert ! appsink max-buffers=1 drop=true "

def video_capture(frame_queue, darknet_image_queue):
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_resized = cv2.resize(frame_rgb, (width, height),
                                   interpolation=cv2.INTER_LINEAR)
        frame_queue.put(frame_resized)
        img_for_detect = darknet.make_image(width, height, 3)
        darknet.copy_image_from_bytes(img_for_detect, frame_resized.tobytes())
        darknet_image_queue.put(img_for_detect)
    cap.release()

def inference(darknet_image_queue, detections_queue, fps_queue):
    while cap.isOpened():
        darknet_image = darknet_image_queue.get()
        prev_time = time.time()
        detections = darknet.detect_image(network, class_names, darknet_image, thresh=args.thresh)
        detections_queue.put(detections)
        fps = int(1/(time.time() - prev_time))
        fps_queue.put(fps)
        print("FPS: {}".format(fps))
        if detections:
            for label, confidence, bbox in detections:
                mid_x, mid_y, w, h = bbox
            print('Midpoint X: ', mid_x)
            print('Midpoint Y: ', mid_y)
            # print('Width: ', w)
            # print('Height: ',h)
            # print('Windows width', width)
            # print('Windows height', height)
            #Imageservoing
            # Pan = 0
            # Tilt = 4
            #Pan movement
            width_range = mid_x - (width/2)
            print('width range', width_range) #error horizontal
            if width_range < -40 and (kit.servo[0].angle > 10 and kit.servo[0].angle < 170):
                kit.servo[0].angle += 1
                print('pan servo angle', kit.servo[0].angle)
            elif width_range > 40 and (kit.servo[0].angle > 10 and kit.servo[0].angle < 170):
                kit.servo[0].angle -= 1
                print('pan servo angle', kit.servo[0].angle)
            if kit.servo[0].angle >= 170:
                kit.servo[0].angle = 169
                print('max pan angle')
            elif kit.servo[0].angle <= 10:
                kit.servo[0].angle = 11
                print('min pan angle')
            #Tilt movement
            height_range = mid_y - (height/2)
            print('height range', height_range)
            if height_range <-30 and (kit.servo[4].angle > 80 and kit.servo[4].angle < 139):
                kit.servo[4].angle -= 1
                print('servo angle', kit.servo[4].angle)
            elif height_range > 30 and (kit.servo[4].angle > 80 and kit.servo[4].angle < 139):
                kit.servo[4].angle += 1
                print('servo angle', kit.servo[4].angle)
            if kit.servo[4].angle <= 80:
                kit.servo[4].angle = 81
                print('max tilt angle')
            elif kit.servo[4].angle >= 140:
                kit.servo[4].angle = 139
                print('max tilt angle')
        darknet.print_detections(detections, args.ext_output)
        darknet.free_image(darknet_image)
    cap.release()

def drawing(frame_queue, detections_queue, fps_queue):
    random.seed(3)  # deterministic bbox colors
    video = set_saved_video(cap, args.out_filename, (width, height))
    while cap.isOpened():
        frame_resized = frame_queue.get()
        detections = detections_queue.get()
        fps = fps_queue.get()
        if frame_resized is not None:
            image = darknet.draw_boxes(detections, frame_resized, class_colors)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            if args.out_filename is not None:
                video.write(image)
            if not args.dont_show:
                cv2.imshow('Inference', image)
            if cv2.waitKey(fps) == 27:
                break
    cap.release()
    video.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    frame_queue = Queue()
    darknet_image_queue = Queue(maxsize=1)
    detections_queue = Queue(maxsize=1)
    fps_queue = Queue(maxsize=1)

    args = parser()
    check_arguments_errors(args)
    network, class_names, class_colors = darknet.load_network(
            args.config_file,
            args.data_file,
            args.weights,
            batch_size=1
        )
    print("Initializing Servos")
    i2c_bus0=(busio.I2C(board.SCL_1, board.SDA_1))
    print("Initializing ServoKit")
    kit = ServoKit(channels=16, i2c=i2c_bus0)
    # kit[0] is the bottom servo
    # kit[1] is the top servo
    print("Done initializing")
    #set pulse width range
    kit.servo[0].set_pulse_width_range(500, 2500)
    kit.servo[4].set_pulse_width_range(500, 2500)
    kit.servo[0].angle = 90
    kit.servo[4].angle = 120
    #width = darknet.network_width(network)
    width = 800
    #height = darknet.network_height(network)
    height = 600
    input_path = str2int(args.input)
    pipeline = lepton_pipeline()
    # cap = cv2.VideoCapture(0)
    # cap = cv2.VideoCapture(pipeline)
    # cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
    cap = cv2.VideoCapture(input_path)
    Thread(target=video_capture, args=(frame_queue, darknet_image_queue)).start()
    Thread(target=inference, args=(darknet_image_queue, detections_queue, fps_queue)).start()
    Thread(target=drawing, args=(frame_queue, detections_queue, fps_queue)).start()

# pisah
