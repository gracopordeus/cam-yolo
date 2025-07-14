# Project: Real-time Object Recognition with a Phone Camera and YOLO

**Goal:** Use an old phone as a camera source, process the video feed in the cloud with a YOLO model, and access the real-time recognition results remotely.

## Project Status

- [X] **Phase 1: The Phone (Video Source)** - An app like "IP Webcam" (Android) or similar was installed, providing a local network URL for the video stream.
- [X] **Phase 2: The Connection (Phone-to-Cloud Bridge)** - A tool like `ngrok` is used to create a secure public URL that tunnels to the local video stream.
- [X] **Phase 3: The Cloud Server (Processing)** - A cloud environment is set up to receive the video and run the YOLO model.
- [In Progress] **Phase 4: The Code (Project's Brains)** - The Python script to process the video stream is under development.

## Application Setup

This project uses a Flask application to serve the video stream with YOLOv8 inference.

### Prerequisites

- Python 3.x
- An RTMP stream source (e.g., from a phone camera with an app like IP Webcam and an RTMP server).

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the application

1. Make sure your RTMP stream is running and accessible at the URL specified in `app.py` (currently `rtmp://localhost:1935/live/stream`).

2. Run the Flask application:
   ```bash
   python app.py
   ```

3. Open your web browser and navigate to `http://127.0.0.1:5000` to see the video stream with object detection.

## Deployment to Heroku

This application is ready to be deployed to Heroku. The `Procfile` and `requirements.txt` files are included for this purpose.

1. Create a Heroku app:
   ```bash
   heroku create <your-app-name>
   ```

2. Push the code to Heroku:
   ```bash
   git push heroku main
   ```

3. Open the app in your browser:
   ```bash
   heroku open
   ```