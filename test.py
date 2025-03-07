# 

# import cv2
# web_cam = cv2.VideoCapture(0)

# def web_cam_capture():
#     if not web_cam.isOpened():
#         print("Unable to open camera")
#         exit()

#     path = 'webcam.jpg'
#     ret, frame =web_cam.read()
#     cv2.imwrite(path, frame)
# web_cam_capture()


# import pyperclip
# def get_clipboard_text():
#     clipboard_content = pyperclip.paste()
#     if isinstance(clipboard_content, str):
#         return clipboard_content
#     else:
#         print('No clipboard')
#         return None

# print(get_clipboard_text())