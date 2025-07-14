from flask import Flask, Response, render_template
import cv2
import logging
import time

app = Flask(__name__)

# Configura o logger do Flask para que as mensagens apareçam no console do Gunicorn
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

def generate_frames():
    """Lê frames de um stream RTMP, controla o FPS, codifica para JPEG e os envia."""
    # --- CONTROLE DE FPS ---
    # Defina o FPS desejado. Um valor entre 5 e 15 é bom para monitoramento.
    TARGET_FPS = 10
    TIME_PER_FRAME = 1.0 / TARGET_FPS
    # -----------------------
    
    rtmp_url = "rtmp://195.200.0.55/live/stream"
    
    while True: # Loop principal para tentar reconectar em caso de falha total
        app.logger.info(f"Tentando conectar ao stream RTMP em {rtmp_url}")
        camera = cv2.VideoCapture(rtmp_url, cv2.CAP_FFMPEG)

        if not camera.isOpened():
            app.logger.error("Erro: Não foi possível abrir o stream de vídeo. Tentando novamente em 5 segundos...")
            time.sleep(5)
            continue

        app.logger.info("Sucesso! Conectado ao stream RTMP.")

        last_frame_time = time.time()
        while True: # Loop para ler os frames do stream conectado
            
            # --- CONTROLE DE FPS (Início) ---
            start_time = time.time()
            # --------------------------------

            app.logger.info("==> Loop: Tentando ler um frame da câmera...")
            success, frame = camera.read()

            if not success:
                app.logger.warning("Falha ao ler o frame do stream. A conexão pode ter sido perdida. Tentando reconectar...")
                break 

            app.logger.info("Frame lido com sucesso. Redimensionando...")
            
            try:
                frame_resized = cv2.resize(frame, (640, 480))
            except Exception as e:
                app.logger.error(f"Erro ao redimensionar o frame: {e}")
                continue

            app.logger.info("Frame redimensionado. Codificando para JPEG...")
            ret, buffer = cv2.imencode('.jpg', frame_resized)

            if not ret:
                app.logger.error("Falha ao codificar o frame para JPEG.")
                continue

            frame_bytes = buffer.tobytes()
            app.logger.info(f"Frame codificado com sucesso ({len(frame_bytes)} bytes). Enviando para o cliente...")

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # --- CONTROLE DE FPS (Fim) ---
            processing_time = time.time() - start_time
            sleep_time = TIME_PER_FRAME - processing_time
            if sleep_time > 0:
                app.logger.info(f"Processamento rápido. Pausando por {sleep_time:.4f} segundos para manter {TARGET_FPS} FPS.")
                time.sleep(sleep_time)
            # -------------------------------
        
        camera.release()
        app.logger.info("Objeto da câmera liberado.")

@app.route('/video_feed')
def video_feed():
    """Rota que serve o stream de vídeo."""
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    """Página inicial que exibe o vídeo."""
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
