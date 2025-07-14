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
    """Lê frames de um stream RTMP, controla o FPS e os envia."""
    TARGET_FPS = 10
    TIME_PER_FRAME = 1.0 / TARGET_FPS
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
            success, frame = camera.read()

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
            
            processing_time = time.time() - start_time
            sleep_time = TIME_PER_FRAME - processing_time
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        camera.release()
        app.logger.info("Objeto da câmera liberado. Aguardando para reconectar.")
        time.sleep(5)

@app.route('/video_feed')
def video_feed():
    """Rota que serve o stream de vídeo."""
    # Criamos o objeto de resposta com o nosso gerador de frames
    response = Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    
    # --- CORREÇÃO DO PROXY BUFFERING ---
    # Adicionamos os cabeçalhos para instruir proxies (como Nginx) a não fazer buffer da resposta.
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['X-Accel-Buffering'] = 'no' # Instrução específica para Nginx
    # ------------------------------------
    
    return response

@app.route('/')
def index():
    """Página inicial que exibe o vídeo."""
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
