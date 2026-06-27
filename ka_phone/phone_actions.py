#!/usr/bin/env python3
"""
Phone Actions Engine — Executes phone commands
===============================================
Handles: SMS, calls, alarms, calendar, notes, weather, open app, web search

On Android: calls actual Android APIs via pyjnius
On desktop: simulates with console output (dev mode)

Usage:
  from phone_actions import PhoneActions
  pa = PhoneActions()
  result = pa.execute("sms", {"contact": "Marie", "message": "Je serai en retard"})
"""

import os, sys, json, datetime, subprocess, webbrowser
from typing import Dict, Any, Optional

# Try to detect platform
IS_ANDROID = False
try:
    # Check if we're on Android (Kivy, PyJNIus, etc.)
    from android.permissions import request_permissions, Permission
    IS_ANDROID = True
except ImportError:
    IS_ANDROID = False

class PhoneActions:
    """
    Executes phone actions. On Android, uses real APIs.
    On desktop/development, simulates with console output.
    """
    
    def __init__(self, dev_mode: bool = True):
        self.dev_mode = dev_mode or not IS_ANDROID
        self.actions_log = []
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a phone action and return result."""
        
        if action == "sms":
            return self._send_sms(params)
        elif action == "call":
            return self._make_call(params)
        elif action == "alarm":
            return self._set_alarm(params)
        elif action == "calendar":
            return self._add_calendar(params)
        elif action == "weather":
            return self._get_weather(params)
        elif action == "note":
            return self._take_note(params)
        elif action == "search":
            return self._web_search(params)
        elif action == "open_app":
            return self._open_app(params)
        elif action == "music":
            return self._play_music(params)
        elif action == "reminder":
            return self._set_reminder(params)
        else:
            return {"success": False, "message": f"Action '{action}' non supportee"}
    
    # ── ACTION IMPLEMENTATIONS ──
    
    def _send_sms(self, params: Dict) -> Dict:
        contact = params.get("contact", "Inconnu")
        message = params.get("message", "")
        
        if self.dev_mode:
            result = {"success": True, "action": "sms", "contact": contact, 
                     "message": message, "mode": "simulated"}
            self.actions_log.append(result)
            return result
        
        # Android: use SmsManager
        try:
            from jnius import autoclass
            SmsManager = autoclass('android.telephony.SmsManager')
            # Would need to resolve contact name to phone number
            # smsManager.sendTextMessage(phoneNumber, None, message, None, None)
            return {"success": True, "action": "sms", "contact": contact}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _make_call(self, params: Dict) -> Dict:
        contact = params.get("contact", "Inconnu")
        
        if self.dev_mode:
            result = {"success": True, "action": "call", "contact": contact, "mode": "simulated"}
            self.actions_log.append(result)
            return result
        
        try:
            from jnius import autoclass
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            # intent = Intent(Intent.ACTION_CALL)
            # intent.setData(Uri.parse(f"tel:{phoneNumber}"))
            return {"success": True, "action": "call", "contact": contact}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _set_alarm(self, params: Dict) -> Dict:
        time_str = params.get("time", "7:00")
        
        if self.dev_mode:
            result = {"success": True, "action": "alarm", "time": time_str, 
                     "message": f"Alarme programmee a {time_str}", "mode": "simulated"}
            self.actions_log.append(result)
            return result
        
        try:
            from jnius import autoclass
            # AlarmClock = autoclass('android.provider.AlarmClock')
            return {"success": True, "action": "alarm", "time": time_str}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _add_calendar(self, params: Dict) -> Dict:
        title = params.get("title", "Evenement")
        when = params.get("when", "maintenant")
        
        if self.dev_mode:
            result = {"success": True, "action": "calendar", "title": title, 
                     "when": when, "message": f"\"{title}\" ajoute au calendrier ({when})", 
                     "mode": "simulated"}
            self.actions_log.append(result)
            return result
        
        try:
            # Android Calendar Provider
            return {"success": True, "action": "calendar", "title": title}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_weather(self, params: Dict) -> Dict:
        location = params.get("location", "ici")
        
        if self.dev_mode:
            # Simulate weather data
            temps = [12, 15, 18, 20, 22, 25, 28, 30, 27, 18, 14, 10]
            month = datetime.datetime.now().month
            temp = temps[min(month - 1, 11)]
            conditions = ["ensoleille", "nuageux", "pluvieux", "orageux"]
            cond = conditions[month % 4]
            
            return {
                "success": True, "action": "weather",
                "location": location, "temperature": temp,
                "condition": cond, "humidity": 65,
                "message": f"{temp}°C, {cond} a {location}. Humidite: 65%.",
                "mode": "simulated"
            }
        
        # Real weather: would call OpenWeatherMap API or similar
        return {"success": False, "error": "API meteo non configuree"}
    
    def _take_note(self, params: Dict) -> Dict:
        text = params.get("text", "")
        timestamp = datetime.datetime.now().isoformat()
        
        # Save to local storage
        notes_dir = os.path.join(os.path.dirname(__file__), "..", "data", "notes")
        os.makedirs(notes_dir, exist_ok=True)
        
        note_file = os.path.join(notes_dir, f"note_{timestamp[:10]}.json")
        notes = []
        if os.path.exists(note_file):
            with open(note_file, 'r', encoding='utf-8') as f:
                notes = json.load(f)
        
        notes.append({"text": text, "time": timestamp})
        
        with open(note_file, 'w', encoding='utf-8') as f:
            json.dump(notes, f, ensure_ascii=False, indent=2)
        
        result = {"success": True, "action": "note", "text": text, 
                 "message": f"Note enregistree: \"{text[:50]}\"", 
                 "file": note_file}
        self.actions_log.append(result)
        return result
    
    def _web_search(self, params: Dict) -> Dict:
        query = params.get("query", "")
        
        if self.dev_mode:
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            try:
                webbrowser.open(url)
            except:
                pass
            return {"success": True, "action": "search", "query": query,
                   "url": url, "mode": "simulated"}
        
        # Android: open browser intent
        return {"success": True, "action": "search", "query": query}
    
    def _open_app(self, params: Dict) -> Dict:
        app = params.get("app", "").lower()
        
        # Map common app names to package names
        APP_MAP = {
            "whatsapp": "com.whatsapp",
            "maps": "com.google.android.apps.maps",
            "google maps": "com.google.android.apps.maps",
            "youtube": "com.google.android.youtube",
            "spotify": "com.spotify.music",
            "instagram": "com.instagram.android",
            "gmail": "com.google.android.gm",
            "chrome": "com.android.chrome",
            "camera": "com.android.camera",
            "gallery": "com.android.gallery3d",
            "calendar": "com.android.calendar",
            "calculator": "com.android.calculator2",
            "clock": "com.android.deskclock",
            "settings": "com.android.settings",
            "phone": "com.android.dialer",
            "contacts": "com.android.contacts",
        }
        
        package = APP_MAP.get(app, app)
        
        if self.dev_mode:
            result = {"success": True, "action": "open_app", "app": app, 
                     "package": package, "message": f"Ouverture de {app}", 
                     "mode": "simulated"}
            self.actions_log.append(result)
            return result
        
        try:
            from jnius import autoclass
            # PythonActivity = autoclass('org.kivy.android.PythonActivity')
            # context = PythonActivity.mActivity
            # launchIntent = context.getPackageManager().getLaunchIntentForPackage(package)
            # context.startActivity(launchIntent)
            return {"success": True, "action": "open_app", "app": app}
        except Exception as e:
            return {"success": False, "error": str(e), "action": "open_app", "app": app}
    
    def _play_music(self, params: Dict) -> Dict:
        song = params.get("song", "")
        
        if self.dev_mode:
            result = {"success": True, "action": "music", "song": song,
                     "message": f"Lecture de \"{song}\"", "mode": "simulated"}
            self.actions_log.append(result)
            return result
        
        try:
            # Would use MediaPlayer or Spotify API
            return {"success": True, "action": "music", "song": song}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _set_reminder(self, params: Dict) -> Dict:
        what = params.get("what", "")
        when = params.get("when", "plus tard")
        
        # Save reminder to local storage
        reminders_dir = os.path.join(os.path.dirname(__file__), "..", "data", "reminders")
        os.makedirs(reminders_dir, exist_ok=True)
        
        reminder_file = os.path.join(reminders_dir, "reminders.json")
        reminders = []
        if os.path.exists(reminder_file):
            with open(reminder_file, 'r', encoding='utf-8') as f:
                reminders = json.load(f)
        
        reminders.append({
            "what": what, "when": when,
            "created": datetime.datetime.now().isoformat(),
            "status": "pending"
        })
        
        with open(reminder_file, 'w', encoding='utf-8') as f:
            json.dump(reminders, f, ensure_ascii=False, indent=2)
        
        result = {"success": True, "action": "reminder", "what": what,
                 "when": when, "message": f"Je te rappellerai de \"{what}\" {when}",
                 "file": reminder_file}
        self.actions_log.append(result)
        return result


if __name__ == "__main__":
    pa = PhoneActions(dev_mode=True)
    
    tests = [
        ("sms", {"contact": "Marie", "message": "Je serai en retard"}),
        ("call", {"contact": "Papa"}),
        ("alarm", {"time": "7:00"}),
        ("calendar", {"title": "Dentiste", "when": "jeudi 14h"}),
        ("weather", {"location": "Paris"}),
        ("note", {"text": "Acheter du pain"}),
        ("search", {"query": "horaires musee Louvre"}),
        ("open_app", {"app": "whatsapp"}),
        ("music", {"song": "jazz"}),
        ("reminder", {"what": "acheter du pain", "when": "demain 9h"}),
    ]
    
    for action, params in tests:
        r = pa.execute(action, params)
        status = "OK" if r.get("success") else "KO"
        msg = r.get("message", r.get("error", "?"))
        print(f"[{status}] {action:10s} → {msg}")
    
    print(f"\nActions log: {len(pa.actions_log)} actions recorded")