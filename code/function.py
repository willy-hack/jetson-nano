import cv2 # type: ignore
import numpy as np
import pickle

# Load HSV values from the saved file
with open('hsv_values.pkl', 'rb') as f:
    hsv_values = pickle.load(f)


color_ranges = {
    'Orange': (hsv_values['qualifications_Orange'][0], hsv_values['qualifications_Orange'][1], (0, 165, 255)),
    'Blue': (hsv_values['qualifications_Blue'][0], hsv_values['qualifications_Blue'][1], (255, 0, 0))
}
color_ranges_final = {
    'Orange': (hsv_values['Orange_final'][0], hsv_values['Orange_final'][1], (0, 165, 255)),
    'Blue': (hsv_values['Blue_final'][0], hsv_values['Blue_final'][1], (255, 0, 0)),
    'Red': (hsv_values['Red'][0], hsv_values['Red'][1], (0, 0, 255)),
    'Green': (hsv_values['Green'][0], hsv_values['Green'][1], (0, 255, 0)),
    'Pink': (hsv_values['Pink'][0], hsv_values['Pink'][1], (255, 192, 203))
}

current_last = 0

def process_roi(undistorted_frame, x1, y1, x2, y2, threshold_value=90):
    roi = undistorted_frame[y1:y2, x1:x2]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY_INV)

    # Find all contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # If there are contours, find the largest contour
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        black_pixels = int(cv2.contourArea(largest_contour))  # Convert black pixel area to an integer
        # Draw the largest contour
        cv2.drawContours(binary, [largest_contour], -1, (255, 255, 255), -1)
    else:
        black_pixels = 0

    return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR), black_pixels

def detect_color(undistorted_frame):
    hsv_frame = cv2.cvtColor(undistorted_frame, cv2.COLOR_BGR2HSV)
    color_y_positions = []

    for color, (lower, upper, bgr) in color_ranges.items():
        lower = np.array(lower, dtype=np.uint8)
        upper = np.array(upper, dtype=np.uint8)
        color_mask = cv2.inRange(hsv_frame, lower, upper)
        contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest_contour) > 500:  # Filter small areas of noise
                x, y, w, h = cv2.boundingRect(largest_contour)
                center_y = y + h // 2
                cv2.rectangle(undistorted_frame, (x, y), (x + w, y + h), bgr, 2)
                cv2.circle(undistorted_frame, (x + w // 2, center_y), 5, bgr, -1)  # Mark the center point
                color_y_positions.append(center_y)
            else:
                color_y_positions.append(0)  # If no valid contour found, return 0
        else:
            color_y_positions.append(0)  # If no contour found, return 0

    return color_y_positions

def pd_control(target, current, kp, kd):
    global current_last  # Use a global variable
    error = current - target
    derivative = current - current_last
    control_signal = -(kp * error + kd * derivative)
    current_last = current  # Update current_last before returning
    return control_signal

def draw_multiple_curves(undistorted_frame, start_points, end_points, slope_values, curvature_factors, colors, thickness=2):
    """
    Draw multiple curves with different start and end points, slopes, and curvature on the image, 
    and return the coordinate list of the red curve.
    """
    red_curve_points = []  # Used to store red curve points
    green_curve_points = []  # Used to store green curve points

    for start_point, end_point, slope, curvature, color in zip(start_points, end_points, slope_values, curvature_factors, colors):
        x1, y1 = start_point
        x2, y2 = end_point

        # Calculate the middle control point to control the curvature
        mid_x = (x1 + x2) // 2
        mid_y = (y1 + y2) // 2
        control_x = mid_x
        control_y = int(mid_y - curvature * slope * (x2 - x1))  # Use curvature and slope to adjust the middle control point

        # Draw using Bezier curve
        curve_points = []
        for t in np.linspace(0, 1, 100):
            xt = (1 - t)**2 * x1 + 2 * (1 - t) * t * control_x + t**2 * x2
            yt = (1 - t)**2 * y1 + 2 * (1 - t) * t * control_y + t**2 * y2
            curve_points.append((int(xt), int(yt)))

        # If it is a red curve, save the coordinates
        if color == (0, 0, 255):  # Red curve
            red_curve_points = curve_points
        if color == (0, 255, 0):  # Green curve
            green_curve_points = curve_points

        # Draw the curve
        for i in range(len(curve_points) - 1):
            cv2.line(undistorted_frame, curve_points[i], curve_points[i + 1], color, thickness)

    return red_curve_points, green_curve_points  # Return the coordinates of the red and green curves

def draw_multiple_lines(undistorted_frame, start_points, end_points, x, thickness=2):
    """
    Draw multiple straight lines between start and end points on the image,
    and return the coordinate list of the red and green lines.
    """
    pink_left_points = []
    pink_right_points = []

    for start_point, end_point in zip(start_points, end_points):
        x1, y1 = start_point
        x2, y2 = end_point

        # Draw a straight line
        cv2.line(undistorted_frame, (x1, y1), (x2, y2),(255, 192, 203), thickness)

        # Store points if the color matches
        if x1 == x:  # Red
            pink_left_points = y1
        elif x1 == x:  # Green
            pink_right_points = y2

    return pink_left_points,pink_right_points

def detect_color_final(undistorted_frame, last_red_x_diff, last_green_x_diff,
                       start_points, end_points, slope_values, curvature_factors, colors,
                       start_points_pink, end_points_pink):
    hsv_frame = cv2.cvtColor(undistorted_frame, cv2.COLOR_BGR2HSV)
    color_y_positions = []
    pink_positions = [0] * 4
    center_x = 0
    center_y = 0
    red_x_diff = 0
    green_x_diff = 0
    pink_red_x_diff = 0
    pink_green_x_diff = 0
    pink_left_points = []
    pink_right_points = []

    red_curve_points, green_curve_points = draw_multiple_curves(
        undistorted_frame, start_points, end_points, slope_values, curvature_factors, colors
    )

    for color, (lower, upper, bgr) in color_ranges_final.items():
        lower = np.array(lower, dtype=np.uint8)
        upper = np.array(upper, dtype=np.uint8)
        color_mask = cv2.inRange(hsv_frame, lower, upper)
        contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if color == 'Pink':
            sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)
            top_two_contours = [cnt for cnt in sorted_contours[:2] if cv2.contourArea(cnt) > 500]

            if len(top_two_contours) > 0:
                x1, y1, w1, h1 = cv2.boundingRect(top_two_contours[0])
                center_x1 = x1 + w1 // 2
                center_y1 = y1 + h1 // 2
                pink_positions[0] = center_x1
                pink_positions[1] = center_y1
                cv2.rectangle(undistorted_frame, (x1, y1), (x1 + w1, y1 + h1), bgr, 2)
                cv2.circle(undistorted_frame, (center_x1, center_y1), 5, bgr, -1)

                if len(top_two_contours) > 1:
                    x2, y2, w2, h2 = cv2.boundingRect(top_two_contours[1])
                    center_x2 = x2 + w2 // 2
                    center_y2 = y2 + h2 // 2
                    pink_positions[2] = center_x2
                    pink_positions[3] = center_y2
                    cv2.rectangle(undistorted_frame, (x2, y2), (x2 + w2, y2 + h2), bgr, 2)
                    cv2.circle(undistorted_frame, (center_x2, center_y2), 5, bgr, -1)
            else:
                pink_positions[:] = [0, 0, 0, 0]
        else:
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                if cv2.contourArea(largest_contour) > 600:
                    x, y, w, h = cv2.boundingRect(largest_contour)
                    center_x = x + w // 2
                    center_y = y + h // 2
                    color_y_positions.append(center_y)
                    cv2.rectangle(undistorted_frame, (x, y), (x + w, y + h), bgr, 2)
                    cv2.circle(undistorted_frame, (center_x, center_y), 5, bgr, -1)
                else:
                    color_y_positions.append(0)
            else:
                color_y_positions.append(0)

        # Intersection check only for Red and Green
        if color == 'Red' and red_curve_points:
            max_curve_y = max(pt[1] for pt in red_curve_points)
            if center_y < max_curve_y:
                for curve_x, curve_y in red_curve_points:
                    if abs(curve_y - center_y) < 2:
                        red_x_diff = curve_x - center_x
                        cv2.circle(undistorted_frame, (curve_x, curve_y), 6, (0, 0, 255), -1)
                        break
            else:
                red_x_diff = 0
        elif color == 'Green' and green_curve_points:
            max_curve_y = max(pt[1] for pt in green_curve_points)
            if center_y < max_curve_y:
                for curve_x, curve_y in green_curve_points:
                    if abs(curve_y - center_y) < 2:
                        green_x_diff = center_x - curve_x
                        cv2.circle(undistorted_frame, (curve_x, curve_y), 6, (0, 255, 0), -1)
                        break
            else:
                green_x_diff = 0

    # Draw pink lines if we have enough color_y_positions
    if len(color_y_positions) > 1:
        pink_left_points, pink_right_points = draw_multiple_lines(
            undistorted_frame, start_points_pink, end_points_pink, color_y_positions[1]
        )

        # Extra logic: compute pink_red_x_diff & pink_green_x_diff if pink block & lines are valid
        if pink_positions[1] and isinstance(pink_left_points, int):
            pink_red_x_diff = pink_left_points - pink_positions[0]
            cv2.circle(undistorted_frame, (pink_left_points, pink_positions[1]), 6, (255, 192, 203), -1)
        if pink_positions[1] and isinstance(pink_right_points, int):
            pink_green_x_diff = pink_positions[0] - pink_right_points
            cv2.circle(undistorted_frame, (pink_right_points, pink_positions[1]), 6, (255, 192, 203), -1)

    return color_y_positions, pink_positions, red_x_diff, green_x_diff, pink_red_x_diff, pink_green_x_diff
