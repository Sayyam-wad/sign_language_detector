# import os
# import cv2
# import time
# import argparse

# from utils import last_count
# from utils import save_image
# from utils import region_of_interest



# def generate_data(device: int = 0) -> None:
# 	"""
# 	Captures images through the webcam and saves them in the specified path.

# 	Keyword Arguments:
# 		device {int} -- webcam device to use (default: {0})
# 	"""
# 	# get the path to the label
# 	path = os.path.join(args.data, args.label)
# 	os.makedirs(path, exist_ok=True)

# 	# get the last numeric count
# 	start = last_count(path)

# 	# give the user a 10-second grace period before starting the capture
# 	capture = cv2.VideoCapture(0)
# 	grace = 10
# 	t_end = time.time() + grace
# 	print(f'Get ready and position yourself! Starting capture in {grace} seconds...')

# 	cnt = i = 0
# 	while cnt < args.images:
# 		_, frame = capture.read()
# 		frame = cv2.flip(frame, 1)
# 		roi = region_of_interest(frame)

# 		# show results
# 		cv2.imshow('Live Feed', frame)

# 		# force exit condition
# 		if cv2.waitKey(1) & 0xFF == ord('q'):
# 			print('You force quit.')
# 			break

# 		if time.time() <= t_end:	# discard frames captured during the grace period
# 			continue
# 		elif i % args.fps == 0:		# save image after fps frames
# 			cnt += 1
# 			file_name = f'{args.label}_{start + cnt}.png'
# 			file_path = os.path.join(path, file_name)
# 			save_image(roi, file_path)
# 			print(f'Generated image {cnt} out of {args.images}.')
		
# 		i += 1
	
# 	# clean-up
# 	capture.release()
# 	cv2.destroyAllWindows()



# if __name__ == '__main__':
# 	# add keyword arguments
# 	parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
# 	parser.add_argument('--data', '-d', help='Path to a directory to output generated images', required=True)
# 	parser.add_argument('--label', '-l', help='Label of the generated images', required=True)
# 	parser.add_argument('--images', '-i', help='Number of images to generate', type=int, default=500)
# 	parser.add_argument('--fps', '-f', help='Number of frames to skip before capturing the next', type=int, default=10)
# 	args = parser.parse_args()
	
# 	generate_data()


import os

import cv2


DATA_DIR = 'E:/Projects/sign_language_working_project/data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

number_of_classes = 17
dataset_size = 100

cap = cv2.VideoCapture(0)
for j in range(12,number_of_classes):
    if not os.path.exists(os.path.join(DATA_DIR, str(j))):
        os.makedirs(os.path.join(DATA_DIR, str(j)))

    print('Collecting data for class {}'.format(j))

    done = False
    while True:
        ret, frame = cap.read()
        cv2.putText(frame, 'Ready? Press "Q" ! :)', (100, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 255, 0), 3,
                    cv2.LINE_AA)
        cv2.imshow('frame', frame)
        if cv2.waitKey(25) == ord('q'):
            break

    counter = 0
    while counter < dataset_size:
        ret, frame = cap.read()
        cv2.imshow('frame', frame)
        cv2.waitKey(25)
        cv2.imwrite(os.path.join(DATA_DIR, str(j), '{}.jpg'.format(counter)), frame)

        counter += 1

cap.release()
cv2.destroyAllWindows()
