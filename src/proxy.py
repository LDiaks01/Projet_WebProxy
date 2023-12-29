import socket
import threading
import ssl

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
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        request_data = client_socket.recv(4096)
        # Vous pouvez ajouter des logiques de filtrage ici en fonction de self.filter_list

        # Extraire l'URL demandée à partir de la requête
        requested_host = self.extract_requested_host(request_data)

        remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote_socket.connect((requested_host, 443))  # Connexion sécurisée avec le serveur distant sur le port 443

        # Utilisez SSL pour créer un tunnel sécurisé
        remote_socket = ssl.wrap_socket(remote_socket, server_hostname=requested_host)

        remote_socket.sendall(request_data)
        response_data = remote_socket.recv(4096)

        # Modifiez la réponse si nécessaire (par exemple, remplacez des éléments dans le HTML)
        modified_response_data = response_data.replace(b'</body>', f'<p>{self.banner}</p></body>'.encode())

        client_socket.sendall(modified_response_data)
        client_socket.close()
        remote_socket.close()

    def extract_requested_host(self, request_data):
        # Extrait l'URL demandée à partir de la première ligne de la requête
        first_line = request_data.split(b'\n')[0]
        parts = first_line.split(b' ')
        if len(parts) > 1:
            url = parts[1].decode('utf-8')
            return url.split('/')[2]  # Récupère l'hôte à partir de l'URL

        return ''

if __name__ == "__main__":
    # Exemple d'utilisation de la classe ProxyServer
    proxy = ProxyServer('127.0.0.1', 8080, 'Mon Super Banner', ['example.com'])
    proxy.start()
