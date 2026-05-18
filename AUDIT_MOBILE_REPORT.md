# ERP-0447 — Audit Mobile UI (375px viewport)

## Metodologia
- Viewport simulato: **375×667px** (iPhone SE / Galaxy S20)
- Ogni rotta è stata esaminata per: overflow orizzontale, elementi troncati, layout rotto, UX tattile insufficiente
- Il CSS esistente ha già responsive breakpoint a 991.98px, 575.98px, 479.98px
- `.app-content` a 375px: padding orizzontale `0.75rem` → ~**351px utili**

---

## Risultati

### 🔴 ALTA PRIORITÀ (da fixare assolutamente)

| # | Pagina | Problema | File coinvolti |
|---|--------|----------|----------------|
| **A1** | Tutte le pagine con tabelle desktop a larghezza fissa | Tabelle avvolte in `table-responsive` con `d-none d-md-block`. Le mobile-card sottostanti hanno action button in fila (es. modifica + elimina). A 375px i pulsanti sono molto stretti ma gestibili. **OK in produzione**. |
| **A2** | Impostazioni / users.html | Bottone "Elimina definitivamente" ha label lunga. **Già gestito**: `.users-destroy-label { display: none }` a ≤900px (style.css:1293). Label scompare, rimane solo icona. ✅ |

**Nessun problema ALTA trovato.** Le pagine sono già ben gestite su mobile.

### 🟡 MEDIA PRIORITÀ (migliorabili)

| # | Pagina | Problema | File coinvolti |
|---|--------|----------|----------------|
| **M1** | Dettaglio Cliente/Lavoro | Path cartella in `<code>` tag senza `word-break`. Nomi lunghi (>351px *prima del troncamento*) escono dal contenitore. | `templates/cliente.html`, `templates/lavoro.html`, `style.css` |
| **M2** | Preventivo (new) | Pulsante "Cerca" con `btn-lg` + `px-4` è sproporzionato a 375px. In una `d-flex gap-2`, l'input si restringe molto. | `templates/preventivo_new.html` |
| **M3** | Preventivo / Finance / Dashboard | Stat card con `.display-6` o `.h4` (es. "In cassa € 123.456,78"). Bootstrap `display-6` è `2.5rem` di default. A 375px su `col-6` (~160px per card) numeri molto grandi possono overfloware. | `templates/dashboard.html`, `templates/finance.html`, `style.css:1140` (già riduce `.preventivo-summary-card .display-6` a 1.35rem) |
| **M4** | File Browser (mobile card) | Nome file lungo senza ellipsis. La card mobile ha nome file + 3 pulsanti azione (download, rinomina, elimina). I pulsanti sono `btn-sm` (~32px), totale ~120px per bottoni. Residuo ~230px per nome file. **OK per nomi medi, nomi >30 caratteri overflowano.** | `templates/_file_browser.html`, `style.css:4755-4760` (ellipsis già presente per vista tabella ma non per mobile card) |
| **M5** | Preventivo vista stampa | `.quote-summary-table` in `col-6 col-md-3` ha `word-break: break-word`. Tuttavia la tabella nella vista stampa non è responsive. **Non bloccante** (stampa è desktop-first). |

### 🟢 BASSA PRIORITÀ (nice to have)

| # | Pagina | Problema | File coinvolti |
|---|--------|----------|----------------|
| **B1** | Tutte le pagine con `.topbar-center` | A 375px il search input + notifica + avatar + plus sono affollati. La search bar rimane visibile (nessun collapse), ma lo spazio è tirato. | `templates/_navbar.html`, `style.css` |
| **B2** | Calendario | "Mese precedente" / "Mese successivo" hanno testo + icona. Su 375px i due bottoni affiancati occupano quasi tutta la larghezza. | `templates/calendar.html` |
| **B3** | Calendario editoriale | Layout colonne fitte nella lista pubblicazioni a 375px. | `templates/editorial_calendar.html` |
| **B4** | Dashboard KPIs | 4 colonne a 375px diventano `col-6` (2 per fila). Icone + testi lunghi (es. "Fatturato annuo €") possono troncare. | `templates/dashboard.html` |

---

## Statistiche

| Categoria | Conteggio |
|-----------|-----------|
| 🔴 Alta priorità | **0** |
| 🟡 Media priorità | **5** |
| 🟢 Bassa priorità | **4** |
| **Totale problemi** | **9** |
| **Già gestiti** | **3** (users destroy label, search dropdown, toast/confirm modal) |

---

## Conclusione

L'interfaccia mobile è già in buono stato: i template usano `d-none d-md-block` / `d-md-none` sistematicamente, il CSS ha breakpoint dedicati, e componenti critici (confirm modale, toast, search dropdown) sono già responsive.

I veri problemi sono di **dettaglio** — non ci sono rotture strutturali. La priorità maggiore tra quelle emerse è:

1. **M1** — `<code>` path overflow (impatto basso ma visibile)
2. **M4** — File browser mobile card senza ellipsis (impatto su nomi lunghi)
3. **M3** — `.display-6` stat cards (impatto su cifre grandi)
4. **M2/M5** — Preventivo (form e vista stampa) dettagli minori

Consiglio fix diretto per M1, M4, M3 in un unico intervento, e eventualmente M2 in un secondo momento.
