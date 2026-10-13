# AirDrop for Windows

**English** | [Slovenčina](README_SK.md)

Send files between a Windows PC and an iPhone over your home Wi-Fi. Nothing needs to be installed on the iPhone; Safari is enough.

## Getting started

1. Double-click `start.bat` (or run `python airdrop.py`). You need Python 3.8 or newer; nothing else has to be installed.
2. When Windows asks about the firewall on the first run, allow access for **private networks**.
3. A browser window with a QR code opens on the PC. Scan it with the iPhone camera.
4. Recommended: in Safari on the iPhone, tap **Share → Add to Home Screen**. You can then open AirDrop like an app, without scanning.

### Optional: portable version (no Python needed)

If you don't have Python installed, download **[AirDrop-Windows.zip](https://github.com/chose-sm/AirDrop_windows/releases/latest/download/AirDrop-Windows.zip)**. The link always points to the latest version (see [Releases](https://github.com/chose-sm/AirDrop_windows/releases) for the changelog). It includes the official portable Python from python.org (digitally signed by the Python Software Foundation), so nothing needs to be installed. Extract the ZIP anywhere and double-click `start.bat`. The rest of the steps above stay the same. The firewall prompt will mention `python.exe`; allow it for private networks.

To build the package yourself: `powershell -ExecutionPolicy Bypass -File build_release.ps1 -Version 1.0.0`. The ZIP is created in the `dist` folder.

## Usage

| Direction | How |
|---|---|
| PC → iPhone | Drag files into the window on the PC (or press Ctrl+V). On the iPhone, tap **Download** to save a file to the Files app. For photos and videos, tap **Open**, press and hold, then choose **Add to Photos**. |
| iPhone → PC | Tap **Send to PC** and pick photos or files. |

Files are stored in `F:\AirDrop\`:
- `Prijate` contains files received from the iPhone,
- `Odoslane` contains files ready for the iPhone.

## Settings (environment variables)

- `AIRDROP_PORT` sets the port, `8765` by default.
- `AIRDROP_DIR` sets the folder for files, `F:\AirDrop` by default.
- Running with `--no-browser` does not open the browser.

## Security

Access is protected by a random key contained in the QR code and stored in `F:\AirDrop\.token`. If you delete it, a new key is generated and the old link stops working. Transfers are unencrypted HTTP within your local network, so use it only at home or on a trusted Wi-Fi.

## Troubleshooting

- **The iPhone can't connect:** both devices must be on the same Wi-Fi, and the network in Windows must be set to *Private*. You can also add the firewall rule manually (PowerShell as administrator):
  ```
  New-NetFirewallRule -DisplayName "AirDrop for Windows" -Direction Inbound -Protocol TCP -LocalPort 8765 -Action Allow -Profile Private
  ```
- **Multiple network addresses (VPN, Hyper-V):** pick the correct address below the QR code.
- **Photos arrive as .HEIC:** on the iPhone, set *Settings → Camera → Formats → Most Compatible*.

## Language

The interface is available in Slovak and English. Switch it with the selector next to the AirDrop title. Each device (PC and iPhone) remembers its own choice; on first launch the language follows the device setting.
