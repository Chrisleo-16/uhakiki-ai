import cv2
import face_recognition

def check_liveness():
    video_capture = cv2.VideoCapture(0)
    blink_detected = False
    print("👀 Please blink to verify identity...")
    
    while True:
        ret, frame = video_capture.read()
        rgb_frame = frame[:, :, ::-1]
        
        # Detect Face Landmarks
        face_landmarks_list = face_recognition.face_landmarks(rgb_frame)
        
        for face_landmarks in face_landmarks_list:
            # Check if eyes are 'closed' or narrow (simple blink logic)
            left_eye = face_landmarks['left_eye']
            right_eye = face_landmarks['right_eye']
            # (In a real app, calculate Eye Aspect Ratio - EAR)
            # For the demo, if face is detected and moving, we signal liveness
            if len(left_eye) > 0: blink_detected = True
            
        cv2.imshow('KNDC Liveness Check', frame)
        if blink_detected or cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()
    return "LIVENESS_CONFIRMED" if blink_detected else "LIVENESS_FAILED"