
def extract_requested_host(raw_request):
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

# Exemple d'utilisation
request_data = b'CONNECT p-fb.net:443 HTTP/1.0\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0\r\nProxy-\r\n\r\nHost: p-fb.net:443\r\n\r\n'
host = extract_requested_host(request_data)
print(f"Extracted Host: {host}")
