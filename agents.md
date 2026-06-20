# AGENTS.md

## Progetto

Tazebao è un ERP web sviluppato con:

* Flask
* SQLAlchemy
* Alembic
* Bootstrap 5
* Vue.js (solo dove necessario)
* SQLite (sviluppo) / compatibilità futura DB server

L'obiettivo del progetto è mantenere:

* semplicità
* affidabilità
* leggibilità del codice
* coerenza UX/UI

---

# Regole generali

## 1. Modifiche minime

Modificare solo ciò che è necessario per il task richiesto.

Evitare:

* refactor non richiesti
* rinominare file senza motivo
* spostare codice non correlato
* modifiche estetiche collaterali

---

## 2. Nessuna regressione

Ogni task deve preservare il comportamento esistente.

Prima di modificare:

* individuare le funzionalità coinvolte
* verificare gli impatti collaterali

---

## 3. Nessuna modifica distruttiva implicita

Qualsiasi eliminazione deve richiedere conferma esplicita.

Esempi:

* clienti
* lavori
* task
* fatture
* preventivi
* pubblicazioni

---

## 4. Non toccare il database inutilmente

Non creare migration se non strettamente necessarie.

Quando una migration è necessaria:

* descrivere chiaramente la causa
* mantenere compatibilità con i dati esistenti

---

# Workflow task

Ogni attività deve avere un identificatore.

Formato:

ERP-XXXX

Esempi:

ERP-0503A
ERP-0503B
ERP-0504

Alla fine di ogni task fornire:

* causa reale
* file modificati
* comportamento finale
* verifiche eseguite

---

# Verifiche obbligatorie

Quando possibile eseguire:

```bash
python -m compileall app
```

e verificare:

* parse Jinja
* import Flask
* route coinvolte
* template modificati

Mai dichiarare un task concluso senza verifiche.

---

# UX/UI

## Principio

Tazebao deve avvicinarsi ai principi UX di:

* Linear
* Notion
* Stripe Dashboard

Non deve sembrare:

* pannello amministrativo generico
* gestionale anni 2010
* CRUD Bootstrap standard

---

# Table System

## UI-001

Dentro un `<td>` non devono esistere elementi impilati verticalmente.

Consentito:

* valore singolo
* badge singolo
* icona singola

Eccezione:

colonna principale con titolo + metadato.

Vietato:

* badge multipli
* badge + testo
* badge + data
* mini-card dentro una cella

---

## UI-002

Le righe devono mantenere altezza costante.

Una cella non deve aumentare l'altezza della riga.

---

## UI-003

Le tabelle mostrano solo le informazioni necessarie.

I dettagli appartengono:

* alla scheda dettaglio
* alla modifica
* ai tooltip

Non alla lista.

---

## UI-004

Su mobile:

NON usare card che impilano tutte le colonne.

Usare liste compatte.

---

# Mobile First

Ogni modifica UI deve essere verificata anche su:

* 320px
* 375px
* 390px
* 768px

Verificare:

* overflow
* wrapping
* pulsanti
* tabelle
* modali

---

# Sidebar

La sidebar segue stile Linear.

Evitare:

* alberi complessi
* gruppi collassabili inutili
* breadcrumb ridondanti

Preferire:

* navigazione semplice
* gerarchia chiara
* densità elevata

---

# Form System

Tutti i form devono utilizzare il pattern:

* erp-form-page
* erp-form-header
* erp-form-card
* erp-form-section
* erp-form-footer-actions

Ordine pulsanti:

Annulla → Salva

---

# Sicurezza

Mai:

* disabilitare CSRF
* esporre dati sensibili
* rimuovere controlli ruolo

Mantenere:

* login_required
* role_required
* validazione server-side

---

# Vue.js

Utilizzare Vue solo quando porta reale vantaggio.

Preferire:

* Jinja + Flask

per:

* form semplici
* liste semplici
* CRUD standard

---

# JavaScript

Preferenze progetto:

* codice chiaro
* funzioni piccole
* for...of consentito
* evitare complessità inutile

---

# Commit

Formato:

[ERP-XXXX] Descrizione breve

Esempi:

[ERP-0503B] Redesign invoices table

[ERP-0504] Unified form system

[ERP-0498R] Add effective invoice amount
