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
        self.server_socket.listen(5)
        print(f"Proxy Server listening on {self.host}:{self.port}")

        while True:
            client_socket, client_address = self.server_socket.accept()
            print(client_socket)
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        request_data = client_socket.recv(4096)
        

        # Modifier la requête
        modified_request = self.modify_request(request_data)
        print("Modifiied :", modified_request)

        # Extraire l'URL demandée à partir de la requête modifiée
        requested_host = self.extract_requested_host(modified_request)
        print("Requested Host : ",requested_host)

        remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            # Connexion sécurisée avec le serveur distant sur le port 443
            context = ssl.create_default_context()
            remote_socket.connect((requested_host, 443))
            remote_socket = context.wrap_socket(remote_socket, server_hostname=requested_host)

            remote_socket.sendall(modified_request)
            response_data = remote_socket.recv(4096)
            print("Response Data : ",response_data)
        except Exception as e:
            print(e.args)
            # En cas d'échec, essayez la connexion non sécurisée sur le port 80
            remote_socket.connect((requested_host, 80))
            remote_socket.sendall(modified_request)
            response_data = remote_socket.recv(4096)

        # Renvoyer la réponse au client
        client_socket.sendall(response_data)
        client_socket.close()
        remote_socket.close()
        


    def modify_request(self, request_data):
        # Supprimer les lignes spécifiées de la requête
        modified_request = request_data.replace(b'Proxy-Connection: keep-alive', b'')
        modified_request = modified_request.replace(b'Accept-Encoding: gzip', b'')
        modified_request = modified_request.replace(b'Connection: keep-alive', b'')
        
        # Ajouter la version HTTP/1.0 à la requête
        modified_request = modified_request.replace(b'HTTP/1.1', b'HTTP/1.0')

        return modified_request

    def extract_requested_host(self, raw_request):
        raw_request = raw_request.decode('utf-8')
        lines = raw_request.split('\n')
        
        # Chercher l'en-tête Host
        host_line = next((line for line in lines if line.lower().startswith('host:')), None)
        
        if host_line:
            host = host_line.split(':')[1].strip()
        elif 'HTTP/1.0' in lines[0]:
            # Pour HTTP/1.0, le nom d'hôte doit être déduit de l'adresse IP
            host = 'Nom d\'hôte pour HTTP/1.0 non spécifié dans la requête'
        else:
            host = 'En-tête Host non trouvé dans la requête'

        return host

if __name__ == "__main__":
    proxy_instance = ProxyServer('127.0.0.1', 9000, 'test', 'test')
    threading.Thread(target=proxy_instance.start).start()