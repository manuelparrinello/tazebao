# ERP-0449 — Audit Finale Pre-Versione Stabile

## Stato Generale: ✅ **STABILE** (con riserve minori)

---

## VERIFICHE

### 1. Avvio progetto ✅
| Controllo | Esito |
|-----------|-------|
| `pip install -r requirements.txt` | OK — Flask 3.1.3, Werkzeug 3.1.8 |
| `flask db upgrade` | OK — 3 migrazioni applicate |
| `run.py` / `app.py` | OK — identici, `create_app()` funzionante |
| `.env.example` completo | OK — SECRET_KEY, EMAIL_CREDENTIALS_KEY, ERP_STORAGE_ROOT, ERP_MAX_UPLOAD_MB, ERP_MAX_FORM_MEMORY_MB |
| `compileall app/` | OK |

### 2. Auth / Ruoli ✅
| Controllo | Esito |
|-----------|-------|
| Login/logout POST | OK |
| Admin / Operatore / Readonly | OK — `@role_required` coerente |
| Protezioni server-side | OK — `before_request` guard, PUBLIC_ENDPOINTS |
| API CSRF exempt (solo api.bp) | OK |
| `@role_required("admin")` su users/admin_export | OK |
| Protezione ultimo admin attivo | OK |
| Auto-disattivazione impedita | OK |

### 3. Moduli Core ✅
| Modulo | Esito |
|--------|-------|
| Clienti | OK — 15 blueprints registrati, template esistenti |
| Lavori | OK |
| Task | OK |
| Preventivi | OK (con `print()` residuo — vedi MEDIO) |
| Finance | OK |
| Calendario | OK |
| Calendario Editoriale | OK |
| Moodboard | OK |
| File Explorer | OK |
| Mail / Comunicazioni | OK |
| Users / Admin | OK |
| Admin Export | OK |
| API REST | OK — 930 linee, pattern `api_response()` coerente |

### 4. UX Globale ✅
| Controllo | Esito |
|-----------|-------|
| Topbar | OK — responsive, live search, notifiche |
| Sidebar | OK — desktop fissa, mobile offcanvas |
| Notifiche | OK — polling /api/dashboard/summary ogni 60s |
| Live search | OK — endpoint `/api/search`, dropdown JS |
| Toast flash | OK — Bootstrap toasts, 4.5s auto-hide |
| Modale conferma | OK — `erp-confirm.js`, Promise-based, form interception |
| Badge compatti (`erp_badge`) | OK — 56 usi, 20 tipi mappati |
| Mobile 375px | OK — breakpoint 575.98px e 479.98px, card/tabella alternati |

### 5. File / Storage ✅
| Controllo | Esito |
|-----------|-------|
| Upload (whitelist estensioni, secure_filename) | OK |
| Rename (safe_path, safe_folder_name) | OK |
| Download (safe_path, send_file) | OK |
| Sottocartelle (normalize_subdir) | OK |
| Delete (safe_path, symlink guard) | OK |
| Path traversal (normpath + realpath check) | OK |
| ERP_STORAGE_ROOT configurabile | OK |

### 6. Regressioni Note
| Controllo | Esito |
|-----------|-------|
| Dashboard loading infinito | OK — `[v-cloak]`, spinner, loading flag, error state |
| API JSON che restituiscono HTML | OK — pattern coerente `api_response()` |
| Doppio submit | **VEDI MEDIO** — solo form distruttivi protetti |
| Doppio flash | OK — nessun pattern sospetto |
| Overflow tabelle | OK — `.table-responsive`, card mobili, text-truncate |
| Confirm modale bloccata | OK — `erpConfirming` flag, rimozione attributo dopo conferma |

---

## PROBLEMI TROVATI

### 🔴 BLOCCANTI (2)

| # | Problema | File | Impatto |
|---|----------|------|---------|
| **B1** | **`confirm()` mancante su tutte le azioni distruttive** | Tutti i template con form di delete | AGENTS.md richiede `onsubmit="return confirm('...')"` su ogni delete distruttivo. Attualmente **nessun template** ha `confirm()`. L'unica protezione è il modale `erp-confirm.js` via attributo `data-confirm-message`, ma manca in vari form (es. `cliente_delete`, `lavoro_delete`, `task_delete`, `editorial_purge`, `moodboard_delete`, `users_destroy`, `cartella_delete_file`, `cartella_delete_folder`). |
| **B2** | **`.title()` crash in `clienti.py nuovo_cliente()`** | `app/routes/clienti.py:21-27` | Se il form omette un campo (nome, ragsoc, indirizzo, città, provincia, email), `request.form.get("nome").title()` solleva `AttributeError` perché `.title()` su None crasha. Il server restituisce 500 anziché un errore gestito. |

### 🟡 MEDI (7)

| # | Problema | File | Note |
|---|----------|------|------|
| **M1** | **Sidebar collapse desktop non funzionante** | `static/js/sidebar.js` | `document.getElementById("btnSidebarCollapse")` non esiste in nessun template. Il pulsante di collasso sidebar non è mai stato implementato nell'HTML. |
| **M2** | **`window.erpBadge` mai definito** | `static/js/app.js:381-382` | Il codice Vue chiama `window.erpBadge?.html()` e `window.erpBadge?.label()` ma `window.erpBadge` non è mai stato assegnato. Protetto da optional chaining (`?.`), ma il codice non produce badge HTML funzionanti nel dashboard Vue. |
| **M3** | **Form non-distruttivi senza protezione doppio submit** | Tutti i form edit/nuovo | Pulsante submit può essere cliccato più volte. Solo form con `data-confirm-message` hanno protezione. |
| **M4** | **`print()` residuo in produzione** | `app/routes/preventivi.py:60` | `print("Cliente: " + cliente.name + ", ID: " + str(cliente.id))` |
| **M5** | **Nessun error handler 404/500** | `app/__init__.py` | Solo `RequestEntityTooLarge` è gestito. Utenti vedono pagina Flask default su 404/500. |
| **M6** | **Nessun logging strutturato** | Tutta l'app | Zero import `logging`. Errori vanno solo a stderr di Flask. |
| **M7** | **Alcune route mutation mancano try/except** | `clienti.py:183`, `lavori.py:295`, `preventivi.py:154,218`, `finance.py:140`, `editorial_calendar.py:514` | Rollback non gestito in route di delete/edit critiche. |

### 🟢 BASSI (10)

| # | Problema | File | Note |
|---|----------|------|------|
| **L1** | `delete_image_file()` non usa `safe_path()` | `editorial_calendar.py:489-497`, `moodboards.py:278-286` | Usa solo `startswith()` per validazione path. Basso rischio perché path viene dal DB. |
| **L2** | Route `/presentivi/addrow` (typo storico) | `preventivi.py:132` | Esiste sia versione typo sia corretta. Non rompe nulla ma è codice duplicato. |
| **L3** | `db.session.rollback()` prima di modifiche | `lavori.py:361` | Chiamata rollback prima di qualsiasi modifica DB. Inutile ma innocua. |
| **L4** | `parse_optional_datetime` senza try/except | `utils/parsing.py:18` | `datetime.fromisoformat(value)` non gestito, simile a `parse_optional_date` che invece è protetto. |
| **L5** | `g.current_user` vs `g.get("current_user")` misti | `auth.py`, `api.py` | Stesso file, stesse espressioni — stili incoerenti. |
| **L6** | Duplicato `.gitignore` | `.gitignore:7,13` | `app.db` listato due volte. |
| **L7** | Potenziale `KeyError` in `nuovo_preventivo` | `preventivi.py:56-58` | Accesso diretto `data["cliente_id"]` senza `.get()`. |
| **L8** | Search dropdown senza pulsante chiusura | `_navbar.html:44` | Si chiude solo su click outside o Escape. Accettabile ma migliorabile. |
| **L9** | Classi CSS inutilite: `.mobile-hide`, `.mobile-hide-sm`, `.mobile-priority-low` | `style.css` | Definite ma mai usate nei template. |
| **L10** | `form.submit()` bypassa validazione HTML5 | `erp-confirm.js` | Fallback `form.submit()` non attiva `required` fields. Basso impatto (solo form distruttivi). |

---

## COSA PUÒ ESSERE CONSIDERATO STABILE

| Modulo | Stabile? | Note |
|--------|----------|------|
| **Auth/login** | ✅ Sì | Pattern consolidato, session-based, role decorator coerente |
| **Clienti** | ✅ Sì | Dopo fix B2 (`.title()`) |
| **Lavori** | ✅ Sì | |
| **Task** | ✅ Sì | |
| **Preventivi** | ✅ Sì | Dopo rimozione `print()` (M4) |
| **Finance** | ✅ Sì | |
| **Calendario** | ✅ Sì | |
| **Moodboard** | ✅ Sì | |
| **File Explorer** | ✅ Sì | Protezione path traversal robusta |
| **Mail** | ✅ Sì | |
| **Users/Admin** | ✅ Sì | Protezione ultimo admin |
| **Admin Export** | ✅ Sì | |
| **API** | ✅ Sì | |
| **UX Mobile** | ⚠️ Quasi | Base solida, nessun fix urgente |
| **UX Desktop** | ⚠️ Quasi | Sidebar collapse da fixare (M1) |
| **Storage** | ✅ Sì | Safe path, normalize_subdir, secure_filename |

---

## ORDINE FIX CONSIGLIATO

### Fase 1 — Bloccanti (prima della release)
1. **B2** — `clienti.py:21-27` — Aggiungere `or ""` su ogni `request.form.get()`
2. **B1** — Aggiungere `data-confirm-message` a tutti i form di delete che ne sono sprovvisti

### Fase 2 — Medi (ciclo successivo)
3. **M1** — Decidere se implementare sidebar collapse o rimuovere il JS morto
4. **M2** — Decidere se implementare `window.erpBadge` o rimuovere il codice morto
5. **M3** — Aggiungere `:disabled` o `onsubmit` protection su form non-distruttivi
6. **M4** — Rimuovere `print()` da `preventivi.py`
7. **M5** — Aggiungere error handler 404/500
8. **M6** — Valutare se serve logging strutturato (tool interno, forse no)
9. **M7** — Aggiungere try/except sulle route mutation scoperte

### Fase 3 — Bassi (nice to have)
10. **L1** — Refactor `delete_image_file()` per usare `safe_path()`
11. **L4** — Aggiungere try/except in `parse_optional_datetime`
12. **L5** — Uniformare a `g.get("current_user")` o `g.current_user`
13. **L7** — Usare `.get()` in `nuovo_preventivo`
14. **L9** — Rimuovere classi CSS inutilite o usarle nei template
