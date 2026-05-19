# Route HTML

Tutte le route HTML (non `/api/`) organizzate per blueprint. Le route elencate sono quelle registrate direttamente sui blueprint; gli alias legacy endpoint sono esclusi (vedi `register_legacy_endpoint_aliases` in `__init__.py`).

## Blueprint: `auth`

| Metodo | URL | View function | Guard | Descrizione |
|--------|-----|---------------|-------|-------------|
| GET, POST | `/login` | `login` | public | Form login + autenticazione |
| POST | `/logout` | `logout` | — | Clear session, redirect a login |

## Blueprint: `main`

| Metodo | URL | View function | Guard | Descrizione |
|--------|-----|---------------|-------|-------------|
| GET | `/` | `index` | public | Home page (app shell) |
| GET | `/app` | `app_shell` | `login_required` | App shell principale (SPA-like) |
| GET | `/test` | `test` | public | Pagina test (base.html) |
| GET | `/search` | `search` | `login_required` | Ricerca globale multientità (HTML) |
| GET | `/api/search` | `api_search` | `login_required` | Ricerca globale JSON |

## Blueprint: `clienti`

| Metodo | URL | View function | Guard | Descrizione |
|--------|-----|---------------|-------|-------------|
| GET, POST | `/clienti/new` | `nuovo_cliente` | admin, operatore | Creazione nuovo cliente |
| GET | `/clienti` | `clienti` | `login_required` | Lista clienti |
| GET | `/clienti/<int:cliente_id>` | `cliente_page` | `login_required` | Dettaglio cliente (lavori, task, eventi, preventivi, finance, email) |
| DELETE | `/clienti/<int:cliente_id>` | `cliente_delete` | admin, operatore | Eliminazione cliente + cartella |
| GET, PUT | `/clienti/edit/<int:cliente_id>` | `cliente_edit` | admin, operatore | Modifica anagrafica cliente |
| POST | `/clienti/<int:cliente_id>/cartella/crea` | `cliente_cartella_crea` | admin, operatore | Crea cartella storage cliente |
| GET | `/clienti/<int:cliente_id>/cartella` | `cliente_cartella` | `login_required` | File browser cartella cliente |
| POST | `/clienti/<int:cliente_id>/cartella/upload` | `cliente_cartella_upload` | admin, operatore | Upload file in cartella |
| POST | `/clienti/<int:cliente_id>/cartella/sottocartella/crea` | `cliente_cartella_sottocartella_crea` | admin, operatore | Crea sottocartella |
| POST | `/clienti/<int:cliente_id>/cartella/rinomina` | `cliente_cartella_rename` | admin, operatore | Rinomina file/cartella |
| POST | `/clienti/<int:cliente_id>/cartella/elimina/<path:filename>` | `cliente_cartella_delete_file` | admin, operatore | Elimina file |
| POST | `/clienti/<int:cliente_id>/cartella/elimina-cartella/<path:dirname>` | `cliente_cartella_delete_folder` | admin, operatore | Elimina cartella vuota |
| GET | `/clienti/<int:cliente_id>/cartella/download/<path:filename>` | `cliente_cartella_download` | `login_required` | Download file |

## Blueprint: `lavori`

| Metodo | URL | View function | Guard | Descrizione |
|--------|-----|---------------|-------|-------------|
| GET, POST | `/lavori/new` | `nuovo_lavoro` | admin, operatore | Creazione nuovo lavoro |
| GET | `/lavori` | `lavori` | `login_required` | Lista lavori |
| GET | `/lavori/<int:lavoro_id>` | `lavoro_page` | `login_required` | Dettaglio lavoro |
| GET, POST | `/lavori/<int:lavoro_id>/edit` | `lavoro_edit` | admin, operatore | Modifica lavoro |
| POST | `/lavori/<int:lavoro_id>/remove-pdf` | `lavoro_remove_pdf` | admin, operatore | Rimuovi PDF preventivo |
| POST | `/lavori/<int:lavoro_id>/delete` | `lavoro_delete` | admin, operatore | Elimina lavoro (con blocchi) |
| PATCH | `/lavori/<int:lavoro_id>` | `status_lavoro_update` | admin, operatore | Aggiorna stato lavoro |
| POST | `/lavori/<int:lavoro_id>/cartella/crea` | `lavoro_cartella_crea` | admin, operatore | Crea cartella storage lavoro |
| GET | `/lavori/<int:lavoro_id>/cartella` | `lavoro_cartella` | `login_required` | File browser cartella lavoro |
| POST | `/lavori/<int:lavoro_id>/cartella/upload` | `lavoro_cartella_upload` | admin, operatore | Upload file |
| POST | `/lavori/<int:lavoro_id>/cartella/sottocartella/crea` | `lavoro_cartella_sottocartella_crea` | admin, operatore | Crea sottocartella |
| POST | `/lavori/<int:lavoro_id>/cartella/rinomina` | `lavoro_cartella_rename` | admin, operatore | Rinomina file/cartella |
| POST | `/lavori/<int:lavoro_id>/cartella/elimina/<path:filename>` | `lavoro_cartella_delete_file` | admin, operatore | Elimina file |
| POST | `/lavori/<int:lavoro_id>/cartella/elimina-cartella/<path:dirname>` | `lavoro_cartella_delete_folder` | admin, operatore | Elimina cartella vuota |
| GET | `/lavori/<int:lavoro_id>/cartella/download/<path:filename>` | `lavoro_cartella_download` | `login_required` | Download file |

## Blueprint: `preventivi`

| Metodo | URL | View function | Guard | Descrizione |
|--------|-----|---------------|-------|-------------|
| GET, POST | `/preventivi/nuovo` | `nuovo_preventivo` | admin, operatore | Crea preventivo (JSON POST) |
| GET | `/preventivi` | `preventivi` | `login_required` | Lista preventivi con filtri |
| POST | `/presentivi/addrow` | `render_row` | admin, operatore | Render riga preventivo |
| POST | `/preventivi/addrow` | `render_row` | admin, operatore | Render riga preventivo (alias) |
| GET | `/preventivi/visualizza/<int:id>` | `visualizza_preventivo` | `login_required` | Dettaglio preventivo |
| GET, POST | `/preventivi/<int:id>/edit` | `preventivo_edit` | admin, operatore | Modifica preventivo |
| POST | `/preventivi/<int:id>/delete` | `preventivo_delete` | admin, operatore | Elimina preventivo |
| POST | `/preventivi/<int:id>/converti-in-lavoro` | `converti_preventivo_in_lavoro` | admin, operatore | Converti preventivo in lavoro |

## Blueprint: `tasks`

| Metodo | URL | View function | Guard | Descrizione |
|--------|-----|---------------|-------|-------------|
| GET | `/tasks` | `tasks` | `login_required` | Lista task con filtri |
| GET, POST | `/tasks/new` | `task_new` | admin, operatore | Crea nuovo task |
| GET, POST | `/tasks/<int:task_id>/edit` | `task_edit` | admin, operatore | Modifica task |
| POST | `/tasks/<int:task_id>/delete` | `task_delete` | admin, operatore | Elimina task |

## Blueprint: `calendar`

| Metodo | URL | View function | Guard | Descrizione |
|--------|-----|---------------|-------|-------------|
| GET | `/calendar` | `calendar_index` | `login_required` | Calendario mensile con eventi + scadenze task |
| GET, POST | `/calendar/new` | `calendar_new` | admin, operatore | Crea evento |
| POST | `/calendar/<int:event_id>/delete` | `calendar_delete` | admin, operatore | Elimina evento |
| GET, POST | `/calendar/<int:event_id>/edit` | `calendar_edit` | admin, operatore | Modifica evento |

## Blueprint: `editorial_calendar`

| Metodo | URL | View function | Guard | Descrizione |
|--------|-----|---------------|-------|-------------|
| GET | `/editorial-calendar` | `editorial_index` | `login_required` | Vista lista piano editoriale |
| GET | `/editorial-calendar/clienti/<int:cliente_id>` | `client_calendar` | `login_required` | Calendario editoriale per cliente |
| GET, POST | `/editorial-calendar/new` | `editorial_new` | admin, operatore | Crea pubblicazione |
| GET, POST | `/editorial-calendar/<int:publication_id>/edit` | `editorial_edit` | admin, operatore | Modifica pubblicazione |
| POST | `/editorial-calendar/<int:publication_id>/images/<int:image_id>/delete` | `editorial_image_delete` | admin, operatore | Elimina immagine pubblicazione |
| POST | `/editorial-calendar/<int:publication_id>/delete` | `editorial_delete` | admin, operatore | Annulla pubblicazione (soft-delete) |
| POST | `/editorial-calendar/<int:publication_id>/purge` | `editorial_purge` | admin, operatore | Elimina definitivamente pubblicazione |

## Blueprint: `moodboards`

| Metodo | URL | View function | Guard | Descrizione |
|--------|-----|---------------|-------|-------------|
| GET | `/moodboards` | `moodboard_index` | `login_required` | Lista moodboard |
| GET | `/moodboards/<int:id>` | `moodboard_detail` | `login_required` | Dettaglio moodboard con immagini |
| GET, POST | `/moodboards/new` | `moodboard_new` | admin, operatore | Crea moodboard |
| GET, POST | `/moodboards/<int:id>/edit` | `moodboard_edit` | admin, operatore | Modifica moodboard |
| POST | `/moodboards/<int:id>/delete` | `moodboard_delete` | admin, operatore | Elimina moodboard |
| POST | `/moodboards/<int:id>/images` | `moodboard_add_image` | admin, operatore | Aggiungi immagine (upload o URL) |
| POST | `/moodboards/<int:id>/images/<int:image_id>/delete` | `moodboard_delete_image` | admin, operatore | Elimina immagine moodboard |
| GET | `/tasks/<int:task_id>/moodboard` | `task_moodboard` | `login_required` | Redirect alla moodboard del task |

## Blueprint: `finance`

| Metodo | URL | View function | Guard | Descrizione |
|--------|-----|---------------|-------|-------------|
| GET | `/finance` | `finance_index` | `login_required` | Dashboard finanziaria mensile |
| GET, POST | `/finance/new` | `finance_new` | admin, operatore | Crea movimento finanziario |
| GET, POST | `/finance/<int:movement_id>/edit` | `finance_edit` | admin, operatore | Modifica movimento |
| POST | `/finance/<int:movement_id>/delete` | `finance_delete` | admin, operatore | Elimina movimento |

## Blueprint: `emails`

| Metodo | URL | View function | Guard | Descrizione |
|--------|-----|---------------|-------|-------------|
| GET | `/emails` | `emails_index` | `login_required` | Lista log comunicazioni |
| GET, POST | `/emails/new` | `emails_new` | admin, operatore | Registra comunicazione |
| GET, POST | `/emails/<int:email_id>/edit` | `emails_edit` | admin, operatore | Modifica comunicazione |
| POST | `/emails/<int:email_id>/delete` | `emails_delete` | admin, operatore | Elimina comunicazione |

## Blueprint: `mail`

| Metodo | URL | View function | Guard | Descrizione |
|--------|-----|---------------|-------|-------------|
| GET | `/mail` | `mail_index` | `login_required` | Lista messaggi email (IMAP) |
| GET | `/mail/<int:message_id>` | `mail_detail` | `login_required` | Dettaglio messaggio (auto-segna letto) |
| GET, POST | `/mail/new` | `mail_new` | admin, operatore | Composizione nuova email |
| GET, POST | `/mail/<int:message_id>/reply` | `mail_reply` | admin, operatore | Rispondi a email |
| POST | `/mail/<int:message_id>/link` | `mail_link` | admin, operatore | Collega messaggio a cliente/lavoro |
| GET | `/mail/accounts` | `mail_accounts` | admin | Lista account email |
| GET, POST | `/mail/accounts/new` | `mail_account_new` | admin | Crea account email |
| GET, POST | `/mail/accounts/<int:account_id>/edit` | `mail_account_edit` | admin | Modifica account |
| POST | `/mail/accounts/<int:account_id>/sync` | `mail_account_sync` | admin | Sync IMAP account |

## Blueprint: `users`

| Metodo | URL | View function | Guard | Descrizione |
|--------|-----|---------------|-------|-------------|
| GET | `/users` | `users_index` | admin | Lista utenti |
| GET, POST | `/users/new` | `users_new` | admin | Crea utente |
| GET, POST | `/users/<int:user_id>/edit` | `users_edit` | admin | Modifica utente |
| POST | `/users/<int:user_id>/deactivate` | `users_deactivate` | admin | Disattiva utente |
| POST | `/users/<int:user_id>/delete` | `users_delete` | admin | Soft-delete (disattiva) |
| POST | `/users/<int:user_id>/destroy` | `users_destroy` | admin | Eliminazione definitiva |
| POST | `/users/<int:user_id>/activate` | `users_activate` | admin | Riattiva utente |
| GET, POST | `/users/<int:user_id>/password` | `users_password` | admin | Cambia password |

## Blueprint: `admin_export`

| Metodo | URL | View function | Guard | Descrizione |
|--------|-----|---------------|-------|-------------|
| GET | `/admin/export` | `export_index` | admin | Pagina export con lista risorse |
| GET | `/admin/export/<resource>.csv` | `export_csv` | admin | Export CSV di una risorsa |
| GET | `/admin/export/<resource>.json` | `export_json` | admin | Export JSON di una risorsa |

**Risorse export**: `clienti`, `lavori`, `task`, `preventivi`, `calendar`, `finance`, `editorial_publications`, `users`
