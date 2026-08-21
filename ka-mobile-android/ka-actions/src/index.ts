import { registerPlugin, WebPlugin } from '@capacitor/core';
import type { KAActionsPlugin, Contact, DiskSpaceInfo, BatteryInfo, AppInfo, DeviceInfo, WifiInfo } from './definitions';

class KAActionsWeb extends WebPlugin implements KAActionsPlugin {
  async call(options: { number: string }): Promise<{ success: boolean }> {
    console.warn('[KAActions] call() non disponible sur web');
    return { success: false };
  }
  async sms(options: { number: string; text?: string }): Promise<{ success: boolean }> {
    console.warn('[KAActions] sms() non disponible sur web');
    return { success: false };
  }
  async contacts(options: { query?: string }): Promise<{ contacts: Contact[] }> {
    console.warn('[KAActions] contacts() non disponible sur web');
    return { contacts: [] };
  }
  async diskSpace(): Promise<DiskSpaceInfo> {
    if ('storage' in navigator && 'estimate' in navigator.storage) {
      const estimate = await navigator.storage.estimate();
      return {
        total: estimate.quota || 0,
        free: (estimate.quota || 0) - (estimate.usage || 0),
        used: estimate.usage || 0,
        totalGB: ((estimate.quota || 0) / 1e9).toFixed(2),
        freeGB: (((estimate.quota || 0) - (estimate.usage || 0)) / 1e9).toFixed(2),
        usedGB: ((estimate.usage || 0) / 1e9).toFixed(2),
        percentUsed: estimate.quota ? ((estimate.usage || 0) / estimate.quota * 100).toFixed(1) : '0'
      };
    }
    return { total: 0, free: 0, used: 0, totalGB: '0', freeGB: '0', usedGB: '0', percentUsed: '0' };
  }
  async battery(): Promise<BatteryInfo> {
    if ('getBattery' in navigator) {
      const bat = await (navigator as any).getBattery();
      return {
        level: Math.round(bat.level * 100),
        status: bat.charging ? 'charging' : 'discharging',
        health: 'good',
        plugged: bat.charging ? 'ac' : 'none',
        isCharging: bat.charging
      };
    }
    return { level: -1, status: 'unknown', health: 'unknown', plugged: 'none', isCharging: false };
  }
  async openApp(options: { packageName: string }): Promise<{ success: boolean }> {
    console.warn('[KAActions] openApp() non disponible sur web');
    return { success: false };
  }
  async listApps(options: { includeSystem?: boolean }): Promise<{ apps: AppInfo[] }> {
    return { apps: [] };
  }
  async deviceInfo(): Promise<DeviceInfo> {
    return {
      model: navigator.userAgent,
      manufacturer: 'Web',
      brand: 'Browser',
      device: 'Web',
      product: 'Web',
      androidVersion: 'N/A',
      sdkInt: '0',
      fingerprint: 'web',
      serial: 'web'
    };
  }
  async wifiInfo(): Promise<WifiInfo> {
    return { ssid: 'N/A', bssid: 'N/A', rssi: 0, linkSpeed: 0, frequency: 0, ipAddress: 'N/A', macAddress: 'N/A', isConnected: navigator.onLine };
  }
}

const KAActions = registerPlugin<KAActionsPlugin>('KAActions', {
  web: () => new KAActionsWeb()
});

export { KAActions };
export type { Contact, DiskSpaceInfo, BatteryInfo, AppInfo, DeviceInfo, WifiInfo } from './definitions';