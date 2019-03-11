# ======================================================================================================================================================================= #
#-------------> Project 02 <---------------#
# ======================================================================================================================================================================= #
# Course    :-> ENPM673 - Perception for Autonomous Robots
# Date      :-> 13 March 2019
# Authors   :-> Niket Shah(UID: 116345156), Siddhesh(UID: 116147286), Sudharsan(UID: 116298636)
# ======================================================================================================================================================================= #

# ======================================================================================================================================================================= #
# Import Section for Importing library
# ======================================================================================================================================================================= #

import time
import sys
import copy
import numpy as np
import cv2 as cv

# ======================================================================================================================================================================= #
# Function Definition Section
# ======================================================================================================================================================================= #
def adjust_lane(x, y, img):
    new_x = 0
    i = 0
    while i < 100:
        rect_right = img[y-10:y+10, x+i-10:x+i+10]
        hist_right = np.sum(rect_right[:, :], axis=0)
        try:
            if hist_right.mean() > 400:
                new_x = x + i
                # x_dot = np.where(hist_left == np.amax(hist_left[:]))
                return new_x
            rect_left = img[y-10:y+10, x-i-10:x-i+10]
            hist_left = np.sum(rect_left[:, :], axis=0)
            if hist_left.mean() > 400:
                # x_dot = np.where(hist_right == np.amax(hist_right[:]))
                new_x = x - i
                return new_x
        except:
            new_x = None

        i += 1
    return new_x


def fit_curve(left_lanex, left_laney, right_lanex, right_laney, img):

    try:
        left_coeffs = np.polyfit(left_laney, left_lanex, 2)
        right_coeffs = np.polyfit(right_laney, right_lanex, 2)

        plot_xy = np.linspace(0, img.shape[0] - 1, img.shape[0])
        fit_left = left_coeffs[0]*plot_xy**2 + left_coeffs[1]*plot_xy + left_coeffs[2]
        fit_right = right_coeffs[0]*plot_xy**2 + right_coeffs[1]*plot_xy + right_coeffs[2]


        left_line_window1 = np.array([np.transpose(np.vstack([fit_left-5, plot_xy]))])
        left_line_window2 = np.array([np.flipud(np.transpose(np.vstack([fit_left+5, plot_xy])))])
        left_line_pts = np.hstack((left_line_window1, left_line_window2))
        right_line_window1 = np.array([np.transpose(np.vstack([fit_right-5, plot_xy]))])
        right_line_window2 = np.array([np.flipud(np.transpose(np.vstack([fit_right+5, plot_xy])))])
        right_line_pts = np.hstack((right_line_window1, right_line_window2))

        # Draw the lane onto the warped blank image
        cv.fillPoly(img, np.int_([left_line_pts]), (255, 255, 255))
        cv.fillPoly(img, np.int_([right_line_pts]), (255, 255, 255))
    except:
        pass

# ======================================================================================================================================================================= #
# Lane Detection codes
# ======================================================================================================================================================================= #
if __name__ == '__main__':

    # Importing the Video
    # =================================================================================================================================================================== #
    cap = cv.VideoCapture('Data/project_video.mp4')
    #cap = cv.VideoCapture('Data/challenge_video.mp4')
    count = 0

    # ============================================================================================================================================================= #
    # Camera Parameters
    # ============================================================================================================================================================= #
    K = np.array([[1.15422732e+03, 0.00000000e+00, 6.71627794e+02],
                  [0.00000000e+00, 1.14818221e+03, 3.86046312e+02],
                  [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]])
    dist = np.array([-2.42565104e-01, - 4.77893070e-02, -
                     1.31388084e-03, - 8.79107779e-05, 2.20573263e-02])

    key_frame = cv.imread('Frames/frame331.jpg', 1)
    shawdow1 = cv.imread('Frames/frame538.jpg', 1)
    shawdow2 = cv.imread('Frames/frame549.jpg', 1)
    shawdow3 = cv.imread('Frames/frame573.jpg', 1)
    h,  w = key_frame.shape[:2]
    newmatrix, roi = cv.getOptimalNewCameraMatrix(K, dist, (w, h), 0)

    reference = np.array([[600, 450], [715, 450], [1280, 670], [185, 670]])
    target = np.array([[300, 0], [600, 0], [600, 600], [300, 600]])

    H_mat, status = cv.findHomography(reference, target)

    while True:
        # Capture frame-by-frame
        ret, key_frame = cap.read()
        # if frame is read correctly ret is True
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break
        # ============================================================================================================================================================= #
        # Removing Distortion in the Image
        # ============================================================================================================================================================= #
        key_frame = cv.undistort(key_frame, K, dist, None, newmatrix)

        # ============================================================================================================================================================= #
        # Denoising the Image
        # ============================================================================================================================================================= #
        # denoised_kf = cv.fastNlMeansDenoisingColored(key_frame, None, 10, 10, 7, 15)
        denoised_kf = cv.bilateralFilter(key_frame, 9, 75, 75)
        
        # ============================================================================================================================================================= #
        # Unwarpping the Image
        # ============================================================================================================================================================= #
        bird_view = cv.warpPerspective(denoised_kf, H_mat, (900, 600))
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        bird_view = cv.filter2D(bird_view, -1, kernel)
        # =================================================================================================================================================================== #
        # Improving contrast
        # =================================================================================================================================================================== #
        lab = cv.cvtColor(bird_view, cv.COLOR_BGR2LAB)
        l, a, b = cv.split(lab)        
        clahe = cv.createCLAHE(clipLimit=5.0, tileGridSize=(8, 8))        
        cl = clahe.apply(l)
        ca = clahe.apply(a)
        cb = clahe.apply(b)
        flag = cb > 175
        cb[flag] = 255  
        cl[flag] = 255
        ca[flag] = 170           
        limg = cv.merge((cl, ca, cb))
        cv.imshow('limg', limg)
        bird_view = cv.cvtColor(limg, cv.COLOR_LAB2BGR)
        bird_view = cv.bilateralFilter(bird_view, 9, 90, 90)
        cv.imshow('CLAHE output', bird_view)
        # ============================================================================================================================================================= #
        # Thresholding the Unwarpped Image
        # ============================================================================================================================================================= #
        warped_gray = cv.cvtColor(bird_view, cv.COLOR_BGR2GRAY)
        ret, thresh_warped = cv.threshold(warped_gray, 200, 255, cv.THRESH_BINARY)
        cv.imshow("xc,", thresh_warped)
        sobelx = cv.Sobel(bird_view, cv.CV_64F, 1, 0, ksize=5)
        sobely = cv.Sobel(warped_gray, cv.CV_64F, 0, 1, ksize=5)
        abs_sobely = np.absolute(sobely)
        sobely_u8 = np.uint8(abs_sobely)
        laplacian = cv.Laplacian(thresh_warped, cv.CV_64F)
        mask = cv.bitwise_and(thresh_warped, sobely_u8)
        histogram = np.sum(mask[300:, 250:650], axis=0)
        # plt.plot(histogram)
        midpoint = np.int(histogram.shape[0]/2)
        left_lane_base = np.where(histogram == np.amax(histogram[:midpoint]))
        right_lane_base = np.where(histogram == np.amax(histogram[midpoint:]))
        left_lane_basex = left_lane_base[0][0] + 250
        right_lane_basex = right_lane_base[0][0] + 250
        mask_copy = copy.copy(mask)
        cv.circle(mask_copy, (left_lane_basex, 580), 5, (255, 0, 255), -1)
        cv.circle(mask_copy, (right_lane_basex, 580), 5, (255, 0, 255), -1)

        # # Get boxes on the lane points and fit curve
        # y = mask.shape[1]
        # left_lane_currentx = left_lane_basex
        # right_lane_currentx = right_lane_basex
        # left_lanex = []
        # left_laney = []
        # right_lanex = []
        # right_laney = []

        # left_lanex.append(left_lane_currentx)
        # left_laney.append(y)
        # right_lanex.append(right_lane_currentx)
        # right_laney.append(y)

        # while(y > 10):
        #     left_lane_newx = adjust_lane(left_lane_currentx, y, mask_copy)    
        #     right_lane_newx = adjust_lane(right_lane_currentx, y, mask_copy)
            
        #     if left_lane_newx != 0:
        #         cv.rectangle(mask_copy,(left_lane_newx-10,y-10),(left_lane_newx+10,y+10),(255,255,255),3) 
        #         left_lanex.append(left_lane_newx)
        #         left_laney.append(y)
        #     if right_lane_newx != 0:
        #         cv.rectangle(mask_copy,(right_lane_newx-10,y-10),(right_lane_newx+10,y+10),(255,255,255),3)    
        #         right_lanex.append(right_lane_newx)
        #         right_laney.append(y)

        #     left_lane_currentx = left_lane_newx
        #     right_lane_currentx = right_lane_newx

        #     y -= 20

        # fit_curve(left_lanex, left_laney, right_lanex, right_laney, mask_copy)


        cv.imshow("Masked", mask_copy)
        cv.imshow("Original", key_frame)
        # ============================================================================================================================================================= #
        # Thresholding the Unwarpped Image
        # ============================================================================================================================================================= #

        # ============================================================================================================================================================= #
        # Thresholding the Unwarpped Image
        # ============================================================================================================================================================= #

        if cv.waitKey(2) == ord('q'):
            break

    # ================================================================================================================================================================= #
    # Computation Section
    # ================================================================================================================================================================= #

    cap.release()
    cv.destroyAllWindows()
