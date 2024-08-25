import os

import cv2
import time
import glob
from send_mail import send_mail, clean_img_folder
from threading import Thread

MAX_IMAGES = 3
IMAGE_DIR = "images"
TEMP_IMAGE_DIR = "temporary_images"

# Create directories if they don't exist
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)

video = cv2.VideoCapture(0)
time.sleep(1)
# define first frame and status list
first_frame = None
status_list = []

# initialize variables
image_paths = []
middle_image = os.path.join(IMAGE_DIR, "fondo.jpg")
image_count = 1

try:
    while True:
        status = 0
        check, frame = video.read()
        # preprocessing of the video, make it grey
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_frame_gau = cv2.GaussianBlur(gray_frame, (21, 21), 0)

        # save the first frame to compare with new frames
        if first_frame is None:
            first_frame = gray_frame_gau
            continue

        # frame where it shows difference between first and current frame
        delta_frame = cv2.absdiff(first_frame, gray_frame_gau)
        # optimize the delta frame to only have white or black
        thresh_frame = cv2.threshold(delta_frame, 60, 255,
                                     cv2.THRESH_BINARY)[1]
        dil_frame = cv2.dilate(thresh_frame, None, iterations=2)

        # define contours of the found shapes to display them in rectangles
        contours, _ = cv2.findContours(dil_frame, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            if cv2.contourArea(contour) < 5000:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            rectangle = cv2.rectangle(frame, (x, y), (x + w, y + h),
                                      (0, 255, 0), 5)
            # if object enters frame change status and save images
            if rectangle.any():
                status = 1
                cv2.imwrite(f"images/{image_count}.png", frame)
                image_count += 1
                all_images = glob.glob(os.path.join(IMAGE_DIR, "*.png"))
                # get middle image path from all the saved images (int)
                middle_image = all_images[(len(all_images) // 2)]

        status_list.append(status)
        status_list = status_list[-2:]

        # when moving object is out of frame list updates from 1 to 0
        if status_list[0] == 1 and status_list[1] == 0:
            temp_image_path = os.path.join(TEMP_IMAGE_DIR,
                                           os.path.basename(middle_image))
            # Copy the middle image to the temporary directory
            if os.path.exists(middle_image):
                cv2.imwrite(temp_image_path, cv2.imread(middle_image))
            image_paths.append(temp_image_path)
            clean_img_folder()
            if len(image_paths) >= MAX_IMAGES:
                try:
                    email_thread = Thread(target=send_mail, args=(image_paths,))
                    email_thread.daemon = True
                    email_thread.start()
                    image_paths = []  # Reset the list after sending the email
                except Exception as e:
                    print(f"Error sending email: {e}")

        # show video
        cv2.imshow("My video", frame)

        # if press "q" video ends
        key = cv2.waitKey(1)
        if key == ord("q"):
            break

finally:
    # Ensure that remaining images are sent before exiting
    if image_paths:
        try:
            send_mail(image_paths)
        except Exception as e:
            print(f"Error sending final email: {e}")
# Release the video capture and close windows
video.release()
cv2.destroyAllWindows()
