from flask import Flask
from flask import jsonify

app = Flask(__name__)


@app.route("/")
async def index():
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run()
