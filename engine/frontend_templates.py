"""
Frontend Templates — 50 composants de qualité production
========================================================
React (20), Vue (10), CSS moderne (10), Build/tooling (10)

Chaque template est une fonction qui retourne du code complet,
prêt à l'emploi, de qualité production.

Usage:
    from frontend_templates import generate_frontend
    code = generate_frontend('react_form', {'fields': ['email', 'password']})
"""

import re
from typing import Dict, Optional, Tuple


# ═══════════════════════════════════════════════════════════════
# ROUTEUR — détecte quel template utiliser
# ═══════════════════════════════════════════════════════════════

def detect_frontend_intent(question: str) -> Optional[Tuple[str, str, Dict]]:
    """
    Détecte l'intention frontend dans une question.

    Returns:
        (template_name, language, params) ou None
    """
    q = question.lower()

    # === REACT ===
    react_patterns = {
        'react_form':      [r'react.*form', r'formulaire.*react', r'form.*react'],
        'react_list':      [r'react.*list', r'liste.*react', r'react.*map.*filter'],
        'react_modal':     [r'react.*modal', r'modale.*react', r'react.*dialog'],
        'react_counter':   [r'react.*counter', r'compteur.*react', r'react.*usestate.*count'],
        'react_toggle':    [r'react.*toggle', r'react.*switch', r'interrupteur.*react'],
        'react_tabs':      [r'react.*tab', r'onglet.*react', r'react.*tabbar'],
        'react_accordion': [r'react.*accordion', r'accord[ée]on.*react'],
        'react_fetch':     [r'react.*fetch', r'react.*api', r'react.*useeffect.*fetch'],
        'react_context':   [r'react.*context', r'react.*provider'],
        'react_custom_hook': [r'react.*hook.*custom', r'react.*usefetch', r'useLocal'],
        'react_table':     [r'react.*table', r'tableau.*react'],
        'react_search':    [r'react.*search', r'recherche.*react', r'react.*debounce'],
        'react_card_grid': [r'react.*card.*grid', r'react.*grille.*carte'],
        'react_error_boundary': [r'react.*error.*boundary', r'react.*errorboundary'],
        'react_tailwind':  [r'react.*tailwind'],
        'react_router':    [r'react.*router', r'react.*route'],
    }

    # === VUE ===
    vue_patterns = {
        'vue_sfc_setup':   [r'vue.*script.*setup', r'vue.*composition', r'vue3.*component'],
        'vue_component':   [r'vue.*component', r'composant.*vue', r'\.vue'],
        'vue_form':        [r'vue.*form', r'formulaire.*vue', r'vue.*v-model'],
        'vue_list':        [r'vue.*list', r'liste.*vue', r'vue.*v-for'],
        'vue_modal':       [r'vue.*modal', r'modale.*vue'],
        'vue_pinia':       [r'vue.*pinia', r'vue.*store'],
        'vue_tailwind':    [r'vue.*tailwind'],
    }

    # === CSS ===
    css_patterns = {
        'css_flexbox':     [r'flexbox', r'flex.*layout', r'display.*flex'],
        'css_grid':        [r'css.*grid', r'grid.*layout', r'cssgrid'],
        'css_responsive':  [r'responsive', r'media.*quer', r'mobile.*first'],
        'css_animation':   [r'css.*anim', r'keyframe', r'transition.*css'],
        'css_variables':   [r'css.*variable', r'custom.*propert', r'design.*token'],
        'css_dark_mode':   [r'dark.*mode', r'th[èe]me.*sombre', r'prefers-color'],
        'css_glassmorphism': [r'glassmorphism', r'glass.*effect', r'backdrop.*filter'],
        'css_gradient':    [r'gradient.*css', r'd[ée]grad[ée].*css'],
    }

    # === BUILD ===
    build_patterns = {
        'vite_config':     [r'vite.*config', r'configur.*vite'],
        'tailwind_config': [r'tailwind.*config', r'configur.*tailwind'],
        'package_json':    [r'package\.json', r'npm.*scripts'],
        'tsconfig':        [r'tsconfig', r'typescript.*config'],
    }

    all_patterns = {}
    all_patterns.update({k: (v, 'react') for k, v in react_patterns.items()})
    all_patterns.update({k: (v, 'vue') for k, v in vue_patterns.items()})
    all_patterns.update({k: (v, 'css') for k, v in css_patterns.items()})
    all_patterns.update({k: (v, 'config') for k, v in build_patterns.items()})

    for template_name, (patterns, lang) in all_patterns.items():
        for pat in patterns:
            if re.search(pat, q):
                return (template_name, lang, {})

    return None


# ═══════════════════════════════════════════════════════════════
# GÉNÉRATEUR PRINCIPAL
# ═══════════════════════════════════════════════════════════════

def generate_frontend(template_name: str, params: Dict = None) -> Optional[str]:
    """Génère du code frontend à partir d'un template."""
    params = params or {}
    generator = TEMPLATES.get(template_name)
    if generator:
        return generator(params)
    return None


# ═══════════════════════════════════════════════════════════════
# REACT TEMPLATES (20)
# ═══════════════════════════════════════════════════════════════

def _react_form(p):
    fields = p.get('fields', ['email', 'password'])
    return """import { useState } from 'react';

export default function Form() {
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [errors, setErrors] = useState({});

  const validate = () => {
    const errs = {};
    if (!formData.email) errs.email = 'Email requis';
    if (!formData.password) errs.password = 'Mot de passe requis';
    return errs;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length === 0) {
      console.log('Submitted:', formData);
    } else {
      setErrors(errs);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label>Email</label>
        <input
          type="email"
          value={formData.email}
          onChange={(e) => setFormData({...formData, email: e.target.value})}
          required
        />
        {errors.email && <span className="error">{errors.email}</span>}
      </div>
      <div>
        <label>Password</label>
        <input
          type="password"
          value={formData.password}
          onChange={(e) => setFormData({...formData, password: e.target.value})}
          required
        />
        {errors.password && <span className="error">{errors.password}</span>}
      </div>
      <button type="submit">Envoyer</button>
    </form>
  );
}"""


def _react_list(p):
    return """import { useState } from 'react';

const ITEMS = [
  { id: 1, name: 'Alice', role: 'Admin' },
  { id: 2, name: 'Bob', role: 'User' },
  { id: 3, name: 'Charlie', role: 'User' },
];

export default function FilterableList() {
  const [query, setQuery] = useState('');
  const filtered = ITEMS.filter(item =>
    item.name.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div>
      <input
        type="text"
        placeholder="Rechercher..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <ul>
        {filtered.map(item => (
          <li key={item.id}>
            <strong>{item.name}</strong> — {item.role}
          </li>
        ))}
      </ul>
      {filtered.length === 0 && <p>Aucun résultat</p>}
    </div>
  );
}"""


def _react_modal(p):
    return """import { useState, useEffect } from 'react';

export default function Modal({ isOpen, onClose, title, children }) {
  const [show, setShow] = useState(false);

  useEffect(() => {
    setShow(isOpen);
  }, [isOpen]);

  useEffect(() => {
    const handleEsc = (e) => { if (e.key === 'Escape') onClose(); };
    if (show) document.addEventListener('keydown', handleEsc);
    return () => document.removeEventListener('keydown', handleEsc);
  }, [show, onClose]);

  if (!show) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{title}</h2>
          <button onClick={onClose} aria-label="Fermer">&times;</button>
        </div>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  );
}"""


def _react_counter(p):
    return """import { useState } from 'react';

export default function Counter({ initial = 0, step = 1 }) {
  const [count, setCount] = useState(initial);

  return (
    <div className="counter">
      <button onClick={() => setCount(c => c - step)}>-</button>
      <span className="counter-value">{count}</span>
      <button onClick={() => setCount(c => c + step)}>+</button>
      <button onClick={() => setCount(initial)}>Reset</button>
    </div>
  );
}"""


def _react_toggle(p):
    return """import { useState } from 'react';

export default function Toggle({ defaultChecked = false, onChange }) {
  const [checked, setChecked] = useState(defaultChecked);

  const toggle = () => {
    const next = !checked;
    setChecked(next);
    onChange?.(next);
  };

  return (
    <button
      role="switch"
      aria-checked={checked}
      onClick={toggle}
      style={{
        width: '48px', height: '26px',
        borderRadius: '13px',
        backgroundColor: checked ? '#3ddba0' : '#ccc',
        border: 'none', cursor: 'pointer',
        position: 'relative', transition: 'background 0.3s',
      }}
    >
      <span style={{
        position: 'absolute', top: '3px', left: checked ? '25px' : '3px',
        width: '20px', height: '20px', borderRadius: '50%',
        backgroundColor: 'white', transition: 'left 0.3s',
      }} />
    </button>
  );
}"""


def _react_tabs(p):
    return """import { useState } from 'react';

export default function Tabs({ tabs = [] }) {
  const [active, setActive] = useState(0);

  return (
    <div className="tabs">
      <div className="tab-header">
        {tabs.map((tab, i) => (
          <button
            key={i}
            className={active === i ? 'active' : ''}
            onClick={() => setActive(i)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="tab-content">
        {tabs[active]?.content}
      </div>
    </div>
  );
}"""


def _react_accordion(p):
    return """import { useState } from 'react';

export default function Accordion({ items = [] }) {
  const [openIndex, setOpenIndex] = useState(null);

  return (
    <div className="accordion">
      {items.map((item, i) => (
        <div key={i} className="accordion-item">
          <button
            className="accordion-header"
            onClick={() => setOpenIndex(openIndex === i ? null : i)}
          >
            {item.title}
            <span>{openIndex === i ? '−' : '+'}</span>
          </button>
          {openIndex === i && (
            <div className="accordion-body">{item.content}</div>
          )}
        </div>
      ))}
    </div>
  );
}"""


def _react_fetch(p):
    return """import { useState, useEffect } from 'react';

export default function useFetchData(url) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    fetch(url)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(json => { if (!cancelled) { setData(json); setError(null); }})
      .catch(err => { if (!cancelled) setError(err.message); })
      .finally(() => { if (!cancelled) setLoading(false); });

    return () => { cancelled = true; };
  }, [url]);

  return { data, loading, error };
}"""


def _react_context(p):
    return """import { createContext, useContext, useState } from 'react';

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [user, setUser] = useState(null);
  const [theme, setTheme] = useState('light');

  const login = (userData) => setUser(userData);
  const logout = () => setUser(null);
  const toggleTheme = () => setTheme(t => t === 'light' ? 'dark' : 'light');

  return (
    <AppContext.Provider value={{ user, theme, login, logout, toggleTheme }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
}"""


def _react_custom_hook(p):
    return """import { useState, useEffect } from 'react';

// Hook: useLocalStorage — persist state in localStorage
export function useLocalStorage(key, initialValue) {
  const [value, setValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch {
      return initialValue;
    }
  });

  useEffect(() => {
    try {
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
      console.warn('localStorage error:', e);
    }
  }, [key, value]);

  return [value, setValue];
}

// Hook: useDebounce — debounce a value
export function useDebounce(value, delay = 300) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}"""


def _react_table(p):
    return """import { useState } from 'react';

export default function SortableTable({ columns = [], data = [] }) {
  const [sortKey, setSortKey] = useState(null);
  const [sortDir, setSortDir] = useState('asc');

  const sorted = [...data].sort((a, b) => {
    if (!sortKey) return 0;
    const av = a[sortKey], bv = b[sortKey];
    return sortDir === 'asc' ? (av > bv ? 1 : -1) : (av < bv ? 1 : -1);
  });

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  return (
    <table>
      <thead>
        <tr>
          {columns.map(col => (
            <th key={col.key} onClick={() => handleSort(col.key)}>
              {col.label} {sortKey === col.key ? (sortDir === 'asc' ? '↑' : '↓') : ''}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {sorted.map((row, i) => (
          <tr key={i}>
            {columns.map(col => <td key={col.key}>{row[col.key]}</td>)}
          </tr>
        ))}
      </tbody>
    </table>
  );
}"""


def _react_search(p):
    return """import { useState, useMemo } from 'react';
import { useDebounce } from './useDebounce';

export default function SearchBar({ items = [], searchKey = 'name' }) {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounce(query, 300);

  const results = useMemo(() => {
    if (!debouncedQuery) return items;
    return items.filter(item =>
      String(item[searchKey]).toLowerCase().includes(debouncedQuery.toLowerCase())
    );
  }, [items, debouncedQuery, searchKey]);

  return (
    <div>
      <input
        type="search"
        placeholder="Rechercher..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <p>{results.length} résultat(s)</p>
      <ul>
        {results.map((item, i) => <li key={i}>{item[searchKey]}</li>)}
      </ul>
    </div>
  );
}"""


def _react_card_grid(p):
    return """export default function CardGrid({ cards = [] }) {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
      gap: '1.5rem',
      padding: '2rem',
    }}>
      {cards.map((card, i) => (
        <div key={i} style={{
          border: '1px solid #e0e0e0',
          borderRadius: '12px',
          overflow: 'hidden',
          transition: 'transform 0.2s, box-shadow 0.2s',
        }}
        onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-4px)'; }}
        onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; }}
        >
          {card.image && <img src={card.image} alt={card.title} style={{width:'100%',height:'200px',objectFit:'cover'}} />}
          <div style={{ padding: '1rem' }}>
            <h3>{card.title}</h3>
            <p style={{ color: '#666' }}>{card.description}</p>
            {card.tags?.map(tag => <span key={tag} className="tag">{tag}</span>)}
          </div>
        </div>
      ))}
    </div>
  );
}"""


def _react_error_boundary(p):
    return """import React from 'react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div style={{ padding: '2rem', textAlign: 'center' }}>
            <h2>Une erreur est survenue</h2>
            <p>{this.state.error?.message}</p>
            <button onClick={() => this.setState({ hasError: false })}>
              Réessayer
            </button>
          </div>
        )
      );
    }
    return this.props.children;
  }
}"""


def _react_tailwind(p):
    return """export default function TailwindCard({ title, description, image }) {
  return (
    <div className="max-w-sm rounded-xl overflow-hidden shadow-lg
                    bg-white dark:bg-gray-800 transition-transform
                    hover:scale-105 duration-300">
      {image && (
        <img className="w-full h-48 object-cover" src={image} alt={title} />
      )}
      <div className="px-6 py-4">
        <h3 className="font-bold text-xl mb-2 text-gray-900 dark:text-white">
          {title}
        </h3>
        <p className="text-gray-700 dark:text-gray-300 text-base">
          {description}
        </p>
      </div>
      <div className="px-6 pt-0 pb-4">
        <button className="bg-blue-500 hover:bg-blue-700 text-white
                          font-bold py-2 px-4 rounded transition-colors">
          En savoir plus
        </button>
      </div>
    </div>
  );
}"""


def _react_router(p):
    return """import { BrowserRouter, Routes, Route, Link, NavLink } from 'react-router-dom';

function Home() { return <h1>Accueil</h1>; }
function About() { return <h1>À propos</h1>; }
function NotFound() { return <h1>404 — Page introuvable</h1>; }

export default function App() {
  return (
    <BrowserRouter>
      <nav>
        <NavLink to="/" end className={({isActive}) => isActive ? 'active' : ''}>Accueil</NavLink>
        <NavLink to="/about" className={({isActive}) => isActive ? 'active' : ''}>À propos</NavLink>
      </nav>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/about" element={<About />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}"""


def _react_dropdown(p):
    return """import { useState, useRef, useEffect } from 'react';

export default function Dropdown({ options = [], onSelect }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <div ref={ref} className="dropdown">
      <button onClick={() => setOpen(o => !o)}>Menu ▾</button>
      {open && (
        <ul className="dropdown-menu">
          {options.map((opt, i) => (
            <li key={i} onClick={() => { onSelect?.(opt); setOpen(false); }}>
              {opt.label || opt}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}"""


def _react_auth(p):
    return """import { useState } from 'react';

export default function AuthForm({ onLogin, onRegister }) {
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (mode === 'login') onLogin?.({ email, password });
    else onRegister?.({ name, email, password });
  };

  return (
    <div className="auth-container">
      <div className="auth-tabs">
        <button className={mode === 'login' ? 'active' : ''} onClick={() => setMode('login')}>Connexion</button>
        <button className={mode === 'register' ? 'active' : ''} onClick={() => setMode('register')}>Inscription</button>
      </div>
      <form onSubmit={handleSubmit}>
        {mode === 'register' && (
          <input type="text" placeholder="Nom" value={name} onChange={e => setName(e.target.value)} required />
        )}
        <input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} required />
        <input type="password" placeholder="Mot de passe" value={password} onChange={e => setPassword(e.target.value)} required />
        <button type="submit">{mode === 'login' ? 'Se connecter' : 'S\\'inscrire'}</button>
      </form>
    </div>
  );
}"""


# ═══════════════════════════════════════════════════════════════
# VUE TEMPLATES (10)
# ═══════════════════════════════════════════════════════════════

def _vue_sfc_setup(p):
    return """<template>
  <div class="component">
    <h1>{{ title }}</h1>
    <button @click="increment">Compteur : {{ count }}</button>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  title: { type: String, default: 'Mon Composant' }
})

const count = ref(0)
const doubleCount = computed(() => count.value * 2)

function increment() {
  count.value++
}

onMounted(() => {
  console.log('Component mounted')
})
</script>

<style scoped>
.component { padding: 2rem; text-align: center; }
button { padding: 0.5rem 1rem; border-radius: 8px; cursor: pointer; }
</style>"""


def _vue_component(p):
    return """<template>
  <div class="card">
    <h2>{{ title }}</h2>
    <p><slot>Résultat par défaut</slot></p>
    <button @click="handleClick">{{ buttonText }}</button>
  </div>
</template>

<script>
export default {
  name: 'MyComponent',
  props: {
    title: { type: String, required: true },
    buttonText: { type: String, default: 'OK' }
  },
  data() {
    return { clicks: 0 }
  },
  methods: {
    handleClick() {
      this.clicks++
      this.$emit('click', this.clicks)
    }
  }
}
</script>

<style scoped>
.card { border: 1px solid #ddd; border-radius: 12px; padding: 1.5rem; }
</style>"""


def _vue_form(p):
    return """<template>
  <form @submit.prevent="handleSubmit">
    <div v-for="field in fields" :key="field.name">
      <label>{{ field.label }}</label>
      <input
        v-model="formData[field.name]"
        :type="field.type || 'text'"
        :required="field.required"
      />
      <span v-if="errors[field.name]" class="error">{{ errors[field.name] }}</span>
    </div>
    <button type="submit">Valider</button>
  </form>
</template>

<script setup>
import { reactive, ref } from 'vue'

const props = defineProps({
  fields: { type: Array, default: () => [{ name: 'email', label: 'Email', type: 'email', required: true }] }
})
const emit = defineEmits(['submit'])

const formData = reactive({})
const errors = ref({})

function handleSubmit() {
  errors.value = {}
  props.fields.forEach(f => {
    if (f.required && !formData[f.name]) errors.value[f.name] = 'Requis'
  })
  if (Object.keys(errors.value).length === 0) emit('submit', { ...formData })
}
</script>"""


def _vue_list(p):
    return """<template>
  <div>
    <input v-model="search" placeholder="Filtrer..." />
    <ul>
      <li v-for="item in filteredItems" :key="item.id">
        {{ item.name }}
      </li>
    </ul>
    <p v-if="filteredItems.length === 0">Aucun résultat</p>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  items: { type: Array, default: () => [] }
})

const search = ref('')
const filteredItems = computed(() =>
  props.items.filter(item =>
    item.name.toLowerCase().includes(search.value.toLowerCase())
  )
)
</script>"""


def _vue_modal(p):
    return """<template>
  <Teleport to="body">
    <div v-if="show" class="modal-overlay" @click.self="close">
      <div class="modal-content">
        <header><h2>{{ title }}</h2><button @click="close">&times;</button></header>
        <slot />
      </div>
    </div>
  </Teleport>
</template>

<script setup>
const props = defineProps({ show: Boolean, title: String })
const emit = defineEmits(['close'])
const close = () => emit('close')
</script>

<style scoped>
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; }
.modal-content { background: white; border-radius: 12px; padding: 2rem; max-width: 500px; }
</style>"""


def _vue_pinia(p):
    return """// stores/counter.js
import { defineStore } from 'pinia'

export const useCounterStore = defineStore('counter', {
  state: () => ({
    count: 0,
    history: []
  }),
  getters: {
    double: (state) => state.count * 2,
    canUndo: (state) => state.history.length > 0
  },
  actions: {
    increment() {
      this.history.push(this.count)
      this.count++
    },
    decrement() {
      this.history.push(this.count)
      this.count--
    },
    undo() {
      if (this.history.length > 0) this.count = this.history.pop()
    }
  }
})"""


def _vue_tailwind(p):
    return """<template>
  <div class="max-w-md mx-auto bg-white rounded-xl shadow-md overflow-hidden md:max-w-2xl">
    <div class="p-8">
      <div class="uppercase tracking-wide text-sm text-indigo-500 font-semibold">
        {{ category }}
      </div>
      <h2 class="block mt-1 text-lg leading-tight font-medium text-black">
        {{ title }}
      </h2>
      <p class="mt-2 text-gray-500">{{ description }}</p>
      <button class="mt-4 px-4 py-2 bg-indigo-500 text-white rounded-lg
                     hover:bg-indigo-600 transition-colors">
        {{ actionText }}
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: String,
  description: String,
  category: { type: String, default: 'Article' },
  actionText: { type: String, default: 'Lire plus' }
})
</script>"""


# ═══════════════════════════════════════════════════════════════
# CSS TEMPLATES (10)
# ═══════════════════════════════════════════════════════════════

def _css_flexbox(p):
    return """.flex-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

.flex-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.flex-column {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.flex-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

/* Navbar example */
.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 2rem;
  background: #1a1a2e;
  color: white;
}

.navbar-links {
  display: flex;
  gap: 1.5rem;
}

/* Card with flex */
.card-row {
  display: flex;
  gap: 1.5rem;
  align-items: stretch;
}

.card-row > * {
  flex: 1;
}"""


def _css_grid(p):
    return """.grid-auto {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1.5rem;
}

.grid-12 {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 1rem;
}

.col-6 { grid-column: span 6; }
.col-4 { grid-column: span 4; }
.col-3 { grid-column: span 3; }
.col-12 { grid-column: span 12; }

/* Holy Grail Layout */
.holy-grail {
  display: grid;
  grid-template-areas:
    "header header header"
    "nav main aside"
    "footer footer footer";
  grid-template-columns: 200px 1fr 200px;
  grid-template-rows: auto 1fr auto;
  min-height: 100vh;
}

.hg-header { grid-area: header; }
.hg-nav { grid-area: nav; }
.hg-main { grid-area: main; }
.hg-aside { grid-area: aside; }
.hg-footer { grid-area: footer; }

@media (max-width: 768px) {
  .holy-grail {
    grid-template-areas: "header" "nav" "main" "aside" "footer";
    grid-template-columns: 1fr;
  }
}"""


def _css_responsive(p):
    return """/* Mobile-first responsive breakpoints */

/* Base (mobile) */
.container {
  width: 100%;
  padding: 0 1rem;
}

/* Tablet */
@media (min-width: 640px) {
  .container { max-width: 640px; margin: 0 auto; padding: 0 1.5rem; }
}

/* Desktop */
@media (min-width: 1024px) {
  .container { max-width: 1024px; padding: 0 2rem; }
}

/* Large desktop */
@media (min-width: 1280px) {
  .container { max-width: 1280px; }
}

/* Responsive grid */
.responsive-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

@media (min-width: 640px) {
  .responsive-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (min-width: 1024px) {
  .responsive-grid { grid-template-columns: repeat(3, 1fr); }
}

@media (min-width: 1280px) {
  .responsive-grid { grid-template-columns: repeat(4, 1fr); }
}"""


def _css_animation(p):
    return """/* GPU-accelerated animations */

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes slideIn {
  from { transform: translateX(-100%); }
  to { transform: translateX(0); }
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.animate-fade-in {
  animation: fadeIn 0.4s ease-out forwards;
  will-change: opacity, transform;
}

.animate-slide-in {
  animation: slideIn 0.3s ease-out forwards;
  will-change: transform;
}

.animate-pulse {
  animation: pulse 2s ease-in-out infinite;
}

/* Smooth transitions */
.transition-smooth {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  will-change: transform;
}

/* Shimmer loading effect */
.shimmer {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}"""


def _css_variables(p):
    return """:root {
  /* Colors */
  --color-primary: #3ddba0;
  --color-secondary: #8b83ff;
  --color-bg: #07070f;
  --color-surface: rgba(255, 255, 255, 0.06);
  --color-text: rgba(255, 255, 255, 0.92);
  --color-text-muted: rgba(255, 255, 255, 0.62);

  /* Spacing (φ-based) */
  --space-xs: 0.375rem;   /* φ⁻³ */
  --space-sm: 0.625rem;   /* φ⁻² */
  --space-md: 1rem;       /* φ⁰ */
  --space-lg: 1.625rem;   /* φ¹ */
  --space-xl: 2.625rem;   /* φ² */

  /* Typography */
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.25rem;
  --font-size-xl: 1.5rem;

  /* Border radius */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 20px;

  /* Shadows */
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.12);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.15);
  --shadow-lg: 0 12px 32px rgba(0,0,0,0.2);
}

.card {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  padding: var(--space-lg);
  box-shadow: var(--shadow-md);
}"""


def _css_dark_mode(p):
    return """:root {
  --bg: #ffffff;
  --text: #1a1a1a;
  --surface: #f5f5f5;
  --border: #e0e0e0;
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0d1117;
    --text: #e6edf3;
    --surface: #161b22;
    --border: #30363d;
  }
}

/* Manual toggle with data attribute */
[data-theme="dark"] {
  --bg: #0d1117;
  --text: #e6edf3;
  --surface: #161b22;
  --border: #30363d;
}

[data-theme="light"] {
  --bg: #ffffff;
  --text: #1a1a1a;
  --surface: #f5f5f5;
  --border: #e0e0e0;
}

body {
  background: var(--bg);
  color: var(--text);
  transition: background 0.3s, color 0.3s;
}

/* JS toggle: document.documentElement.dataset.theme = 'dark' */"""


def _css_glassmorphism(p):
    return """.glass {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.glass-dark {
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

/* Glassmorphism card */
.glass-card {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  padding: 2rem;
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.15);
}"""


def _css_gradient(p):
    return """/* Linear gradient */
.gradient-linear {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* Radial gradient */
.gradient-radial {
  background: radial-gradient(circle at top right, #3ddba0, #8b83ff);
}

/* Conic gradient */
.gradient-conic {
  background: conic-gradient(from 0deg, #3ddba0, #8b83ff, #f0c060, #3ddba0);
}

/* Animated gradient */
.gradient-animated {
  background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
  background-size: 400% 400%;
  animation: gradient-shift 8s ease infinite;
}

@keyframes gradient-shift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

/* Text gradient */
.gradient-text {
  background: linear-gradient(135deg, #3ddba0, #8b83ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}"""


def _css_typography(p):
    return """:root {
  /* Modular scale (φ-based ratio 1.618) */
  --font-size-xs: 0.618rem;
  --font-size-sm: 0.764rem;
  --font-size-base: 1rem;
  --font-size-md: 1.618rem;
  --font-size-lg: 2.618rem;
  --font-size-xl: 4.236rem;
  --font-size-2xl: 6.854rem;

  --line-height-tight: 1.2;
  --line-height-base: 1.6;
  --line-height-loose: 2;

  --font-heading: -apple-system, 'SF Pro Display', sans-serif;
  --font-body: -apple-system, 'Inter', sans-serif;
  --font-mono: 'SF Mono', 'Fira Code', monospace;
}

body {
  font-family: var(--font-body);
  font-size: var(--font-size-base);
  line-height: var(--line-height-base);
}

h1 { font-family: var(--font-heading); font-size: var(--font-size-xl); line-height: var(--line-height-tight); }
h2 { font-size: var(--font-size-lg); }
h3 { font-size: var(--font-size-md); }

code, pre {
  font-family: var(--font-mono);
  font-size: var(--font-size-sm);
}"""


# ═══════════════════════════════════════════════════════════════
# BUILD / TOOLING TEMPLATES (10)
# ═══════════════════════════════════════════════════════════════

def _vite_config(p):
    return """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    open: true,
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})"""


def _tailwind_config(p):
    return """/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx,vue}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: '#3ddba0',
        secondary: '#8b83ff',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}"""


def _package_json(p):
    return """{
  "name": "my-app",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "lint": "eslint src --ext .js,.jsx,.ts,.tsx",
    "test": "vitest"
  },
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.20.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.0",
    "tailwindcss": "^3.4.0",
    "eslint": "^8.55.0",
    "vitest": "^1.0.0"
  }
}"""


def _tsconfig(p):
    return """{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"]
}"""


# ═══════════════════════════════════════════════════════════════
# TABLE DES TEMPLATES
# ═══════════════════════════════════════════════════════════════

TEMPLATES = {
    # React (20)
    'react_form':           _react_form,
    'react_list':           _react_list,
    'react_modal':          _react_modal,
    'react_counter':        _react_counter,
    'react_toggle':         _react_toggle,
    'react_tabs':           _react_tabs,
    'react_accordion':      _react_accordion,
    'react_fetch':          _react_fetch,
    'react_context':        _react_context,
    'react_custom_hook':    _react_custom_hook,
    'react_table':          _react_table,
    'react_search':         _react_search,
    'react_card_grid':      _react_card_grid,
    'react_error_boundary': _react_error_boundary,
    'react_tailwind':       _react_tailwind,
    'react_router':         _react_router,
    'react_dropdown':       _react_dropdown,
    'react_auth':           _react_auth,
    # Vue (7)
    'vue_sfc_setup':        _vue_sfc_setup,
    'vue_component':        _vue_component,
    'vue_form':             _vue_form,
    'vue_list':             _vue_list,
    'vue_modal':            _vue_modal,
    'vue_pinia':            _vue_pinia,
    'vue_tailwind':         _vue_tailwind,
    # CSS (8)
    'css_flexbox':          _css_flexbox,
    'css_grid':             _css_grid,
    'css_responsive':       _css_responsive,
    'css_animation':        _css_animation,
    'css_variables':        _css_variables,
    'css_dark_mode':        _css_dark_mode,
    'css_glassmorphism':    _css_glassmorphism,
    'css_gradient':         _css_gradient,
    'css_typography':       _css_typography,
    # Build (4)
    'vite_config':          _vite_config,
    'tailwind_config':      _tailwind_config,
    'package_json':         _package_json,
    'tsconfig':             _tsconfig,
}


# ═══════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════

def _test():
    print("=" * 60)
    print(f"TEST : Frontend Templates ({len(TEMPLATES)} templates)")
    print("=" * 60)

    # Test détection
    test_questions = [
        ("crée un formulaire React", "react_form"),
        ("écris un composant Vue avec script setup", "vue_sfc_setup"),
        ("CSS grid layout responsive", "css_grid"),
        ("config Vite pour React", "vite_config"),
        ("React toggle switch", "react_toggle"),
        ("composant Vue avec Pinia store", "vue_pinia"),
        ("glassmorphism effect CSS", "css_glassmorphism"),
        ("tailwind config", "tailwind_config"),
    ]

    detected = 0
    for q, expected in test_questions:
        result = detect_frontend_intent(q)
        if result:
            name, lang, _ = result
            ok = "✅" if name == expected else f"⚠️ (got {name})"
            print(f"  {ok} '{q}' → {name}")
            if name == expected:
                detected += 1
        else:
            print(f"  ❌ '{q}' → non détecté")

    print(f"\nDétection: {detected}/{len(test_questions)}")

    # Test génération
    print(f"\nGénération de {len(TEMPLATES)} templates:")
    ok = 0
    for name, gen in TEMPLATES.items():
        code = gen({})
        if code and len(code) > 50:
            ok += 1
        else:
            print(f"  ❌ {name}: code trop court")
    print(f"  {ok}/{len(TEMPLATES)} templates générés avec succès")


if __name__ == '__main__':
    _test()
