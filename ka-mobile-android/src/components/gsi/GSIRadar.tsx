/**
 * GSIRadar — Visualisation radar des 5 oscillateurs physiologiques
 * Canvas-based, 5 axes (S/D, LF/HF, I/E, β/α, Temp)
 */

import { useEffect, useRef } from 'react'
import type { GSIResult, OscillatorReading } from '@/services/gsi'
import { statusColor } from '@/services/gsi'

interface GSIRadarProps {
  result: GSIResult
  size?: number
}

export default function GSIRadar({ result, size = 220 }: GSIRadarProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || result.oscillators.length === 0) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const dpr = window.devicePixelRatio || 1
    canvas.width = size * dpr
    canvas.height = size * dpr
    ctx.scale(dpr, dpr)

    const cx = size / 2
    const cy = size / 2
    const radius = size * 0.35
    const n = result.oscillators.length

    // Clear
    ctx.clearRect(0, 0, size, size)

    // Background rings
    for (let ring = 1; ring <= 3; ring++) {
      const r = (radius * ring) / 3
      ctx.beginPath()
      for (let i = 0; i <= n; i++) {
        const angle = (2 * Math.PI * i) / n - Math.PI / 2
        const x = cx + r * Math.cos(angle)
        const y = cy + r * Math.sin(angle)
        if (i === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
      }
      ctx.strokeStyle = `rgba(45,212,191,${0.06 + ring * 0.03})`
      ctx.lineWidth = 0.5
      ctx.stroke()
    }

    // Axes
    for (let i = 0; i < n; i++) {
      const angle = (2 * Math.PI * i) / n - Math.PI / 2
      const x = cx + radius * Math.cos(angle)
      const y = cy + radius * Math.sin(angle)
      ctx.beginPath()
      ctx.moveTo(cx, cy)
      ctx.lineTo(x, y)
      ctx.strokeStyle = 'rgba(45,212,191,0.10)'
      ctx.lineWidth = 0.5
      ctx.stroke()
    }

    // Target polygon (φ values)
    ctx.beginPath()
    for (let i = 0; i <= n; i++) {
      const idx = i % n
      const angle = (2 * Math.PI * idx) / n - Math.PI / 2
      const r = radius * 0.85 // target ≈ 85% du rayon max
      const x = cx + r * Math.cos(angle)
      const y = cy + r * Math.sin(angle)
      if (i === 0) ctx.moveTo(x, y)
      else ctx.lineTo(x, y)
    }
    ctx.strokeStyle = 'rgba(45,212,191,0.25)'
    ctx.lineWidth = 1
    ctx.setLineDash([4, 3])
    ctx.stroke()
    ctx.setLineDash([])

    // Value polygon
    ctx.beginPath()
    for (let i = 0; i <= n; i++) {
      const idx = i % n
      const osc = result.oscillators[idx]
      const angle = (2 * Math.PI * idx) / n - Math.PI / 2
      const normalizedValue = 1 - osc.delta // 1 = parfait, 0 = écarté
      const r = radius * (0.1 + normalizedValue * 0.9)
      const x = cx + r * Math.cos(angle)
      const y = cy + r * Math.sin(angle)
      if (i === 0) ctx.moveTo(x, y)
      else ctx.lineTo(x, y)
    }
    ctx.closePath()
    ctx.fillStyle = `${result.color}18`
    ctx.fill()
    ctx.strokeStyle = result.color
    ctx.lineWidth = 1.5
    ctx.stroke()

    // Data points
    result.oscillators.forEach((osc, i) => {
      const angle = (2 * Math.PI * i) / n - Math.PI / 2
      const normalizedValue = 1 - osc.delta
      const r = radius * (0.1 + normalizedValue * 0.9)
      const x = cx + r * Math.cos(angle)
      const y = cy + r * Math.sin(angle)

      // Point
      ctx.beginPath()
      ctx.arc(x, y, 3.5, 0, 2 * Math.PI)
      ctx.fillStyle = statusColor(osc.status)
      ctx.fill()

      // Glow
      ctx.beginPath()
      ctx.arc(x, y, 6, 0, 2 * Math.PI)
      ctx.fillStyle = statusColor(osc.status) + '30'
      ctx.fill()
    })

    // Labels
    ctx.font = '10px -apple-system, system-ui, sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    result.oscillators.forEach((osc, i) => {
      const angle = (2 * Math.PI * i) / n - Math.PI / 2
      const labelR = radius + 18
      const x = cx + labelR * Math.cos(angle)
      const y = cy + labelR * Math.sin(angle)
      ctx.fillStyle = 'rgba(230,255,250,0.52)'
      ctx.fillText(osc.label, x, y)
    })

    // Score au centre
    ctx.font = 'bold 22px -apple-system, system-ui, sans-serif'
    ctx.fillStyle = result.color
    ctx.fillText(String(result.score), cx, cy - 8)
    ctx.font = '9px -apple-system, system-ui, sans-serif'
    ctx.fillStyle = 'rgba(230,255,250,0.52)'
    ctx.fillText(result.label, cx, cy + 12)

  }, [result, size])

  if (result.oscillators.length === 0) return null

  return (
    <canvas
      ref={canvasRef}
      style={{ width: size, height: size }}
      aria-label={`Radar GSI: score ${result.score}`}
    />
  )
}
