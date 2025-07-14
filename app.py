from flask import Flask, Response, render_template
import cv2
import logging
import time

app = Flask(__name__)

# Configura o logger do Flask
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

def generate_frames():
    """Lê frames de um stream RTMP, otimiza a latência."""
    rtmp_url = "rtmp://195.200.0.55/live/stream"
    
    while True:
        app.logger.info(f"Tentando conectar ao stream RTMP em {rtmp_url}")
        camera = cv2.VideoCapture(rtmp_url, cv2.CAP_FFMPEG)

        if not camera.isOpened():
            app.logger.error("Erro: Não foi possível abrir o stream. Tentando novamente em 5s...")
            time.sleep(5)
            continue

        app.logger.info("Sucesso! Conectado ao stream RTMP.")
        
        while True:
            start_time = time.time()
            
            # --- OTIMIZAÇÃO DE LATÊNCIA ---
            # Pega (e descarta) alguns frames para limpar o buffer interno do OpenCV.
            # O número de grabs pode ser ajustado. 2-4 é geralmente um bom valor.
            for _ in range(2):
                camera.grab()
            
            # Agora, recupera o frame mais recente.
            success, frame = camera.retrieve()
            # -----------------------------

            if not success:
                app.logger.warning("Falha ao ler o frame. Reconectando...")
                break 

            try:
                frame_resized = cv2.resize(frame, (640, 480))
            except Exception as e:
                app.logger.error(f"Erro ao redimensionar o frame: {e}")
                continue

            ret, buffer = cv2.imencode('.jpg', frame_resized)
            if not ret:
                app.logger.error("Falha ao codificar o frame para JPEG.")
                continue

            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        camera.release()
        app.logger.info("Objeto da câmera liberado. Aguardando para reconectar.")
        time.sleep(5)

@app.route('/video_feed')
def video_feed():
    """Rota que serve o stream de vídeo."""
    response = Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['X-Accel-Buffering'] = 'no'
    return response

@app.route('/')
def index():
    """Página inicial que exibe o vídeo."""
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
