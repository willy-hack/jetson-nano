import cv2
import numpy as np
import pickle
import os

def nothing(x):
    pass

# 創建顯示視窗
cv2.namedWindow('image', cv2.WINDOW_NORMAL)
cv2.resizeWindow('image', 1024, 768)

# 創建HSV滑桿（H範圍改為0-255）
cv2.createTrackbar('H_low', 'image', 0, 255, nothing)
cv2.createTrackbar('H_high', 'image', 255, 255, nothing)
cv2.createTrackbar('S_low', 'image', 0, 255, nothing)
cv2.createTrackbar('S_high', 'image', 255, 255, nothing)
cv2.createTrackbar('V_low', 'image', 0, 255, nothing)
cv2.createTrackbar('V_high', 'image', 255, 255, nothing)

# 相機設定
imcap = cv2.VideoCapture(
    'nvarguscamerasrc ! video/x-raw(memory:NVMM), width=640, height=480, format=(string)NV12, framerate=(fraction)30/1 ! '
    'nvvidconv ! video/x-raw, format=(string)BGRx ! videoconvert ! video/x-raw, format=(string)BGR ! appsink', 
    cv2.CAP_GSTREAMER
)

imcap.set(cv2.CAP_PROP_BRIGHTNESS, 60)
kernal = np.ones((5, 5))

# 顏色HSV值字典
hsv_values = {
    'Blue_final': None, 'Orange_final': None, 'Red': None, 
    'Green': None, 'Pink': None, 
    'qualifications_Blue': None, 'qualifications_Orange': None
}

# 檢查並載入之前儲存的HSV值
if os.path.exists('hsv_values.pkl'):
    with open('hsv_values.pkl', 'rb') as f:
        hsv_values = pickle.load(f)

print("Loaded previously saved HSV values:", hsv_values)

def print_actions():
    print("\n操作說明:")
    print("按 '1' 儲存當前HSV值為 Blue_final")
    print("按 '2' 儲存當前HSV值為 Orange_final")
    print("按 '3' 儲存當前HSV值為 Red")
    print("按 '4' 儲存當前HSV值為 Green")
    print("按 '5' 儲存當前HSV值為 Pink")
    print("按 '6' 儲存當前HSV值為 qualifications_Blue")
    print("按 '7' 儲存當前HSV值為 qualifications_Orange")
    print("按 'q' 儲存所有HSV值並退出程式")
    print("** 直接在影像上拖曳滑鼠框選區域，自動計算HSV範圍 **\n")

print_actions()


# 創建按鈕視窗
cv2.namedWindow('buttons')
buttons_img = np.zeros((600, 700, 3), np.uint8)  # 增大視窗尺寸
button_size = (250, 80)

# 按鈕設定（新的佈局：兩邊各4個，底部中間1個）
buttons = {
    # 左側按鈕 (4個)
    'Blue_final': (20, 100),
    'Orange_final': (20, 220),
    'Red': (20, 340),
    'qualifications_Blue': (20, 460),
    
    # 右側按鈕 (4個)
    'Green': (350, 100),
    'Pink': (350, 220),
    'qualifications_Orange': (350, 340),
    'Save & Quit': (350, 460),
    
    # 底部中間按鈕 (1個)
    'Reset HSV': (185, 550)  # 中間位置
}

# 繪製按鈕
for text, pos in buttons.items():
    color = (255, 255, 255)  # 預設白色
    if "final" in text:
        color = (0, 255, 0)  # 綠色
    elif "qualifications" in text:
        color = (0, 0, 255)  # 紅色
    elif text == 'Reset HSV':
        color = (255, 255, 0)  # 黃色
    elif text == 'Save & Quit':
        color = (0, 165, 255)  # 橙色

    cv2.rectangle(buttons_img, (pos[0], pos[1] - button_size[1]), (pos[0] + button_size[0], pos[1]), color, -1)
    cv2.putText(buttons_img, text, (pos[0] + 10, pos[1] - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

# 滑鼠框選變數
drawing = False
roi_start = (-1, -1)
roi_end = (-1, -1)

def detect_shapes(mask, frame):
    """外觀特徵辨識：形狀檢測"""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 500:  # 忽略小區域
            continue
            
        perimeter = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.04 * perimeter, True)
        sides = len(approx)
        
        # 形狀判斷
        shape = "unknown"
        if sides == 3:
            shape = "triangle"
        elif sides == 4:
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = float(w)/h
            shape = "square" if 0.95 <= aspect_ratio <= 1.05 else "rectangle"
        elif sides == 5:
            shape = "pentagon"
        elif sides >= 6:
            shape = "circle"
        
        # 繪製形狀
        cv2.drawContours(frame, [cnt], -1, (0, 255, 0), 2)
        M = cv2.moments(cnt)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            cv2.putText(frame, shape, (cX, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

def mouse_callback(event, x, y, flags, param):
    global drawing, roi_start, roi_end

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        roi_start = (x, y)
        roi_end = (x, y)

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            roi_end = (x, y)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        roi_end = (x, y)
        
        if roi_start != (-1, -1) and roi_end != (-1, -1):
            x1, y1 = roi_start
            x2, y2 = roi_end
            x_min, x_max = min(x1, x2), max(x1, x2)
            y_min, y_max = min(y1, y2), max(y1, y2)
            
            roi = param[y_min:y_max, x_min:x_max]
            if roi.size > 0:
                hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
                
                h_min, h_max = np.min(hsv_roi[:,:,0]), np.max(hsv_roi[:,:,0])
                s_min, s_max = np.min(hsv_roi[:,:,1]), np.max(hsv_roi[:,:,1])
                v_min, v_max = np.min(hsv_roi[:,:,2]), np.max(hsv_roi[:,:,2])
                
                margin = 10
                h_low = max(0, h_min - margin)
                h_high = min(255, h_max + margin)  # 改為255
                s_low = max(0, s_min - margin)
                s_high = min(255, s_max + margin)
                v_low = max(0, v_min - margin)
                v_high = min(255, v_max + margin)
                
                cv2.setTrackbarPos('H_low', 'image', h_low)
                cv2.setTrackbarPos('H_high', 'image', h_high)
                cv2.setTrackbarPos('S_low', 'image', s_low)
                cv2.setTrackbarPos('S_high', 'image', s_high)
                cv2.setTrackbarPos('V_low', 'image', v_low)
                cv2.setTrackbarPos('V_high', 'image', v_high)

def button_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        for button, pos in buttons.items():
            if pos[0] <= x <= pos[0] + button_size[0] and pos[1] - button_size[1] <= y <= pos[1]:
                if button == 'Save & Quit':
                    with open('hsv_values.pkl', 'wb') as f:
                        pickle.dump(hsv_values, f)
                    print("已儲存所有HSV值到 hsv_values.pkl")
                    cv2.destroyAllWindows()
                    exit()
                elif button == 'Reset HSV':
                    # 重置HSV滑桿為預設值
                    cv2.setTrackbarPos('H_low', 'image', 0)
                    cv2.setTrackbarPos('H_high', 'image', 255)  # 改為255
                    cv2.setTrackbarPos('S_low', 'image', 0)
                    cv2.setTrackbarPos('S_high', 'image', 255)
                    cv2.setTrackbarPos('V_low', 'image', 0)
                    cv2.setTrackbarPos('V_high', 'image', 255)
                else:
                    H_low = cv2.getTrackbarPos('H_low', 'image')
                    H_high = cv2.getTrackbarPos('H_high', 'image')
                    S_low = cv2.getTrackbarPos('S_low', 'image')
                    S_high = cv2.getTrackbarPos('S_high', 'image')
                    V_low = cv2.getTrackbarPos('V_low', 'image')
                    V_high = cv2.getTrackbarPos('V_high', 'image')
                    
                    hsv_values[button] = ([H_low, S_low, V_low], [H_high, S_high, V_high])
                    print(f"儲存 {button} HSV值:", hsv_values[button])

i = 0
while True:
    H_high = cv2.getTrackbarPos('H_high', 'image')
    H_low = cv2.getTrackbarPos('H_low', 'image')
    S_high = cv2.getTrackbarPos('S_high', 'image')
    S_low = cv2.getTrackbarPos('S_low', 'image')
    V_high = cv2.getTrackbarPos('V_high', 'image')
    V_low = cv2.getTrackbarPos('V_low', 'image')
    success, img = imcap.read()

    if not success:
        break
    elif i == 0:
        print_actions()
        i += 1

    # 顯示ROI選擇框
    display_img = img.copy()
    if drawing and roi_start != (-1, -1) and roi_end != (-1, -1):
        cv2.rectangle(display_img, roi_start, roi_end, (0, 255, 0), 2)

    # HSV處理（注意H範圍已改為0-255）
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hsv_low = np.array([H_low, S_low, V_low])
    hsv_high = np.array([H_high, S_high, V_high])

    mask = cv2.inRange(hsv, hsv_low, hsv_high)
    mask = cv2.dilate(mask, kernal, iterations=1)
    res = cv2.bitwise_and(img, img, mask=mask)
    
    # 外觀特徵辨識（形狀檢測）
    detect_shapes(mask, res)

    # 顯示選取方框
    if drawing and roi_start != (-1, -1) and roi_end != (-1, -1):
        cv2.rectangle(res, roi_start, roi_end, (0, 255, 0), 2)

    cv2.imshow('image', res)
    cv2.imshow('buttons', buttons_img)

    # 設定滑鼠回調
    cv2.setMouseCallback('image', mouse_callback, img)
    cv2.setMouseCallback('buttons', button_callback)

    key = cv2.waitKey(30) & 0xFF

    # 處理按鍵輸入
    if key == ord('1'):
        hsv_values['Blue_final'] = ([H_low, S_low, V_low], [H_high, S_high, V_high])
        print("儲存 Blue_final HSV值:", hsv_values['Blue_final'])
    elif key == ord('2'):
        hsv_values['Orange_final'] = ([H_low, S_low, V_low], [H_high, S_high, V_high])
        print("儲存 Orange_final HSV值:", hsv_values['Orange_final'])
    elif key == ord('3'):
        hsv_values['Red'] = ([H_low, S_low, V_low], [H_high, S_high, V_high])
        print("儲存 Red HSV值:", hsv_values['Red'])
    elif key == ord('4'):
        hsv_values['Green'] = ([H_low, S_low, V_low], [H_high, S_high, V_high])
        print("儲存 Green HSV值:", hsv_values['Green'])
    elif key == ord('5'):
        hsv_values['Pink'] = ([H_low, S_low, V_low], [H_high, S_high, V_high])
        print("儲存 Pink HSV值:", hsv_values['Pink'])
    elif key == ord('6'):
        hsv_values['qualifications_Blue'] = ([H_low, S_low, V_low], [H_high, S_high, V_high])
        print("儲存 qualifications_Blue HSV值:", hsv_values['qualifications_Blue'])
    elif key == ord('7'):
        hsv_values['qualifications_Orange'] = ([H_low, S_low, V_low], [H_high, S_high, V_high])
        print("儲存 qualifications_Orange HSV值:", hsv_values['qualifications_Orange'])
    elif key == ord('q'):
        with open('hsv_values.pkl', 'wb') as f:
            pickle.dump(hsv_values, f)
        print("已儲存所有HSV值到 hsv_values.pkl")
        break

cv2.destroyAllWindows()