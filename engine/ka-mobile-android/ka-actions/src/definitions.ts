import { Plugin, PluginMethod, CapacitorPlugin } from '@capacitor/core';

export interface KAActionsPlugin extends Plugin {
  call(options: { number: string }): Promise<{ success: boolean }>;
  sms(options: { number: string; text?: string }): Promise<{ success: boolean }>;
  contacts(options: { query?: string }): Promise<{ contacts: Contact[] }>;
  diskSpace(): Promise<DiskSpaceInfo>;
  battery(): Promise<BatteryInfo>;
  openApp(options: { packageName: string }): Promise<{ success: boolean }>;
  listApps(options: { includeSystem?: boolean }): Promise<{ apps: AppInfo[] }>;
  deviceInfo(): Promise<DeviceInfo>;
  wifiInfo(): Promise<WifiInfo>;
  /**
   * COMPRESSION ZIP natif (java.util.zip — zéro dépendance open-source).
   * Background-compatible : peut être lancée depuis WorkManager.
   */
  compress(options: { sourcePath: string; targetPath: string }): Promise<{
    success: boolean; inputBytes: number; outputBytes: number; ratio: number;
    engine: string;
  }>;
}

export interface Contact {
  name: string;
  number: string;
}

export interface DiskSpaceInfo {
  total: number;
  free: number;
  used: number;
  totalGB: string;
  freeGB: string;
  usedGB: string;
  percentUsed: string;
}

export interface BatteryInfo {
  level: number;
  status: 'charging' | 'discharging' | 'full' | 'not_charging' | 'unknown';
  health: 'good' | 'overheat' | 'dead' | 'over_voltage' | 'failure' | 'unknown';
  plugged: 'ac' | 'usb' | 'wireless' | 'none';
  isCharging: boolean;
}

export interface AppInfo {
  packageName: string;
  name: string;
  icon: number;
  isSystem: boolean;
  enabled: boolean;
}

export interface DeviceInfo {
  model: string;
  manufacturer: string;
  brand: string;
  device: string;
  product: string;
  androidVersion: string;
  sdkInt: string;
  fingerprint: string;
  serial: string;
}

export interface WifiInfo {
  ssid: string;
  bssid: string;
  rssi: number;
  linkSpeed: number;
  frequency: number;
  ipAddress: string;
  macAddress: string;
  isConnected: boolean;
}

declare global {
  interface Window {
    KAActions?: KAActionsPlugin;
  }
}