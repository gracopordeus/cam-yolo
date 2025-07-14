from flask import Flask, Response, render_template
import cv2
from ultralytics import YOLO

app = Flask(__name__)

# Load the YOLOv8 model
model = YOLO('yolov8n.pt')

def generate_frames():
    camera = cv2.VideoCapture("rtmp://localhost:1935/live/stream")  # Use the RTMP stream
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            # Run YOLOv8 inference on the frame
            results = model(frame)

            # Visualize the results on the frame
            annotated_frame = results[0].plot()

            ret, buffer = cv2.imencode('.jpg', annotated_frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
