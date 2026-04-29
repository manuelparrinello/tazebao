# Setup sviluppo ERP

## Nuovo PC

1. Crea il virtualenv:

```powershell
python -m venv venv
```

2. Attiva il virtualenv su Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

3. Installa le dipendenze:

```powershell
pip install -r requirements.txt
```

4. Copia il file ambiente di esempio:

```powershell
Copy-Item .env.example .env
```

5. Genera `EMAIL_CREDENTIALS_KEY`:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

6. Inserisci in `.env`:

```text
SECRET_KEY=una-chiave-lunga-casuale
EMAIL_CREDENTIALS_KEY=valore-generato-con-fernet
FLASK_ENV=development
```

In produzione `SECRET_KEY` e obbligatoria e deve arrivare dalle variabili ambiente.

7. Applica le migration:

```powershell
flask --app app.py db upgrade
```

8. Crea l'admin iniziale:

```powershell
flask --app app.py create-admin --email admin@example.com --password "Admin123!" --name "Admin"
```

9. Avvia l'app:

```powershell
python run.py
```

10. Apri:

```text
http://127.0.0.1:5000/login
```
