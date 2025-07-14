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
    """Lê frames de um stream RTMP, codifica para JPEG e os envia."""
    rtmp_url = "rtmp://195.200.0.55/live/stream"
    
    while True: # Loop principal para tentar reconectar em caso de falha total
        app.logger.info(f"Tentando conectar ao stream RTMP em {rtmp_url}")
        # Força o uso do backend FFMPEG, que é mais robusto para streams de rede
        camera = cv2.VideoCapture(rtmp_url, cv2.CAP_FFMPEG)

        if not camera.isOpened():
            app.logger.error("Erro: Não foi possível abrir o stream de vídeo. Tentando novamente em 5 segundos...")
            time.sleep(5)
            continue

        app.logger.info("Sucesso! Conectado ao stream RTMP.")

        while True: # Loop para ler os frames do stream conectado
            app.logger.info("==> Loop: Tentando ler um frame da câmera...")
            success, frame = camera.read()

            if not success:
                app.logger.warning("Falha ao ler o frame do stream. A conexão pode ter sido perdida. Tentando reconectar...")
                break # Sai do loop de leitura de frames para acionar a reconexão no loop principal

            app.logger.info("Frame lido com sucesso. Redimensionando...")
            
            # --- OTIMIZAÇÃO CRÍTICA ---
            # Reduz a resolução do frame para diminuir a carga de processamento.
            # 640x480 é um bom ponto de partida.
            try:
                frame_resized = cv2.resize(frame, (640, 480))
            except Exception as e:
                app.logger.error(f"Erro ao redimensionar o frame: {e}")
                continue # Pula este frame e tenta o próximo

            app.logger.info("Frame redimensionado. Codificando para JPEG...")
            ret, buffer = cv2.imencode('.jpg', frame_resized)

            if not ret:
                app.logger.error("Falha ao codificar o frame para JPEG.")
                continue # Pula este frame

            frame_bytes = buffer.tobytes()
            app.logger.info(f"Frame codificado com sucesso ({len(frame_bytes)} bytes). Enviando para o cliente...")

            # Envia o frame para o navegador
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        # Libera o objeto da câmera antes de tentar reconectar
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
    # Esta parte é para debug local e não é usada pelo Gunicorn
    app.run(host='0.0.0.0', port=5000, debug=True)
