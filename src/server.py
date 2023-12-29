from flask import Flask, render_template, request, send_file
import threading
from proxy import ProxyServer


app = Flask(__name__)


proxy_instance = None

@app.route('/')
def index():
    return send_file('../templates/welcome.html')


@app.route('/submit', methods=['POST'])
def submit():
    global proxy_instance

    banner_text = request.form.get('bannerText', '')
    filter_list = request.form.get('filterList', '')
    filter_list_textarea = request.form.get('filterListTextarea', '')
    no_filter = 'noFilter' in request.form

    # Fermer l'instance précédente du serveur proxy si elle existe
    if proxy_instance:
        proxy_instance.server_socket.close()

    # Lancer une nouvelle instance du serveur proxy avec les nouveaux paramètres
    proxy_instance = ProxyServer('127.0.0.1', 8080, banner_text, filter_list)
    threading.Thread(target=proxy_instance.start).start()

    # Faites quelque chose avec les données, par exemple imprimez-les pour le moment
    print(f"Banner Text: {banner_text}")
    print(f"Filter List: {filter_list}")
    print(f"Filter List Textarea: {filter_list_textarea}")
    print(f"No Filter: {no_filter}")

    # Ajoutez le code ici pour effectuer d'autres actions si nécessaire

    return 'Données du formulaire reçues avec succès!', 200


if __name__ == '__main__':
    app.run(debug=True)