import socket
import threading
import ssl
import re
import traceback
class ProxyServer:
    def __init__(self, host, port, banner, filter_list, proxy_message, blocked_ressources):
        self.host = host
        self.port = port
        self.banner = banner
        self.filter_list = filter_list
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.proxy_message = proxy_message
        self.blocked_ressources = blocked_ressources

    def start(self):
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(socket.SOMAXCONN)
        print(f"Proxy Server listening on {self.host}:{self.port}")

        while True:
            client_socket, client_address = self.server_socket.accept()
            
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        request_data = b""
        
        while True:
            # Recevoir les données par tranches de 4096 octets
            chunk = client_socket.recv(4096)
            if not chunk:
                # La connexion a été fermée par le client
                break
            request_data += chunk

            # Si le dernier morceau de données reçu est moins de 4096 octets, cela signifie que toutes les données ont été reçues
            if len(chunk) < 4096:
                break

        # Vérifier si la requête commence par le verbe "CONNECT"
        is_https_request = request_data.startswith(b'CONNECT')

        # Modifier la requête si nécessaire
        modified_request = self.modify_request(request_data)
        
        # on verifie si la requete est autorisée
        if self.is_multimedia_request(modified_request, self.blocked_ressources):
            pass
        else:
        # Extraire l'URL demandée à partir de la requête modifiée
            requested_host = self.extract_host_header(modified_request)
            
            try:
                # Créer un socket vers le serveur distant
                remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                if is_https_request:

                    ssl_client = ssl.wrap_socket(client_socket, server_side=True, certfile='proxy_cert.pem', keyfile='proxy_key.pem', ssl_version=ssl.PROTOCOL_TLS)

                    # Lire la requête du client
                    request_data = ssl_client.recv(4096)
                    
                    # Modifier la requête si nécessaire
                    modified_request = self.modify_request(request_data)

                    remote_socket.connect((requested_host, 443))

                    # Tunnel SSL/TLS entre le proxy et le serveur distant
                    ssl_remote = ssl.wrap_socket(remote_socket, ssl_version=ssl.PROTOCOL_TLS)

                    # Envoyer la requête modifiée au serveur distant
                    ssl_remote.sendall("GET / HTTP/1.1\r\nHost: p-fb.net\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0\r\n\r\n \r\n".encode())

                    # Transférer les données entre le client et le serveur distant
                    self.forward_data(ssl_remote, ssl_client)
                    
                else:
                    # Connexion non sécurisée sur le port 80 pour les requêtes HTTP
                    remote_socket.connect((requested_host, 80))
                    remote_socket.sendall(modified_request)

                response_data = b""
                while True:
                    # Recevoir les données par tranches de 4096 octets depuis le serveur distant
                    chunk = remote_socket.recv(4096)
                    if not chunk:
                        # Toutes les données du serveur distant ont été reçues
                        break
                    response_data += chunk
                
                #traitement de la reponse
                
                # Verifier la presence du banner qui remplacera le titre
                if self.banner :
                    response_data = self.modify_html_title(response_data, self.banner)
                    
                if self.proxy_message:
                    response_data = self.add_proxy_message(response_data, self.proxy_message)
                  
                response_data = self.censor_words(response_data, self.filter_list)
                    
                
                
                client_socket.sendall(response_data)
            except Exception as e:
                print(e.args)
                traceback.print_exc()



    def modify_request(self, request_data):
        # Supprimer les lignes spécifiées de la requête
        modified_request = request_data.replace(b'Proxy-Connection: keep-alive', b'')
        modified_request = modified_request.replace(b'Accept-Encoding: gzip', b'')
        modified_request = modified_request.replace(b'Connection: keep-alive', b'')
        
        # Ajouter la version HTTP/1.0 à la requête
        modified_request = modified_request.replace(b'HTTP/1.1', b'HTTP/1.0')

        return modified_request
    
    #used for https verb
    def forward_data(self, source, destination):
        data = b""
        while True:
            data += source.recv(4096)
            
            if not data:
                break
            destination.sendall(data)
        
            
            
    def extract_host_header(self, request_data):
        # Rechercher le champ "Host" dans l'en-tête
        host_header = None
        for line in request_data.split(b"\r\n"):
            if line.lower().startswith(b"host:"):
                # Vérifier si ":" est présent avant de diviser
                if b":" not in line:
                    host_header = line.split(b":", 1)[1].strip()
                else:
                    host_header = line.split(b":", 1)[1].strip().split(b":")[0]
                break
        return host_header
    
    # Modify HTML title by inserting the banner
    def modify_html_title(self, html_content, insertion_text):
        title_pattern = re.compile(b'<title>(.*?)</title>', re.IGNORECASE | re.DOTALL)
        match = title_pattern.search(html_content)

        if match:
            modified_title = insertion_text.encode()
            modified_html = html_content.replace(match.group(0), b'<title>' + modified_title + b'</title>')
            return modified_html
        else:
            return html_content


    #Ajouter une balise au format H1 dans les entetes pour indiquer l'utilisation d'un proxy
    def add_proxy_message(self, html_content, proxy_message):
        proxy_message = "<h1>" + proxy_message+ "</h1>"
        # Étape 1: Rechercher la balise <body> avec des attributs potentiels
        body_match = re.search(b'<body[^>]*>', html_content, flags=re.IGNORECASE)

        if body_match:
            # Étape 2: Insérer le message juste après la balise <body>
            modified_html = re.sub(b'<body[^>]*>', b'<body>' + proxy_message.encode(), html_content, count=1, flags=re.IGNORECASE)

            return modified_html
        else:
            return html_content

    
    def is_multimedia_request(self, request, ressources):

        # Récupérer l'URL de la requête
        url = request.split(b' ')[1].decode()

        # Vérifier si l'URL se termine par une extension de fichier audio
        for extension in ressources:
            if url.lower().endswith(extension):
                return True

        return False

    # pas utilisée, mais permet de bloquer toutes les images
    def is_image_request(self, request):
        # Liste des extensions d'image courantes
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico']

        # Récupérer l'URL de la requête
        url = request.split(b' ')[1].decode()

        # Vérifier si l'URL se termine par une extension d'image
        for extension in image_extensions:
            if url.lower().endswith(extension):
                return True

        return False
    # remplace les mots clés par censored by proxy
    def censor_words(self, response_data, censor_words):
        if censor_words:
            for word in censor_words:
                # Utilise une expression régulière pour remplacer les occurrences du mot
                response_data = re.sub(rb'\b' + re.escape(word.encode()) + rb'\b', b'censored By Proxy', response_data, flags=re.IGNORECASE)
        
        return response_data

