# AirDrop pre Windows

[English](README.md) | **Slovenčina**

Posielanie súborov medzi Windows PC a iPhonom cez domácu Wi-Fi. Na iPhone sa nič neinštaluje, stačí Safari.

## Spustenie

1. Dvojklik na `start.bat` (alebo `python airdrop.py`). Potrebuješ Python 3.8 alebo novší, nič ďalšie netreba inštalovať.
2. Keď sa Windows pri prvom spustení opýta na bránu firewall, povoľ prístup pre **súkromné siete**.
3. V prehliadači na PC sa otvorí okno s QR kódom. Naskenuj ho fotoaparátom iPhonu.
4. Odporúčam: na iPhone v Safari ťukni na **Zdieľať → Pridať na plochu**. Potom AirDrop otvoríš ako aplikáciu, bez skenovania.

## Použitie

| Smer | Ako |
|---|---|
| PC → iPhone | Pretiahni súbory do okna na PC (alebo Ctrl+V). Na iPhone ich potom stiahneš cez **Stiahnuť** (uloží sa do Súborov), fotky a videá cez **Otvoriť** a podržanie prsta → **Pridať do Fotiek**. |
| iPhone → PC | Ťukni na **Poslať do PC** a vyber fotky alebo súbory. |

Súbory sú v `F:\AirDrop\`:
- `Prijate` obsahuje súbory z iPhonu,
- `Odoslane` obsahuje súbory pripravené pre iPhone.

## Nastavenia (premenné prostredia)

- `AIRDROP_PORT` je port, predvolene `8765`.
- `AIRDROP_DIR` je priečinok so súbormi, predvolene `F:\AirDrop`.
- Spustenie s `--no-browser` neotvorí prehliadač.

## Bezpečnosť

Prístup chráni náhodný kľúč v QR kóde, uložený v `F:\AirDrop\.token`. Keď ho zmažeš, vygeneruje sa nový a starý odkaz prestane fungovať. Prenos ide nešifrovane cez HTTP v lokálnej sieti, preto ho používaj len doma alebo na dôveryhodnej Wi-Fi.

## Riešenie problémov

- **iPhone sa nepripojí:** obe zariadenia musia byť na rovnakej Wi-Fi a sieť vo Windows musí byť nastavená ako *Súkromná*. Pravidlo firewallu môžeš pridať aj ručne (PowerShell ako správca):
  ```
  New-NetFirewallRule -DisplayName "AirDrop pre Windows" -Direction Inbound -Protocol TCP -LocalPort 8765 -Action Allow -Profile Private
  ```
- **Viac sieťových adries (VPN, Hyper-V):** pod QR kódom vyber správnu adresu.
- **Fotky prídu ako .HEIC:** v iPhone nastav *Nastavenia → Fotoaparát → Formáty → Najkompatibilnejšie*.

## Jazyk

Rozhranie je v slovenčine a angličtine. Prepneš ho prepínačom vedľa nápisu AirDrop. Každé zariadenie (PC aj iPhone) si pamätá svoju voľbu a pri prvom spustení sa jazyk zvolí podľa nastavenia zariadenia.
