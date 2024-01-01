import socket
import threading
import ssl
import re

class ProxyServer:
    def __init__(self, host, port, banner, filter_list):
        self.host = host
        self.port = port
        self.banner = banner
        self.filter_list = filter_list
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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

        # Extraire l'URL demandée à partir de la requête modifiée
        requested_host = self.extract_requested_host(modified_request)

        remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            if is_https_request:
                # Connexion sécurisée avec le serveur distant sur le port 443
                context = ssl.create_default_context()
                remote_socket.connect((requested_host, 443))
                remote_socket = context.wrap_socket(remote_socket, server_hostname=requested_host)
                remote_socket.sendall(modified_request)
                
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

            # print("Response Data : ", response_data)
        except Exception as e:
            print(e.args)
            # En cas d'échec, essayez la connexion non sécurisée sur le port 80
            # remote_socket.connect((requested_host, 80))
            # remote_socket.sendall(modified_request)
            # response_data = remote_socket.recv(4096)

        # Renvoyer la réponse au client
        # print("Client Socket :", client_socket, " ---Reponse : ", response_data.decode()[:20])
        client_socket.sendall(response_data)



    def modify_request(self, request_data):
        # Supprimer les lignes spécifiées de la requête
        modified_request = request_data.replace(b'Proxy-Connection: keep-alive', b'')
        modified_request = modified_request.replace(b'Accept-Encoding: gzip', b'')
        modified_request = modified_request.replace(b'Connection: keep-alive', b'')
        
        # Ajouter la version HTTP/1.0 à la requête
        modified_request = modified_request.replace(b'HTTP/1.1', b'HTTP/1.0')

        return modified_request
    
    def extract_requested_host(self, request_data):
      
       
        # Trouver le nom d'hôte à partir du champ "Host" dans l'en-tête
        host_header = self.extract_host_header(request_data)
        if host_header:
            return host_header

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


if __name__ == "__main__":
    proxy_instance = ProxyServer('127.0.0.1', 9000, 'test', 'test')
    threading.Thread(target=proxy_instance.start).start()