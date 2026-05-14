import os
import re
import unicodedata

from flask import current_app


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
