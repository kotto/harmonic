/* ── KA Design System Types ── */

export type ColorAccent = 'soul' | 'life' | 'wisdom' | 'rose' | 'sky' | 'coral'

export interface User {
  id: string
  name: string
  domains: string[]
  customInterests: string[]
  onboarded: boolean
}

export interface Message {
  id: string
  text: string
  sender: 'user' | 'contact' | 'ka'
  timestamp: Date
}

export interface Contact {
  id: string
  name: string
  initials: string
  online: boolean
  color: ColorAccent
}

export interface MemoryItem {
  id: string
  title: string
  date: string
  photoCount: number
  messageCount?: number
  location?: string
  photos: string[] // gradient strings or URLs
  lastMessage?: string
  timeline: TimelineEntry[]
}

export interface TimelineEntry {
  id: string
  title: string
  subtitle: string
  color: ColorAccent
}

export interface Stat {
  label: string
  value: string | number
  color?: 'default' | 'green' | 'red' | 'accent'
  suffix?: string
}

export interface Participant {
  initials: string
  name: string
  color: ColorAccent
}

export interface AgendaItem {
  title: string
  by?: string
  priority?: 'normal' | 'high'
}

/* ── Keyboard ── */
export interface KeyRow {
  label: string
  alt?: string
  width?: number
}

export type NavTab = 'home' | 'messages' | 'memory' | 'more'