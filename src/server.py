from flask import Flask, render_template, request, send_file
import threading
from proxy import ProxyServer
import re

app = Flask(__name__, template_folder='../templates/')


proxy_instance = None
config_file_path = "config_file.txt"

@app.route('/')
def index():
    return render_template('welcome.html')


@app.route('/submit', methods=['POST'])
def submit():
    global proxy_instance
    global config_file_path
    
    # Fermer l'instance précédente du serveur proxy si elle existe
    if proxy_instance:
        proxy_instance.server_socket.close()
        proxy_instance = None

    # Lancer une nouvelle instance du serveur proxy avec les nouveaux paramètres
    
    
    banner_text = request.form.get('bannerText', '')
    proxy_message_head = request.form.get('proxyMessage', '')
    filter_list_textarea = request.form.get('filterListTextarea', '')
    no_filter = 'noFilter' in request.form
    if no_filter:
        filter_list_textarea = None
    
    
    # Récupérer les valeurs d'IP et de port depuis le fichier texte
    config_data = read_proxy_config(config_file_path)
    ip = config_data.get('ip')
    port = int(config_data.get('port'))
    blocked_ressources = config_data.get('blocked_ressources')
    proxy_instance = ProxyServer(ip, port, banner_text, filter_list_textarea, proxy_message_head, blocked_ressources)
    threading.Thread(target=proxy_instance.start).start()

    #Données du formulaire
    print(f"Banner Text: {banner_text}")
    print(f"Filter List Textarea: {filter_list_textarea}")
    print(f"No Filter: {no_filter}")


    return render_template('welcome.html', host=ip, port=port)

def read_proxy_config(file_path):
    config_dict = {}

    try:
        with open(file_path, 'r') as config_file:
            for line in config_file.readlines():
                parts = line.strip().split('=')
                if len(parts) == 2:
                    key, value = parts[0].strip(), parts[1].strip()
                    
                    
                    # Vérifier si la valeur est une liste et extraire les éléments
                    match = re.match(r'\[(.*)\]', value)
                    if match:
                        elements = match.group(1).split(',')
                        config_dict[key] = [element.strip() for element in elements]
                    else:
                        config_dict[key] = value.replace('\n', '')
    except FileNotFoundError:
        print(f"Fichier de configuration '{file_path}' non trouvé.")
    except Exception as e:
        print(f"Une erreur s'est produite lors de la lecture du fichier de configuration : {e}")

    return config_dict



if __name__ == '__main__':
    app.run(debug=True)