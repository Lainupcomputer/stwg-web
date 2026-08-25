# STWG Web – Technische Projektdokumentation

> **Projekt:** STWG Web  
> **Repository:** `Lainupcomputer/stwg-web`  
> **Dokumentationsstand:** 25.08.2026  
> **Technologie:** Python / Flask / SQLAlchemy / MariaDB / Discord / JavaScript  
> **Status:** Produktives Community-Management-System

---

## Inhaltsverzeichnis

1. [Projektübersicht](#1-projektübersicht)
2. [Systemarchitektur](#2-systemarchitektur)
3. [Repository-Struktur](#3-repository-struktur)
4. [Anwendungsstart](#4-anwendungsstart)
5. [Flask-Anwendung](#5-flask-anwendung)
6. [Authentifizierung](#6-authentifizierung)
7. [Benutzer- und Berechtigungssystem](#7-benutzer--und-berechtigungssystem)
8. [Datenbank](#8-datenbank)
9. [ActionQueue](#9-actionqueue)
10. [DataStorage](#10-datastorage)
11. [Marktsystem](#11-marktsystem)
12. [Market Grabber](#12-market-grabber)
13. [Market Alerts](#13-market-alerts)
14. [Training](#14-training)
15. [Benutzerverwaltung](#15-benutzerverwaltung)
16. [Messaging](#16-messaging)
17. [Tickets](#17-tickets)
18. [Warehouse](#18-warehouse)
19. [Orders](#19-orders)
20. [Regelverwaltung](#20-regelverwaltung)
21. [Dokumente und Meetings](#21-dokumente-und-meetings)
22. [Voice Credits](#22-voice-credits)
23. [Browser-Games](#23-browser-games)
24. [Server- und Worker-Control](#24-server--und-worker-control)
25. [Frontend](#25-frontend)
26. [Konfiguration](#26-konfiguration)
27. [Deployment](#27-deployment)
28. [Security](#28-security)
29. [Performance](#29-performance)
30. [Logging](#30-logging)
31. [Tests](#31-tests)
32. [Bekannte technische Schulden](#32-bekannte-technische-schulden)
33. [Empfohlene Zielarchitektur](#33-empfohlene-zielarchitektur)
34. [Roadmap](#34-roadmap)
35. [Gesamtbewertung](#35-gesamtbewertung)
36. [Fazit](#36-fazit)

---

# 1. Projektübersicht

STWG Web ist eine zentrale Web- und Verwaltungsplattform für das STWG-System.

Das Projekt verbindet eine Flask-Webanwendung mit:

- Discord OAuth
- Discord-Rollen
- Benutzerverwaltung
- MariaDB
- SQLAlchemy
- Hintergrund-Workern
- einer datenbankbasierten ActionQueue
- Marktüberwachung
- Preisalarmen
- Messaging
- Training
- Warehouse
- Orders
- Tickets
- Dokumentenverwaltung
- Meetings
- Voice Credits
- Server-/Worker-Control
- Browser-Games

Das Projekt ist damit kein klassisches kleines Flask-Webprojekt mehr, sondern eine integrierte Community-Management-Plattform.

---

# 2. Systemarchitektur

## 2.1 Gesamtübersicht

```text
                         ┌──────────────────────┐
                         │       Discord        │
                         │ OAuth / Bot / Rollen │
                         └──────────┬───────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────┐
│                     STWG WEB / FLASK                       │
│                                                            │
│ Auth · Users · Training · Market · Warehouse · Messaging   │
│ Orders · Tickets · Rules · Documents · Games · Admin      │
└──────────────────────────┬─────────────────────────────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │     MariaDB      │
                  │    SQLAlchemy    │
                  └────────┬─────────┘
                           │
             ┌─────────────┼──────────────┐
             ▼             ▼              ▼
      ┌────────────┐ ┌─────────────┐ ┌─────────────┐
      │ Market     │ │ ActionQueue │ │ DataStorage │
      │ Grabber    │ │             │ │             │
      └─────┬──────┘ └──────┬──────┘ └─────────────┘
            │                │
            ▼                ▼
       externe API       Discord Bot


## 2.2 Hauptkomponenten

Das System besteht aus mehreren logisch getrennten Komponenten:

### Webserver

Verantwortlich für:

* HTTP-Anfragen
* Benutzeroberfläche
* API-Endpunkte
* Authentifizierung
* Berechtigungen
* Datenbankzugriff
* administrative Funktionen

### Datenbank

MariaDB dient als zentrale Datenquelle.

### Worker

Worker übernehmen Aufgaben, die nicht direkt innerhalb eines HTTP-Requests ausgeführt werden sollten.

Beispiele:

* Markt-Datensammlung
* Marktalarme
* weitere Hintergrundaufgaben

### Discord Bot

Der Discord-Bot ist für Discord-spezifische Aktionen zuständig.

Die Kommunikation kann über die `ActionQueue` erfolgen.

### Reverse Proxy

Nginx steht vor dem Webserver und übernimmt unter anderem:

* HTTPS
* Domainrouting
* Reverse Proxy
* Weiterleitung an Gunicorn

---

# 3. Repository-Struktur

Die zentrale Struktur des Projekts ist:

```text
stwg-web/
│
├── blueprints/
├── database/
├── helper/
├── static/
├── templates/
│
├── app.py
├── main.py
├── market_grabber.py
└── market_alert_checker.py
```

## 3.1 `blueprints/`

Die Flask-Anwendung ist in fachliche Bereiche aufgeteilt.

Unter anderem:

```text
auth
user
training
market
market_alerts
warehouse
messaging
meeting
rules
document
orders
voice_credits
jetpack
wasp
control
```

Diese Struktur verhindert, dass sämtliche Routen in einer einzigen Flask-Datei landen.

---

## 3.2 `database/`

Enthält:

* Datenbankinitialisierung
* SQLAlchemy
* Datenmodelle

Das zentrale Model-Modul enthält einen großen Teil der fachlichen Datenstruktur des Projekts.

---

## 3.3 `helper/`

Enthält wiederverwendbare Hilfsfunktionen.

Ein wichtiger Bereich ist die Berechtigungsprüfung.

---

## 3.4 `static/`

```text
static/
├── img/
├── script/
└── style/
```

Hier liegen Frontend-Ressourcen.

---

## 3.5 `templates/`

Die Jinja2-Templates sind ebenfalls fachlich organisiert.

Beispiel:

```text
templates/
├── control/
├── document/
├── errors/
├── jetpack_game/
├── main/
├── market/
├── meeting/
├── orders/
├── partials/
├── rules/
├── training/
├── voice_credits/
├── warehouse/
├── wasp_game/
└── ...
```

---

# 4. Anwendungsstart

Der zentrale Einstiegspunkt ist `main.py`.

Die Anwendung initialisiert:

* Flask
* Konfiguration
* Datenbank
* Session
* Error Handler
* Blueprints

Die Blueprints werden zentral registriert.

Das ermöglicht eine einheitliche Flask-Anwendung trotz der vielen Fachbereiche.

---

# 5. Flask-Anwendung

## 5.1 Architektur

Die Anwendung folgt grundsätzlich diesem Muster:

```text
HTTP Request
     │
     ▼
Blueprint
     │
     ▼
Berechtigungsprüfung
     │
     ▼
Business Logic
     │
     ▼
SQLAlchemy
     │
     ▼
MariaDB
```

Bei Aktionen für Discord:

```text
Blueprint
     │
     ▼
ActionQueue
     │
     ▼
Discord Bot
```

---

## 5.2 Vorteile

Die Blueprint-Struktur bietet:

* bessere Wartbarkeit
* klare Zuständigkeiten
* einfachere Erweiterbarkeit
* kleinere einzelne Module
* geringere Kopplung zwischen Fachbereichen

---

# 6. Authentifizierung

Die Authentifizierung erfolgt über Discord OAuth.

Der Ablauf ist:

```text
Browser
   │
   ▼
Discord OAuth
   │
   ▼
Authorization Code
   │
   ▼
Discord Token
   │
   ▼
Discord User API
   │
   ▼
Guild-/Rollenprüfung
   │
   ▼
Flask Session
```

Dadurch muss für Benutzer kein separates Passwortsystem betrieben werden.

Discord stellt die Identität bereit.

---

## 6.1 Vorteile

* kein eigenes Passwortmanagement
* Discord ist bereits die zentrale Identität
* Rollen können zur Rechteermittlung genutzt werden
* Benutzer können über Discord eindeutig erkannt werden

---

# 7. Benutzer- und Berechtigungssystem

Das Berechtigungssystem basiert auf mehreren Ebenen.

```text
Discord
   │
   ├── Benutzer
   ├── Rollen
   │
   ▼
UserProfile
   │
   ├── Lizenzen
   ├── Status
   └── Mitgliederdaten
   │
   ▼
Session
   │
   ├── is_admin
   ├── is_trainer
   ├── is_supporter
   └── weitere Flags
```

## 7.1 Lizenzen

Lizenzen werden verwendet, um zusätzliche Funktionen freizuschalten.

Beispiele:

```text
Ausbilder
Supporter
Leitung
```

## 7.2 Helper

Berechtigungen werden über Helper-Funktionen geprüft.

Beispiel:

```python
@require_role_management
```

Dadurch können administrative Routen geschützt werden.

---

## 7.3 Verbesserungspotenzial

Langfristig wäre ein zentralisiertes Permission-System sinnvoll:

```python
current_user.can("training.manage")
current_user.can("warehouse.manage")
current_user.can("messaging.manage")
current_user.can("system.control")
```

Dadurch wären Rechte nicht mehr über viele verschiedene Session-Flags verteilt.

---

# 8. Datenbank

Die Datenbank basiert auf:

```text
MariaDB
   │
   ▼
SQLAlchemy
   │
   ▼
Flask
```

Die Datenbank enthält verschiedene fachliche Domänen.

---

## 8.1 Benutzer

```text
UserProfile
Comment
Warning
GroupAction
```

---

## 8.2 Kommunikation

```text
Ticket
DMMessage
MessagePreset
ActionQueue
```

---

## 8.3 Markt

```text
MarketItem
MarketPriceHistory
MarketAlert
```

---

## 8.4 Training

```text
Training
TrainingCompletion
```

---

## 8.5 Warehouse

```text
Warehouse
WarehouseItem
```

---

## 8.6 Games

```text
JetpackHighscore
WaspHighscore
```

---

## 8.7 System

```text
DataStorage
StatusMessage
VoiceCreditChannel
```

---

## 8.8 Dokumente

```text
InternalDocument
TeamMeeting
RuleField
```

---

# 9. ActionQueue

Die `ActionQueue` ist eine zentrale Integrationskomponente.

Sie dient als Verbindung zwischen:

```text
Web
Worker
   │
   ▼
ActionQueue
   │
   ▼
Discord Bot
```

Eine Queue-Aktion besteht grundsätzlich aus:

```text
id
key
data
timestamp
```

Beispiel:

```json
{
    "userId": 123456789,
    "text": "Beispielnachricht"
}
```

mit einem Action-Key wie:

```text
send_user_message
```

---

## 9.1 Warum die Queue sinnvoll ist

Die Webanwendung muss nicht auf eine direkte Discord-Antwort warten.

Stattdessen:

```text
Web Request
    │
    ▼
DB INSERT
    │
    ▼
HTTP Response
```

Der Bot kann später:

```text
ActionQueue
    │
    ▼
Action lesen
    │
    ▼
Discord API
```

ausführen.

---

## 9.2 Vorteile

* Entkopplung
* bessere Fehlertoleranz
* keine direkte Bot-Abhängigkeit im Request
* Worker können ebenfalls Aktionen erzeugen
* gemeinsame Schnittstelle

---

## 9.3 Empfohlene Queue 2.0

Für einen noch robusteren Betrieb:

```text
ActionQueue
├── id
├── action
├── payload
├── status
├── created_at
├── started_at
├── completed_at
├── locked_at
├── retry_count
├── max_retries
└── error
```

Status:

```text
PENDING
PROCESSING
COMPLETED
FAILED
```

Ablauf:

```text
PENDING
   │
   ▼
PROCESSING
   │
   ├── Erfolg ──► COMPLETED
   │
   └── Fehler ──► RETRY
                    │
                    └── FAILED
```

---

# 10. DataStorage

`DataStorage` ist ein generischer Key-Value-Speicher.

```text
key
data
```

Er kann für Einstellungen und dynamische Konfigurationen verwendet werden.

Beispielbereiche:

```text
hooks.*
market.*
worker.*
settings.*
```

---

## 10.1 Vorteile

* sehr flexibel
* neue Einstellungen ohne neues Datenbankmodell
* einfach zu erweitern

---

## 10.2 Nachteile

Alle Werte sind logisch weniger stark typisiert.

Beispielsweise können boolesche Werte als String gespeichert werden:

```text
"true"
```

anstatt:

```text
True
```

Dadurch muss der jeweilige Verbraucher wissen, wie der Wert interpretiert werden soll.

---

## 10.3 Empfehlung

Langfristig:

```text
DataStorage
    │
    ├── normale Konfiguration
    │
    └── keine Secrets
```

Secrets sollten über Environment-Variablen oder einen Secret Store verwaltet werden.

---

# 11. Marktsystem

Das Marktsystem ist eines der technisch umfangreichsten Subsysteme.

```text
Externe Markt-API
        │
        ▼
Market Grabber
        │
        ▼
MarketItem
        │
        ▼
MarketPriceHistory
        │
        ├──────────────┐
        ▼              ▼
     Graphen       MarketAlert
                       │
                       ▼
              Alert Checker
                       │
                       ▼
                 ActionQueue
                       │
                       ▼
                  Discord Bot
```

---

# 12. Market Grabber

Der Market Grabber ist ein separater Worker.

Aufgaben:

1. externe API abfragen
2. relevante Items bestimmen
3. aktuelle Preise vergleichen
4. Preisänderungen speichern
5. Fehler protokollieren
6. regelmäßig wiederholen

---

## 12.1 Speicherung

Die Anwendung muss nicht zwangsläufig jeden identischen Preis erneut speichern.

Das reduziert:

* Datenbankgröße
* Schreiboperationen
* Speicherverbrauch

---

## 12.2 Historienwachstum

Eine Markt-Historie wächst langfristig kontinuierlich.

Empfohlene Strategie:

```text
0–30 Tage
    ↓
Rohdaten

30–365 Tage
    ↓
aggregierte Daten

> 365 Tage
    ↓
Archiv / löschen
```

---

# 13. Market Alerts

Market Alerts ermöglichen automatisierte Preisüberwachung.

Ein Alert besitzt unter anderem:

```text
condition
target_price
enabled
armed
last_price
```

---

## 13.1 Armed-Prinzip

Beispiel:

```text
Preis steigt über Ziel
        │
        ▼
Alarm auslösen
        │
        ▼
armed = false
```

Erst wenn der Preis wieder unter die entsprechende Schwelle fällt:

```text
armed = true
```

Dadurch wird verhindert, dass bei jedem Worker-Lauf derselbe Discord-Alarm erneut gesendet wird.

---

# 14. Training

Das Training-System verwaltet Ausbildungen und deren Abschlüsse.

Grundstruktur:

```text
Training
   │
   ▼
TrainingCompletion
   │
   ├── User
   ├── Training
   ├── Jahr
   ├── Monat
   ├── Trainer
   └── Notiz
```

---

## 14.1 Monatliche Abschlüsse

Eine Datenbank-Constraint verhindert doppelte Einträge für:

```text
Benutzer
+
Training
+
Jahr
+
Monat
```

Dadurch wird die monatliche Pflichtausbildung auf Datenbankebene abgesichert.

---

# 15. Benutzerverwaltung

Das User-System verbindet:

```text
Discord User
     │
     ▼
UserProfile
     │
     ├── Comments
     ├── Warnings
     ├── GroupActions
     ├── Licenses
     ├── Awards
     └── TrainingCompletions
```

---

## 15.1 Kommentare

Kommentare können Benutzerinformationen ergänzen.

---

## 15.2 Verwarnungen

Warnings dienen der internen Verwaltung von Regelverstößen.

---

## 15.3 Gruppenaktionen

Gruppenaktionen bilden organisatorische Änderungen bzw. Aktionen gegenüber Benutzern ab.

---

# 16. Messaging

Das Messaging-System verwendet:

```text
MessagePreset
DMMessage
ActionQueue
```

Nachrichten können dadurch:

1. vorbereitet
2. gespeichert
3. über die Weboberfläche ausgelöst
4. in die ActionQueue geschrieben
5. vom Bot verarbeitet

werden.

---

## 16.1 Platzhalter

Das System kann dynamische Platzhalter unterstützen.

Beispiel:

```text
!USERNAME!
```

kann durch den Namen des Empfängers ersetzt werden.

Dadurch können allgemeine Nachrichtenvorlagen personalisiert werden.

---

## 16.2 Sicherheitsanforderung

Messaging-Endpunkte müssen streng geschützt werden.

Insbesondere gespeicherte Direktnachrichten dürfen nicht für normale Benutzer abrufbar sein.

---

# 17. Tickets

Das Ticketsystem speichert unter anderem:

```text
creator_id
creator_name
handler_id
description
status
created_at
closed_at
is_locked
channel_id
transcript
```

Das Webinterface kann damit Discord-Tickets administrativ darstellen und verwalten.

Das eigentliche Discord-Ticketverhalten kann im separaten Bot-System liegen.

---

# 18. Warehouse

Das Warehouse verwaltet Lagerbestände.

Grundstruktur:

```text
Warehouse
   │
   └── WarehouseItem
```

Das System berücksichtigt:

* Benutzer
* Artikel
* Mengen
* Gewicht
* Kapazität

Die konfigurierte Kapazität beträgt aktuell:

```text
20.000
```

---

## 18.1 Gewicht

Das Gesamtgewicht wird aus den Lagerpositionen berechnet.

Bei kleinen Datenmengen ist die aktuelle Berechnung ausreichend.

Bei größeren Datenmengen sollte die Summe direkt über SQL aggregiert werden.

---

# 19. Orders

Das Order-System verwaltet Aufträge und zugehörige Preis-/Kategorieinformationen.

Mögliche Bereiche sind unter anderem:

```text
vehicle
equipment
components
weapons
```

Administrative Aktionen können über die ActionQueue an den Discord-Bot weitergegeben werden.

---

# 20. Regelverwaltung

Das Regelwerk wird strukturiert verwaltet.

`RuleField` ermöglicht beispielsweise:

```text
title
content
inline
```

Damit können Regeln dynamisch zusammengestellt werden.

Das ist besonders für Discord-Embeds bzw. strukturierte Darstellungen sinnvoll.

---

# 21. Dokumente und Meetings

## 21.1 InternalDocument

Interne Dokumente enthalten:

```text
title
content
created_at
updated_at
```

Das System kann dadurch als internes Wiki-/Dokumentensystem genutzt werden.

---

## 21.2 TeamMeeting

Meetings enthalten beispielsweise:

```text
title
meeting_date
content
created_at
updated_at
```

Damit können Besprechungen geplant und dokumentiert werden.

---

# 22. Voice Credits

`VoiceCreditChannel` verwaltet Discord-Sprachkanäle für ein internes Creditsystem.

Beispielhafte Felder:

```text
guild_id
channel_id
channel_name
credit_rate
enabled
created_at
updated_at
```

Dadurch kann die Sprachaktivität eines Kanals in interne Credits übersetzt werden.

---

# 23. Browser-Games

Das Projekt enthält mehrere Browser-Spiele.

Aktuell vorhanden sind:

```text
/jetpack
/wasp
```

---

## 23.1 Jetpack

Das Jetpack-Spiel verwendet:

```text
JetpackHighscore
```

mit unter anderem:

```text
user_id
username
highscore
games_played
```

---

## 23.2 Wespenflug

Das Wespenflug-Spiel verwendet:

```text
WaspHighscore
```

und besitzt eine eigene Leaderboard-Funktion.

Das Spiel ist als Flappy-Bird-artiges Spiel mit dem STWG-Wespen-Thema umgesetzt.

---

## 23.3 Highscore-Sicherheit

Bei Browser-Games darf grundsätzlich nicht davon ausgegangen werden, dass der Client vertrauenswürdig ist.

Highscores sollten daher serverseitig validiert werden, soweit möglich.

---

# 24. Server- und Worker-Control

Das Webinterface besitzt Control-Funktionen für Services.

Mögliche Operationen:

```text
status
start
stop
restart
enable
disable
logs
```

Die Aktionen werden über `systemctl` ausgeführt.

---

## 24.1 Architektur

```text
Browser
   │
   ▼
Flask Control Blueprint
   │
   ▼
systemctl
   │
   ▼
systemd
   │
   ▼
Worker / Bot / Webserver
```

---

## 24.2 Sicherheit

Die Service-Namen müssen fest definiert sein.

Es darf niemals möglich sein, über einen HTTP-Parameter einen beliebigen Systembefehl einzuschleusen.

Empfohlen:

```python
ALLOWED_SERVICES = {
    "market-grabber": "stwg-market-grabber.service",
    "alerts": "stwg-market-alert-checker.service",
    "bot": "stwg-discord-bot.service",
}
```

und:

```python
ALLOWED_ACTIONS = {
    "status",
    "start",
    "stop",
    "restart",
}
```

---

# 25. Frontend

Das Frontend basiert auf:

* HTML
* Jinja2
* CSS
* JavaScript

Gemeinsame Elemente werden über Templates/Partials wiederverwendet.

---

## 25.1 Vorteile

* zentrale Navigation
* gemeinsame Layouts
* wiederverwendbare Komponenten
* fachlich getrennte Seiten

---

# 26. Konfiguration

Die Anwendung sollte zwischen drei Arten von Konfiguration unterscheiden.

## 26.1 Secrets

Beispiele:

```text
DB_PASSWORD
SECRET_KEY
DISCORD_CLIENT_SECRET
DISCORD_BOT_TOKEN
WEBHOOK_URL
```

Diese gehören nicht in Git.

---

## 26.2 Environment-Konfiguration

Beispiele:

```text
DB_HOST
DB_PORT
DB_NAME
DB_USER
DB_PASSWORD
```

---

## 26.3 Laufzeitkonfiguration

Beispiele:

```text
Market Settings
Training Settings
Application Settings
```

Diese können über `DataStorage` verwaltet werden.

---

# 27. Deployment

Eine sinnvolle Produktionsarchitektur ist:

```text
                    Internet
                       │
                       ▼
                    Nginx
                       │
                       ▼
                   Gunicorn
                       │
                       ▼
                    Flask
                       │
                       ▼
                    MariaDB
```

Separate Dienste:

```text
systemd
├── stwg-web.service
├── stwg-market-grabber.service
├── stwg-market-alert-checker.service
└── stwg-discord-bot.service
```

---

## 27.1 Vorteile der Trennung

Wenn beispielsweise der Market Grabber abstürzt:

```text
Market Grabber ❌
       │
       X
       │
Webserver      ✅
Discord Bot    ✅
```

Das gesamte System bleibt dadurch teilweise verfügbar.

---

# 28. Security

Security ist derzeit einer der wichtigsten Bereiche für weitere Arbeiten.

---

## 28.1 Kritisch: öffentlich gewordener Webhook

Wenn eine echte Discord-Webhook-URL im Repository vorhanden war oder ist, muss sie als kompromittiert betrachtet werden.

Maßnahmen:

1. Webhook löschen.
2. neuen Webhook erstellen.
3. alten Wert aus dem Code entfernen.
4. Secret über Environment laden.
5. Repository-Historie prüfen.

Das Entfernen aus der aktuellen Datei reicht nicht aus, wenn der Secret-Wert bereits in einem öffentlichen Git-Commit enthalten war.

---

## 28.2 Flask Secret Key

Ein häufiger Fehler ist:

```python
app.secret_key = "os.urandom(24)"
```

Das ist **kein** zufälliger Key.

Es ist lediglich ein String.

Richtig:

```python
app.secret_key = os.environ["SECRET_KEY"]
```

Beispiel:

```text
SECRET_KEY=<zufälliger-langer-wert>
```

Der Key darf nicht im Repository stehen.

---

## 28.3 Discord Secrets

Discord-Bot-Tokens, OAuth-Secrets und Webhooks müssen ausschließlich aus sicherer Konfiguration geladen werden.

Nicht:

```python
TOKEN = "..."
```

Sondern:

```python
TOKEN = os.environ["DISCORD_BOT_TOKEN"]
```

---

## 28.4 Session Security

Für Produktion sollte die Session zusätzlich sinnvoll konfiguriert werden.

Beispielsweise:

```python
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
```

Die genaue Einstellung muss zur OAuth-Architektur passen.

---

## 28.5 CSRF

Alle zustandsverändernden Webformulare sollten gegen CSRF geschützt sein.

Für JSON-APIs sollte ebenfalls geprüft werden, welche Authentifizierungs- und CSRF-Strategie verwendet wird.

---

## 28.6 System-Control

Serverbefehle sind besonders kritisch.

Die Webanwendung darf niemals freie Shell-Befehle ausführen.

---

# 29. Performance

## 29.1 Positive Aspekte

Bereits vorhandene gute Ansätze:

* SQLAlchemy
* gezielte Queries
* `selectinload()`
* separate Worker
* ActionQueue
* Vermeidung unnötiger Markt-Historieneinträge

---

## 29.2 Optimierungspotenzial

### Datenbank

* Indexe prüfen
* `DateTime` statt Strings
* SQL-Aggregationen nutzen
* Foreign Keys ergänzen

### Worker

* große Worker-Dateien aufteilen
* API-Aufrufe begrenzen
* Retry-Strategien definieren

### Frontend

* statische Dateien cachen
* unnötige Requests reduzieren
* große JavaScript-Dateien aufteilen

---

# 30. Logging

Produktive Services sollten getrennte Logs verwenden.

Beispiel:

```text
logs/
├── web.log
├── market-grabber.log
├── market-alerts.log
└── bot.log
```

Secrets dürfen niemals geloggt werden.

Verboten sind beispielsweise:

```text
DISCORD_BOT_TOKEN
OAuth Token
Webhook URL
DB Password
SECRET_KEY
```

---

# 31. Tests

Für die aktuelle Größe des Systems sollte eine automatisierte Teststruktur eingeführt werden.

Empfohlene Struktur:

```text
tests/
├── test_auth.py
├── test_permissions.py
├── test_training.py
├── test_market.py
├── test_market_alerts.py
├── test_warehouse.py
├── test_messaging.py
├── test_orders.py
├── test_games.py
└── test_action_queue.py
```

---

## 31.1 Besonders wichtige Tests

### Auth

* Login
* Logout
* OAuth Fehler
* Session

### Permissions

* normaler Benutzer
* Trainer
* Supporter
* Leitung
* Admin

### Training

* Training anlegen
* Abschluss erstellen
* doppelter Abschluss
* monatlicher Wechsel

### Market

* Preisänderung
* unveränderter Preis
* fehlendes Item
* API-Ausfall

### Alerts

* Alarm auslösen
* Alarm nicht doppelt auslösen
* Re-Arming

### Warehouse

* Bestand hinzufügen
* Bestand entfernen
* Kapazitätsgrenze

### Queue

* neue Aktion
* erfolgreiche Verarbeitung
* Fehler
* Retry
* endgültiger Fehler

---

# 32. Bekannte technische Schulden

## 32.1 Große Dateien

Einige Module sind inzwischen sehr groß.

Besonders betroffen sind:

```text
database/models.py
market_grabber.py
warehouse.py
training.py
```

Das erschwert langfristig Wartung und Tests.

---

## 32.2 Zeit als String

Mehrere Zeitwerte werden als formatierter String gespeichert.

Problem:

```text
25.08.2026 14:30
```

ist für Menschen gut lesbar, aber für Datenbankoperationen schlechter geeignet als:

```text
DATETIME
```

---

## 32.3 `default=current_time()`

Bei SQLAlchemy sollte bei dynamischen Defaults grundsätzlich die Funktion selbst übergeben werden:

```python
default=current_time
```

und nicht:

```python
default=current_time()
```

Andernfalls wird die Funktion bereits beim Import ausgeführt.

---

## 32.4 Fehlende Migrationen

`db.create_all()` ist für die initiale Entwicklung praktisch.

Für produktive Weiterentwicklung sollte ein Migration-System verwendet werden.

---

## 32.5 Fehlende Tests

Mit steigender Anzahl von Blueprints und Workern steigt das Risiko, dass Änderungen an einer Stelle andere Funktionen beschädigen.

---

## 32.6 Verteilte Permission-Logik

Berechtigungen werden teilweise über Session-Flags, Lizenzen und Decorators abgebildet.

Eine zentrale Permission-Abstraktion wäre langfristig sauberer.

---

# 33. Empfohlene Zielarchitektur

Eine mögliche zukünftige Struktur:

```text
stwg-web/
│
├── app/
│   ├── __init__.py
│   │
│   ├── auth/
│   ├── users/
│   ├── training/
│   ├── market/
│   ├── warehouse/
│   ├── messaging/
│   ├── orders/
│   ├── tickets/
│   ├── games/
│   └── admin/
│
├── database/
│   ├── models/
│   │   ├── users.py
│   │   ├── market.py
│   │   ├── training.py
│   │   ├── warehouse.py
│   │   ├── communication.py
│   │   └── games.py
│   │
│   └── migrations/
│
├── services/
│   ├── discord.py
│   ├── permissions.py
│   ├── queue.py
│   └── settings.py
│
├── workers/
│   ├── market/
│   │   ├── client.py
│   │   ├── service.py
│   │   ├── repository.py
│   │   └── worker.py
│   │
│   └── alerts/
│       ├── service.py
│       └── worker.py
│
├── templates/
├── static/
├── tests/
├── config/
│
├── main.py
├── requirements.txt
└── DOCUMENTATION.md
```

---

# 34. Roadmap

## Phase 1 – Sicherheit

* [ ] alle öffentlich gewordenen Secrets rotieren
* [ ] Webhooks aus dem Quellcode entfernen
* [ ] Flask `SECRET_KEY` korrigieren
* [ ] Discord Tokens prüfen
* [ ] Messaging-APIs prüfen
* [ ] System-Control absichern
* [ ] CSRF-Konzept überprüfen

---

## Phase 2 – Stabilität

* [ ] ActionQueue erweitern
* [ ] Retry-System
* [ ] Fehlerstatus
* [ ] Worker Heartbeats
* [ ] bessere Logs
* [ ] Datenbankmigrationen

---

## Phase 3 – Architektur

* [ ] Models auf mehrere Dateien verteilen
* [ ] große Worker zerlegen
* [ ] Service Layer einführen
* [ ] Permission Service
* [ ] Settings Service

---

## Phase 4 – Datenbank

* [ ] Zeitfelder auf `DateTime`
* [ ] Foreign Keys vervollständigen
* [ ] Indexe überprüfen
* [ ] JSON/TEXT-Felder überprüfen
* [ ] Historien-Retention

---

## Phase 5 – Qualität

* [ ] Unit Tests
* [ ] Integration Tests
* [ ] API Tests
* [ ] CI Pipeline
* [ ] Linting
* [ ] Type Hints
* [ ] automatische Deployments

---

# 35. Gesamtbewertung

| Bereich         | Bewertung |
| --------------- | --------: |
| Architektur     |      8/10 |
| Modularisierung |      8/10 |
| Funktionalität  |      9/10 |
| Datenmodell     |      7/10 |
| Security        |      4/10 |
| Wartbarkeit     |      6/10 |
| Worker          |      7/10 |
| API             |      7/10 |
| Frontend        |      8/10 |
| Dokumentation   |      3/10 |
| Tests           |      2/10 |

## Gesamteinschätzung

**ca. 7/10**

Die Bewertung bedeutet nicht, dass das Projekt schlecht ist.

Im Gegenteil:

Das Projekt ist für eine individuell entwickelte Community-Plattform bereits relativ umfangreich.

Die niedrige Security-/Testbewertung entsteht hauptsächlich dadurch, dass das Projekt stark gewachsen ist und inzwischen Anforderungen besitzt, die über ein klassisches Hobby-Flask-Projekt hinausgehen.

---

# 36. Fazit

STWG Web ist inzwischen eine vollständige Community-Management-Plattform.

Die wesentlichen Komponenten sind:

```text
                 Discord
                    │
                    ▼
             Discord OAuth
                    │
                    ▼
               Flask Web
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
       MariaDB            ActionQueue
          │                   │
          │                   ▼
          │              Discord Bot
          │
    ┌─────┼───────────────┐
    ▼     ▼               ▼
 Market Training       Warehouse
 Worker
    │
    ▼
Market Alerts
```

Besonders stark sind:

* die modulare Blueprint-Struktur
* die Integration mit Discord
* die ActionQueue
* die getrennten Worker
* das Markt-/Alert-System
* die umfangreiche Benutzerverwaltung
* das Training-System
* die Warehouse-Verwaltung
* die integrierten Spiele
* die Möglichkeit, Serverdienste über die Weboberfläche zu kontrollieren

Die wichtigsten nächsten Schritte sind nicht weitere Features, sondern die Stabilisierung der vorhandenen Architektur.

Priorität:

```text
1. Security
2. ActionQueue
3. Permissions
4. Datenbank
5. Worker-Struktur
6. Tests
7. Monitoring
8. weitere Features
```

---

# Hinweis zur Dokumentationsgrenze

Diese Dokumentation beschreibt das Repository:

```text
Lainupcomputer/stwg-web
```

Der vollständige Discord-Bot ist nicht Bestandteil dieses Repositorys.

Daher können Bot-interne:

* Commands
* Events
* Cogs
* Listener
* Discord-API-Implementierungen
* Bot-interne Worker

nur insoweit dokumentiert werden, wie sie über die Webanwendung, Datenbank oder `ActionQueue` sichtbar sind.

Für eine vollständige STWG-Systemdokumentation sollte zusätzlich das Discord-Bot-Repository analysiert werden.

---

## Technische Kurzbeschreibung

> **STWG Web ist eine Flask-basierte Community-Management-Plattform mit Discord-OAuth, SQLAlchemy/MariaDB, rollen- und lizenzbasierter Zugriffskontrolle, datenbankbasierter ActionQueue, separaten Hintergrund-Workern, Marktüberwachung, Preisalarmen, Benutzerverwaltung, Training, Messaging, Warehouse, Orders, Tickets, Dokumentenverwaltung, Server-Control und integrierten Browser-Games.**

Die Architektur ermöglicht eine lose Kopplung zwischen Webanwendung, Datenbank, Workern und Discord-Bot.

```text
Web
 │
 ├──────────────► Database
 │                    │
 │                    ├── Users
 │                    ├── Training
 │                    ├── Market
 │                    ├── Warehouse
 │                    └── Queue
 │
 └──────────────► ActionQueue
                      │
                      ▼
                  Discord Bot
```

Damit bildet das Projekt eine zentrale technische Plattform für die Verwaltung und Automatisierung des STWG-Systems.

