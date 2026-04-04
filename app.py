from flask import Flask, request, jsonify
import sqlite3
import tempfile
import os

app = Flask(__name__)

def analyze_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    analysis = {
        "tables": [],
        "summary": [],
        "suggested_queries": []
    }

    # Get tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]

    for table in tables:
        table_info = {"table": table, "columns": [], "row_count": 0}

        # Columns
        cursor.execute(f"PRAGMA table_info({table});")
        table_info["columns"] = [col[1] for col in cursor.fetchall()]

        # Row count
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        table_info["row_count"] = cursor.fetchone()[0]

        analysis["tables"].append(table_info)

        # Suggested queries
        analysis["suggested_queries"].append(f"SELECT * FROM {table} LIMIT 5;")
        analysis["suggested_queries"].append(f"SELECT COUNT(*) FROM {table};")

    conn.close()
    return analysis


@app.route("/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files:
        return jsonify({"error": "No SQLite file uploaded"}), 400

    file = request.files["file"]

    # Save file temporarily
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        file.save(tmp.name)
        db_path = tmp.name

    # Run analysis
    analysis = analyze_database(db_path)

    os.remove(db_path)
    return jsonify(analysis)


@app.route("/query", methods=["POST"])
def query():
    if "file" not in request.files:
        return jsonify({"error": "No SQLite file uploaded"}), 400

    sql = request.form.get("query")
    if not sql:
        return jsonify({"error": "No SQL query provided"}), 400

    file = request.files["file"]

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        file.save(tmp.name)
        db_path = tmp.name

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        result = {"columns": columns, "rows": rows}
    except Exception as e:
        result = {"error": str(e)}

    conn.close()
    os.remove(db_path)

    return jsonify(result)


@app.route("/", methods=["GET"])
def home():
    return "SQLite backend is running."


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)