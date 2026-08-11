package com.vitalka.ka.actions;

import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.JSObject;
import com.getcapacitor.PermissionCallback;

import android.Manifest;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import androidx.core.content.ContextCompat;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@CapacitorPlugin(name = "KAActions")
public class KAActionsPlugin extends Plugin {

    // Permissions
    private static final String PERM_CALL = Manifest.permission.CALL_PHONE;
    private static final String PERM_SMS = Manifest.permission.SEND_SMS;
    private static final String PERM_CONTACTS = Manifest.permission.READ_CONTACTS;
    private static final String PERM_WIFI = Manifest.permission.ACCESS_WIFI_STATE;

    // Helpers permissions
    private boolean hasPerm(String perm) {
        return ContextCompat.checkSelfPermission(getContext(), perm) == PackageManager.PERMISSION_GRANTED;
    }

    private void requestPerm(PluginCall call, String perm, Runnable onGranted) {
        if (hasPerm(perm)) {
            onGranted.run();
        } else {
            // Capacitor v7: requestPermissions prend un callback direct
            requestPermissions(new String[]{perm}, new PermissionCallback() {
                @Override
                public void onPermissionResult(String permission, boolean granted) {
                    if (granted) {
                        onGranted.run();
                    } else {
                        call.reject("Permission refusée : " + perm);
                    }
                }
            });
        }
    }

    // Helper pour créer JSObject depuis Map<String, Object>
    private JSObject toJSObject(Map<String, Object> map) {
        JSObject obj = new JSObject();
        for (Map.Entry<String, Object> entry : map.entrySet()) {
            Object value = entry.getValue();
            if (value instanceof String) {
                obj.put(entry.getKey(), (String) value);
            } else if (value instanceof Integer) {
                obj.put(entry.getKey(), (Integer) value);
            } else if (value instanceof Long) {
                obj.put(entry.getKey(), (Long) value);
            } else if (value instanceof Double) {
                obj.put(entry.getKey(), (Double) value);
            } else if (value instanceof Boolean) {
                obj.put(entry.getKey(), (Boolean) value);
            } else if (value instanceof Map) {
                @SuppressWarnings("unchecked")
                Map<String, Object> subMap = (Map<String, Object>) value;
                obj.put(entry.getKey(), toJSObject(subMap));
            } else if (value instanceof List) {
                obj.put(entry.getKey(), toJSArray((List<?>) value));
            } else if (value != null) {
                obj.put(entry.getKey(), value.toString());
            }
        }
        return obj;
    }

    private JSONArray toJSArray(List<?> list) {
        JSONArray arr = new JSONArray();
        for (Object item : list) {
            if (item instanceof Map) {
                @SuppressWarnings("unchecked")
                Map<String, Object> subMap = (Map<String, Object>) item;
                arr.put(toJSObject(subMap));
            } else if (item instanceof String) {
                arr.put((String) item);
            } else if (item instanceof Number) {
                arr.put((Number) item);
            } else if (item instanceof Boolean) {
                arr.put((Boolean) item);
            } else if (item != null) {
                arr.put(item.toString());
            }
        }
        return arr;
    }

    // ═══════════════════════════════════════════════════════════════
    // ACTIONS
    // ══════════════════════════════════════════════════════════════

    @PluginMethod
    public void call(PluginCall call) {
        String number = call.getString("number");
        if (number == null || number.isEmpty()) {
            call.reject("Numéro requis");
            return;
        }
        requestPerm(call, PERM_CALL, () -> {
            try {
                android.content.Intent intent = new android.content.Intent(android.content.Intent.ACTION_CALL);
                intent.setData(android.net.Uri.parse("tel:" + number));
                intent.addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK);
                getContext().startActivity(intent);
                JSObject result = new JSObject();
                result.put("success", true);
                call.resolve(result);
            } catch (Exception e) {
                call.reject("Erreur appel: " + e.getMessage());
            }
        });
    }

    @PluginMethod
    public void sms(PluginCall call) {
        String number = call.getString("number");
        String text = call.getString("text", "");
        if (number == null || number.isEmpty()) {
            call.reject("Numéro requis");
            return;
        }
        requestPerm(call, PERM_SMS, () -> {
            try {
                android.content.Intent intent = new android.content.Intent(android.content.Intent.ACTION_SENDTO);
                intent.setData(android.net.Uri.parse("smsto:" + number));
                intent.putExtra("sms_body", text);
                intent.addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK);
                getContext().startActivity(intent);
                JSObject result = new JSObject();
                result.put("success", true);
                call.resolve(result);
            } catch (Exception e) {
                call.reject("Erreur SMS: " + e.getMessage());
            }
        });
    }

    @PluginMethod
    public void contacts(PluginCall call) {
        String query = call.getString("query", "");
        requestPerm(call, PERM_CONTACTS, () -> {
            try {
                android.database.Cursor cursor = getContext().getContentResolver().query(
                    android.provider.ContactsContract.CommonDataKinds.Phone.CONTENT_URI,
                    new String[]{
                        android.provider.ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME,
                        android.provider.ContactsContract.CommonDataKinds.Phone.NUMBER
                    },
                    query.isEmpty() ? null : android.provider.ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME + " LIKE ?",
                    query.isEmpty() ? null : new String[]{"%" + query + "%"},
                    android.provider.ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME + " ASC"
                );

                List<Map<String, String>> results = new ArrayList<>();
                if (cursor != null) {
                    while (cursor.moveToNext()) {
                        Map<String, String> c = new HashMap<>();
                        c.put("name", cursor.getString(0));
                        c.put("number", cursor.getString(1));
                        results.add(c);
                    }
                    cursor.close();
                }
                JSObject result = new JSObject();
                result.put("contacts", toJSArray(results));
                call.resolve(result);
            } catch (Exception e) {
                call.reject("Erreur contacts: " + e.getMessage());
            }
        });
    }

    @PluginMethod
    public void diskSpace(PluginCall call) {
        try {
            java.io.File path = android.os.Environment.getDataDirectory();
            android.os.StatFs stat = new android.os.StatFs(path.getPath());
            long blockSize = stat.getBlockSizeLong();
            long totalBlocks = stat.getBlockCountLong();
            long freeBlocks = stat.getAvailableBlocksLong();

            long total = totalBlocks * blockSize;
            long free = freeBlocks * blockSize;
            long used = total - free;

            Map<String, Object> result = new HashMap<>();
            result.put("total", total);
            result.put("free", free);
            result.put("used", used);
            result.put("totalGB", String.format("%.2f", total / (1024.0 * 1024.0 * 1024.0)));
            result.put("freeGB", String.format("%.2f", free / (1024.0 * 1024.0 * 1024.0)));
            result.put("usedGB", String.format("%.2f", used / (1024.0 * 1024.0 * 1024.0)));
            result.put("percentUsed", String.format("%.1f", (used * 100.0) / total));

            call.resolve(toJSObject(result));
        } catch (Exception e) {
            call.reject("Erreur diskSpace: " + e.getMessage());
        }
    }

    @PluginMethod
    public void battery(PluginCall call) {
        try {
            android.content.IntentFilter filter = new android.content.IntentFilter(android.content.Intent.ACTION_BATTERY_CHANGED);
            android.content.Intent batteryStatus = getContext().registerReceiver(null, filter);

            int level = -1, scale = -1, status = -1, health = -1, plugged = -1;
            if (batteryStatus != null) {
                level = batteryStatus.getIntExtra(android.os.BatteryManager.EXTRA_LEVEL, -1);
                scale = batteryStatus.getIntExtra(android.os.BatteryManager.EXTRA_SCALE, -1);
                status = batteryStatus.getIntExtra(android.os.BatteryManager.EXTRA_STATUS, -1);
                health = batteryStatus.getIntExtra(android.os.BatteryManager.EXTRA_HEALTH, -1);
                plugged = batteryStatus.getIntExtra(android.os.BatteryManager.EXTRA_PLUGGED, -1);
            }

            int percent = (level >= 0 && scale > 0) ? (level * 100 / scale) : -1;

            String statusStr = "unknown";
            if (status == android.os.BatteryManager.BATTERY_STATUS_CHARGING) statusStr = "charging";
            else if (status == android.os.BatteryManager.BATTERY_STATUS_DISCHARGING) statusStr = "discharging";
            else if (status == android.os.BatteryManager.BATTERY_STATUS_FULL) statusStr = "full";
            else if (status == android.os.BatteryManager.BATTERY_STATUS_NOT_CHARGING) statusStr = "not_charging";

            String healthStr = "unknown";
            if (health == android.os.BatteryManager.BATTERY_HEALTH_GOOD) healthStr = "good";
            else if (health == android.os.BatteryManager.BATTERY_HEALTH_OVERHEAT) healthStr = "overheat";
            else if (health == android.os.BatteryManager.BATTERY_HEALTH_DEAD) healthStr = "dead";
            else if (health == android.os.BatteryManager.BATTERY_HEALTH_OVER_VOLTAGE) healthStr = "over_voltage";
            else if (health == android.os.BatteryManager.BATTERY_HEALTH_UNSPECIFIED_FAILURE) healthStr = "failure";

            String pluggedStr = "none";
            if (plugged == android.os.BatteryManager.BATTERY_PLUGGED_AC) pluggedStr = "ac";
            else if (plugged == android.os.BatteryManager.BATTERY_PLUGGED_USB) pluggedStr = "usb";
            else if (plugged == android.os.BatteryManager.BATTERY_PLUGGED_WIRELESS) pluggedStr = "wireless";

            Map<String, Object> result = new HashMap<>();
            result.put("level", percent);
            result.put("status", statusStr);
            result.put("health", healthStr);
            result.put("plugged", pluggedStr);
            result.put("isCharging", statusStr.equals("charging") || statusStr.equals("full"));

            call.resolve(toJSObject(result));
        } catch (Exception e) {
            call.reject("Erreur battery: " + e.getMessage());
        }
    }

    @PluginMethod
    public void openApp(PluginCall call) {
        String packageName = call.getString("packageName");
        if (packageName == null || packageName.isEmpty()) {
            call.reject("packageName requis");
            return;
        }
        try {
            android.content.Intent intent = getContext().getPackageManager().getLaunchIntentForPackage(packageName);
            if (intent != null) {
                intent.addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK);
                getContext().startActivity(intent);
                JSObject result = new JSObject();
                result.put("success", true);
                call.resolve(result);
            } else {
                call.reject("App non trouvée: " + packageName);
            }
        } catch (Exception e) {
            call.reject("Erreur openApp: " + e.getMessage());
        }
    }

    @PluginMethod
    public void listApps(PluginCall call) {
        boolean includeSystem = call.getBoolean("includeSystem", false);
        try {
            android.content.pm.PackageManager pm = getContext().getPackageManager();
            List<android.content.pm.ApplicationInfo> apps = pm.getInstalledApplications(android.content.pm.PackageManager.GET_META_DATA);

            List<Map<String, Object>> results = new ArrayList<>();
            for (android.content.pm.ApplicationInfo app : apps) {
                boolean isSystem = (app.flags & android.content.pm.ApplicationInfo.FLAG_SYSTEM) != 0;
                if (!includeSystem && isSystem) continue;

                Map<String, Object> a = new HashMap<>();
                a.put("packageName", app.packageName);
                a.put("name", pm.getApplicationLabel(app).toString());
                a.put("icon", app.icon);
                a.put("isSystem", isSystem);
                a.put("enabled", app.enabled);
                results.add(a);
            }
            JSObject result = new JSObject();
            result.put("apps", toJSArray(results));
            call.resolve(result);
        } catch (Exception e) {
            call.reject("Erreur listApps: " + e.getMessage());
        }
    }

    @PluginMethod
    public void deviceInfo(PluginCall call) {
        try {
            Map<String, Object> result = new HashMap<>();
            result.put("model", android.os.Build.MODEL);
            result.put("manufacturer", android.os.Build.MANUFACTURER);
            result.put("brand", android.os.Build.BRAND);
            result.put("device", android.os.Build.DEVICE);
            result.put("product", android.os.Build.PRODUCT);
            result.put("androidVersion", android.os.Build.VERSION.RELEASE);
            result.put("sdkInt", String.valueOf(android.os.Build.VERSION.SDK_INT));
            result.put("fingerprint", android.os.Build.FINGERPRINT);
            result.put("serial", android.os.Build.SERIAL);
            call.resolve(toJSObject(result));
        } catch (Exception e) {
            call.reject("Erreur deviceInfo: " + e.getMessage());
        }
    }

    @PluginMethod
    public void wifiInfo(PluginCall call) {
        requestPerm(call, PERM_WIFI, () -> {
            try {
                android.net.wifi.WifiManager wifi = (android.net.wifi.WifiManager) getContext().getSystemService(android.content.Context.WIFI_SERVICE);
                android.net.wifi.WifiInfo info = wifi.getConnectionInfo();

                Map<String, Object> result = new HashMap<>();
                result.put("ssid", info.getSSID().replace("\"", ""));
                result.put("bssid", info.getBSSID());
                result.put("rssi", info.getRssi());
                result.put("linkSpeed", info.getLinkSpeed());
                result.put("frequency", info.getFrequency());
                result.put("ipAddress", intToIp(info.getIpAddress()));
                result.put("macAddress", info.getMacAddress());
                result.put("isConnected", info.getSupplicantState() == android.net.wifi.SupplicantState.COMPLETED);

                call.resolve(toJSObject(result));
            } catch (Exception e) {
                call.reject("Erreur wifiInfo: " + e.getMessage());
            }
        });
    }

    private String intToIp(int i) {
        return ((i >> 0) & 0xFF) + "." + ((i >> 8) & 0xFF) + "." + ((i >> 16) & 0xFF) + "." + ((i >> 24) & 0xFF);
    }

    /**
     * COMPRESSION (agentique, background-compatible) — ZIP natif java.util.zip,
     * AUCUNE dépendance open-source : le SDK Android embarque tout.
     * compress({sourcePath, targetPath}) → {success, inputBytes, outputBytes, ratio}
     */
    @PluginMethod
    public void compress(PluginCall call) {
        String source = call.getString("sourcePath", "");
        String target = call.getString("targetPath", "");
        if (source.isEmpty() || target.isEmpty()) {
            call.reject("sourcePath et targetPath requis");
            return;
        }
        try {
            java.io.File src = new java.io.File(source);
            java.io.File dst = new java.io.File(target);
            if (!src.exists()) {
                call.reject("source introuvable: " + source);
                return;
            }
            long inputBytes = src.isDirectory() ? dirSize(src) : src.length();
            try (java.util.zip.ZipOutputStream zos =
                         new java.util.zip.ZipOutputStream(new java.io.FileOutputStream(dst))) {
                if (src.isDirectory()) {
                    zipDir(src, src, zos);
                } else {
                    zipEntry(src, src.getParentFile(), zos);
                }
            }
            long outputBytes = dst.length();
            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            result.put("inputBytes", inputBytes);
            result.put("outputBytes", outputBytes);
            result.put("ratio", inputBytes > 0 ? (double) outputBytes / inputBytes : 0.0);
            result.put("engine", "java.util.zip — ZIP natif, zéro dépendance");
            call.resolve(toJSObject(result));
        } catch (Exception e) {
            call.reject("Erreur compress: " + e.getMessage());
        }
    }

    private long dirSize(java.io.File dir) {
        long total = 0;
        java.io.File[] files = dir.listFiles();
        if (files == null) return 0;
        for (java.io.File f : files) {
            total += f.isDirectory() ? dirSize(f) : f.length();
        }
        return total;
    }

    private void zipDir(java.io.File dir, java.io.File base, java.util.zip.ZipOutputStream zos)
            throws java.io.IOException {
        java.io.File[] files = dir.listFiles();
        if (files == null) return;
        for (java.io.File f : files) {
            if (f.isDirectory()) {
                zipDir(f, base, zos);
            } else {
                zipEntry(f, base, zos);
            }
        }
    }

    private void zipEntry(java.io.File f, java.io.File base, java.util.zip.ZipOutputStream zos)
            throws java.io.IOException {
        String rel = base.toURI().relativize(f.toURI()).getPath();
        byte[] buffer = new byte[8192];
        try (java.io.FileInputStream fis = new java.io.FileInputStream(f)) {
            zos.putNextEntry(new java.util.zip.ZipEntry(rel));
            int len;
            while ((len = fis.read(buffer)) > 0) {
                zos.write(buffer, 0, len);
            }
            zos.closeEntry();
        }
    }
}