
from flask import Flask, request, jsonify, send_from_directory
import sqlite3
from pathlib import Path
from datetime import date
from twilio.rest import Client

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
DB = ROOT / "financeiro.db"

app = Flask(__name__, static_folder=str(FRONTEND), static_url_path='')

TWILIO_ACCOUNT_SID = "AC796300de2500d46d26dd1ddcc8395a4f"
TWILIO_AUTH_TOKEN = "64e47a74337c15c075ca784b071a635b"

client = Client(
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN
)

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

with conn() as c:

    c.execute('''
    CREATE TABLE IF NOT EXISTS lancamentos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT,
        descricao TEXT,
        valor REAL,
        vencimento TEXT,
        status TEXT
    )
    ''')

    c.commit()

def enviar(msg):
    print("TENTANDO ENVIAR WHATSAPP:", msg, flush=True)

    try:
        envio = client.messages.create(
            from_='whatsapp:+14155238886',
            to='whatsapp:+554792445277',
            body=msg
        )

        print("WHATSAPP ENVIADO:", envio.sid, envio.status, flush=True)
        return True

    except Exception as e:
        print("ERRO WHATSAPP:", str(e), flush=True)
        return False

@app.route("/")
def home():
    return send_from_directory(FRONTEND, "index.html")

@app.route("/<path:p>")
def staticf(p):
    return send_from_directory(FRONTEND, p)

@app.get("/api/lancamentos")
def listar():

    mes = request.args.get('mes','')

    with conn() as c:

        rows = [
            dict(r)
            for r in c.execute(
                "SELECT * FROM lancamentos ORDER BY id DESC"
            )
        ]

    hoje = date.today().isoformat()

    filtrados = []

    for r in rows:

        if r["status"] != "pago":

            if r["vencimento"] and r["vencimento"] < hoje:
                r["status"] = "atrasado"

        if mes:

            if not r["vencimento"].startswith(mes):
                continue

        filtrados.append(r)

    return jsonify(filtrados)

@app.post("/api/lancamentos")
def criar():

    d = request.json

    with conn() as c:

        c.execute(
            "INSERT INTO lancamentos(tipo,descricao,valor,vencimento,status) VALUES(?,?,?,?,?)",
            (
                d["tipo"],
                d["descricao"],
                d["valor"],
                d["vencimento"],
                "pendente"
            )
        )

        c.commit()

    titulo = (
        "💰 Conta a receber"
        if d["tipo"] == "receber"
        else "💸 Conta a pagar"
    )

    enviar(
        f"{titulo}\n\n"
        f"{d['descricao']}\n"
        f"Valor: R$ {d['valor']}\n"
        f"Vencimento: {d['vencimento']}"
    )

    return jsonify({"ok":True})

@app.patch("/api/pago/<int:i>")
def pago(i):

    with conn() as c:

        row = c.execute(
            "SELECT descricao FROM lancamentos WHERE id=?",
            (i,)
        ).fetchone()

        c.execute(
            "UPDATE lancamentos SET status='pago' WHERE id=?",
            (i,)
        )

        c.commit()

    if row:

        enviar(
            f"✅ Conta paga\n\n{row['descricao']}"
        )

    return jsonify({"ok":True})

@app.delete("/api/delete/<int:i>")
def delete(i):

    with conn() as c:

        c.execute(
            "DELETE FROM lancamentos WHERE id=?",
            (i,)
        )

        c.commit()

    return jsonify({"ok":True})

@app.post("/api/twilio")
def twilio():

    texto = request.form.get("Body","").lower().strip()

    if texto.startswith("pago "):

        nome = texto.replace("pago ","").strip()

        with conn() as c:

            row = c.execute(
                "SELECT id,descricao FROM lancamentos WHERE lower(descricao)=? AND status!='pago' LIMIT 1",
                (nome,)
            ).fetchone()

            if row:

                c.execute(
                    "UPDATE lancamentos SET status='pago' WHERE id=?",
                    (row["id"],)
                )

                c.commit()

                enviar(
                    f"✅ Conta marcada como paga\n\n{row['descricao']}"
                )

    return "ok"

if __name__ == "__main__":
    import os

app.run(
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 5000))
)
