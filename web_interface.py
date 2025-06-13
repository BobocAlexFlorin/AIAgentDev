from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route("/translate", methods=["POST"])
def translate():
    data = request.json
    chunk = data.get("chunk")
    model = data.get("model", "gpt-4o")
    dest_language = data.get("dest_language", "English")
    # Simulare traducere
    translation = f"Translated: {chunk}"
    return jsonify({"translation": translation})

if __name__ == "__main__":
    app.run(debug=True)