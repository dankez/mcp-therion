# Design Spec: Therion MCP Server (Anonymný Mentor)
**Date:** 2026-04-13
**Status:** Approved

## 1. Úvod
Cieľom je vytvoriť MCP (Model Context Protocol) server pre program Therion, ktorý umožní AI asistentovi radiť pri spracovaní jaskynných dát bez toho, aby mal prístup k citlivým geografickým súradniciam a objavom.

## 2. Architektúra
- **Typ:** MCP Server (Python)
- **Knižnica:** `mcp` (Python SDK)
- **Lokalizácia:** `/home/dankez/mcp-therion/`

## 3. Komponenty a Nástroje (Tools)

### 3.1. `list_therion_projects`
- **Vstup:** Žiadny.
- **Výstup:** Zoznam adresárov v `/home/dankez/Downloads/dropbox-spolu/`, ktoré obsahujú `.th` súbory.

### 3.2. `read_anonymized_th(file_path)`
- **Vstup:** Relatívna cesta k `.th` alebo `.th2` súboru.
- **Logika anonymizácie:**
    - **Regex 1:** Vymaže riadky začínajúce na `cs`, `fix`, `explo`, `date`, `team`, `author`.
    - **Regex 2:** V riadkoch `data normal` nahradí všetky číselné hodnoty (okrem názvov staníc) nulami.
    - **Regex 3:** V `.th2` súboroch nahradí všetky numerické súradnice v `line` a `point` definíciách logickými placeholderami (napr. `10.0 10.0`).
- **Výstup:** Textový obsah súboru zbavený citlivých dát.

### 3.3. `compile_therion(file_path)`
- **Vstup:** Cesta k hlavnému `.th` súboru.
- **Logika:** Spustí `therion <file_path>` v izolovanom procese.
- **Výstup:** Ak prebehne úspešne, vráti „Kompilácia prebehla v poriadku“. Ak zlyhá, vráti len chybové hlásenia z `stderr`.

### 3.4. `search_studnica(query)`
- **Vstup:** Kľúčové slovo alebo téma.
- **Výstup:** Relevantné záznamy z `studnica.json` (vedomostná báza používateľa).

### 3.5. `add_to_studnica(topic, trick)`
- **Vstup:** Názov témy a popis postupu/triku.
- **Logika:** Uloží záznam do `studnica.json`.

### 3.6. `generate_th2_skeleton(description)`
- **Vstup:** Slovný popis štruktúry z náčrtu (JPG).
- **Výstup:** Vygenerovaný kód `.th2` s definíciami stien a bodov v mriežke, pripravený na manuálne dopracovanie v XTherione.

## 4. Bezpečnosť a Súkromie
- AI **nikdy** neuvidí reálne súradnice ani GPS polohu.
- Všetky operácie s originálnymi dátami sú **len na čítanie**.
- Žiadne dáta nie sú nahrávané do cloudu, spracovanie prebieha lokálne na MCP serveri.

## 5. Ďalšie kroky (Implementation Plan)
1. Nastavenie Python prostredia (venv).
2. Implementácia MCP servera s anonymizačným filtrom.
3. Testovanie na reálnych dátach z Jánskej doliny.
4. Spustenie a integrácia do Gemini CLI.
