from flask import Flask, Response, render_template
import cv2
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

def generate_frames():
    rtmp_url = "rtmp://195.200.0.55:8080/live/stream"
    app.logger.info(f"Attempting to connect to RTMP stream at {rtmp_url}")
    camera = cv2.VideoCapture(rtmp_url)

    if not camera.isOpened():
        app.logger.error("Error: Could not open video stream.")
        return

    app.logger.info("Successfully connected to RTMP stream.")

    while True:
        success, frame = camera.read()
        if not success:
            app.logger.warning("Failed to read frame from stream. Reconnecting...")
            camera.release()
            camera = cv2.VideoCapture(rtmp_url)
            if not camera.isOpened():
                app.logger.error("Failed to reconnect. Stopping stream.")
                break
            continue

        ret, buffer = cv2.imencode('.jpg', frame)
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
