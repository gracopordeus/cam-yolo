from flask import Flask, render_template

# Inicializa a aplicação Flask
app = Flask(__name__)

@app.route('/')
def index():
    """
    Esta é a única rota necessária.
    Sua única função é renderizar e servir o arquivo index.html.
    """
    return render_template('index.html')

if __name__ == '__main__':
    # Permite executar a aplicação localmente para testes
    app.run(debug=True)
