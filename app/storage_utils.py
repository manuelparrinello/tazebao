import os
import re
import unicodedata

from flask import current_app
from werkzeug.utils import secure_filename


MAX_SLUG_LENGTH = 60
CLIENTI_PREFIX = "clienti"
LAVORI_PREFIX = "lavori"


def slugify(text, max_length=MAX_SLUG_LENGTH):
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    if max_length:
        text = text[:max_length].rstrip("-")
    return text or "untitled"


def resolve_storage_root():
    return os.path.abspath(current_app.config["ERP_STORAGE_ROOT"])


def ensure_storage_dir(relative_path):
    abs_path = os.path.join(resolve_storage_root(), relative_path)
    os.makedirs(abs_path, exist_ok=True)
    return abs_path


def safe_path(relative_path):
    root = resolve_storage_root()
    abs_path = os.path.normpath(os.path.join(root, relative_path))
    if os.path.realpath(abs_path).startswith(os.path.realpath(root)):
        return abs_path
    return None


def get_cliente_relative_path(cliente_id, slug):
    return os.path.join(CLIENTI_PREFIX, f"{cliente_id}_{slug}").replace("\\", "/")


def get_lavoro_relative_path(lavoro_id, slug):
    return os.path.join(LAVORI_PREFIX, f"{lavoro_id}_{slug}").replace("\\", "/")


def resolve_collision(base_rel_path):
    root = resolve_storage_root()
    candidate = base_rel_path
    counter = 1
    while os.path.exists(os.path.join(root, candidate)):
        name, ext = os.path.splitext(base_rel_path)
        candidate = f"{name}_{counter}{ext}"
        counter += 1
    return candidate


def normalize_subdir(subdir):
    if not subdir:
        return ""
    raw = subdir.replace("\\", "/")
    if raw.startswith("/"):
        return None
    if os.path.isabs(raw):
        return None
    normalized = raw.strip("/")
    if ".." in normalized.split("/"):
        return None
    return normalized


def build_breadcrumb(subdir, root_url_func, root_label):
    segments = [{"label": root_label, "subdir": None, "url": root_url_func()}]
    if not subdir:
        return segments
    parts = subdir.strip("/").split("/")
    cumulative = ""
    for part in parts:
        cumulative = f"{cumulative}/{part}" if cumulative else part
        segments.append({
            "label": part,
            "subdir": cumulative,
            "url": root_url_func(subdir=cumulative),
        })
    return segments


def list_entries(abs_path):
    entries = []
    if not abs_path or not os.path.isdir(abs_path):
        return entries
    for name in os.listdir(abs_path):
        full = os.path.join(abs_path, name)
        try:
            is_dir = os.path.isdir(full)
            size = os.path.getsize(full) if os.path.isfile(full) else None
            mtime = os.path.getmtime(full)
        except (OSError, PermissionError):
            continue
        entries.append({
            "name": name,
            "is_dir": is_dir,
            "size": size,
            "mtime": mtime,
        })
    entries.sort(key=lambda e: (not e["is_dir"], e["name"].lower()))
    return entries


ALLOWED_STORAGE_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.odt', '.xls', '.xlsx', '.csv',
    '.txt', '.md', '.ppt', '.pptx',
    '.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg',
    '.ai', '.psd', '.eps', '.indd', '.idml', '.tiff', '.tif',
    '.mp4', '.mov', '.avi', '.mkv', '.webm',
    '.mp3', '.wav', '.aiff', '.flac',
    '.zip', '.rar', '.7z',
    '.blend', '.aep', '.prproj',
}


def allowed_storage_file(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_STORAGE_EXTENSIONS


def unique_filename(directory, filename):
    name, ext = os.path.splitext(filename)
    counter = 1
    candidate = filename
    while os.path.exists(os.path.join(directory, candidate)):
        candidate = f"{name}_{counter}{ext}"
        counter += 1
    return candidate


def save_uploaded_storage_file(file, target_dir):
    original_name = secure_filename(file.filename or "file")
    if not original_name:
        raise ValueError("Nessun file selezionato.")
    if not allowed_storage_file(original_name):
        raise ValueError("Estensione non consentita.")
    safe_name = unique_filename(target_dir, original_name)
    abs_path = os.path.join(target_dir, safe_name)
    file.save(abs_path)
    return safe_name


def safe_folder_name(name):
    name = name.strip()
    if not name:
        return None
    if "/" in name or "\\" in name:
        return None
    if ".." in name:
        return None
    if os.path.isabs(name):
        return None
    if name.startswith("."):
        return None
    return name


def create_subfolder(base_dir, folder_name):
    safe_name = safe_folder_name(folder_name)
    if not safe_name:
        raise ValueError("Inserisci un nome cartella valido.")
    target = os.path.join(base_dir, safe_name)
    if os.path.exists(target):
        raise ValueError("Cartella già esistente.")
    try:
        os.makedirs(target)
    except OSError as e:
        raise ValueError(f"Errore nella creazione della cartella: {str(e)}")
    return safe_name
