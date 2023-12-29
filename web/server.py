from flask import Flask, render_template, request, send_file

app = Flask(__name__)

@app.route('/')
def index():
    return send_file('../templates/welcome.html')

@app.route('/submit', methods=['POST'])
def submit():
    banner_text = request.form.get('bannerText', '')
    filter_list = request.form.get('filterList', '')
    filter_list_textarea = request.form.get('filterListTextarea', '')
    no_filter = 'noFilter' in request.form

    # Faites quelque chose avec les données, par exemple imprimez-les pour le moment
    print(f"Banner Text: {banner_text}")
    print(f"Filter List: {filter_list}")
    print(f"Filter List Textarea: {filter_list_textarea}")
    print(f"No Filter: {no_filter}")

    # Ajoutez le code ici pour lancer votre serveur proxy ou effectuer d'autres actions

    return 'Données du formulaire reçues avec succès!', 200

if __name__ == '__main__':
    app.run(debug=True)
