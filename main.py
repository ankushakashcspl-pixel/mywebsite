from flask import Flask
import os
import psycopg2

app = Flask(__name__)

# Get connection string from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

def get_message():
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    cur = conn.cursor()
    cur.execute("SELECT content FROM messages ORDER BY created_on DESC LIMIT 1;")
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else "No message found."

@app.route("/")
def home():
    return f"<h1>{get_message()}</h1>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
