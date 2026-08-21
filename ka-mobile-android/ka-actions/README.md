# KA Actions Plugin

Plugin Capacitor pour actions natives Android depuis KA Mobile.

## Installation

```bash
cd ka-mobile-android
npm install file:./ka-actions
npx cap sync android
```

## Actions disponibles

| Méthode | Description | Permissions |
|---------|-------------|-------------|
| `call({number})` | Appeler un numéro | `CALL_PHONE` |
| `sms({number, text?})` | Envoyer SMS | `SEND_SMS` |
| `contacts({query?})` | Rechercher contacts | `READ_CONTACTS` |
| `diskSpace()` | Espace disque | - |
| `battery()` | Info batterie | `BATTERY_STATS` |
| `openApp({packageName})` | Lancer une app | `QUERY_ALL_PACKAGES` |
| `listApps({includeSystem?})` | Lister apps installées | `QUERY_ALL_PACKAGES` |
| `deviceInfo()` | Infos device | - |
| `wifiInfo()` | Infos WiFi | `ACCESS_WIFI_STATE` |

## Usage

```typescript
import { KAActions } from '@vitalka/ka-actions';

// Appel
await KAActions.call({ number: '+33612345678' });

// SMS
await KAActions.sms({ number: '+33612345678', text: 'Hello from KA!' });

// Contacts
const { contacts } = await KAActions.contacts({ query: 'Sophie' });

// Disque
const disk = await KAActions.diskSpace();
console.log(`Libre: ${disk.freeGB} GB / ${disk.totalGB} GB`);

// Batterie
const bat = await KAActions.battery();
console.log(`Niveau: ${bat.level}% (${bat.status})`);

// Apps
const { apps } = await KAActions.listApps({ includeSystem: false });
const kaApp = apps.find(a => a.packageName.includes('vitalka'));
if (kaApp) await KAActions.openApp({ packageName: kaApp.packageName });

// Device
const info = await KAActions.deviceInfo();

// WiFi
const wifi = await KAActions.wifiInfo();
```

## Permissions Android (auto-gérées)

Le plugin demande les permissions à la volée via `requestPermissions()`.

## Fallback Web

Sur navigateur (PWA), les actions natives retournent des valeurs par défaut ou utilisent les APIs Web disponibles (`navigator.storage`, `navigator.getBattery`).