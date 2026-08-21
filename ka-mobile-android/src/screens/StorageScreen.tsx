import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import SpaceHeader from '@/components/layout/SpaceHeader'
import Button from '@/components/ui/Button'
import Pill from '@/components/ui/Pill'
import { hcv2, formatSize } from '@/services/hcv2'
import type { FileCompressionResult } from '@/services/hcv2'

type Quality = 'archive' | 'standard' | 'eco'

export default function StorageScreen() {
  const navigate = useNavigate()
  const [quality, setQuality] = useState<Quality>('standard')
  const [files, setFiles] = useState<File[]>([])
  const [results, setResults] = useState<FileCompressionResult[]>([])
  const [optimizing, setOptimizing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [totalFiles, setTotalFiles] = useState(0)
  const [codecStatus, setCodecStatus] = useState<string>('')
  const [wasmReady, setWasmReady] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const totalOrig = results.reduce((s, r) => s + r.origSize, 0)
  const totalComp = results.reduce((s, r) => s + r.compSize, 0)
  const totalSaved = totalOrig - totalComp
  const savingsPct = totalOrig > 0 ? Math.round(totalSaved / totalOrig * 100) : 0

  // Vérifier l'état du codec au chargement
  useEffect(() => {
    async function check() {
      const ok = await hcv2.checkWasmAccessible()
      setWasmReady(ok)
      if (ok) {
        setCodecStatus('WASM ✓')
        hcv2.init().then(ready => {
          setCodecStatus(ready ? 'HCV2 ✓' : 'HCV2 (serveur)')
        })
      } else {
        setCodecStatus('estimation')
      }
    }
    check()
  }, [])

  const handleFiles = (newFiles: FileList) => {
    const fileList = Array.from(newFiles)
    setFiles(prev => [...prev, ...fileList])
    // Réinitialiser les résultats quand de nouveaux fichiers sont ajoutés
    setResults([])
  }

  const handleOptimize = async () => {
    if (files.length === 0) return
    setOptimizing(true)
    setResults([])
    setProgress(0)
    setTotalFiles(files.length)

    const compResults = await hcv2.compressAll(files, quality, (done) => {
      setProgress(done)
    })

    setResults(compResults)
    setOptimizing(false)
  }

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
    setResults([])
  }

  const clearAll = () => {
    setFiles([])
    setResults([])
    setProgress(0)
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden min-h-0"
      style={{ background: 'linear-gradient(160deg, #141e20 0%, #0a0e0f 100%)' }}>
      <SpaceHeader title="KA" badge="ESPACE DISQUE" badgeColor="sky" backPath="/" />

      <div className="flex-1 overflow-y-auto px-5 hide-scrollbar min-h-0">
        {/* Status codec */}
        <div className="flex items-center justify-center gap-2 mb-2">
          <Pill color="sky" size="xs">{codecStatus}</Pill>
          {wasmReady && (
            <span className="text-[9px] text-[var(--t4)]">Décodeur HCV2 47Ko • Encodeur 58Ko</span>
          )}
        </div>

        {/* Fichiers sélectionnés */}
        {files.length > 0 && (
          <div className="mb-2">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[9.5px] tracking-[.1em] text-[var(--t4)] uppercase">
                {files.length} FICHIER{files.length > 1 ? 'S' : ''}
              </span>
              <span className="text-[11px] cursor-pointer text-[var(--t3)]" onClick={clearAll}>Tout effacer</span>
            </div>
            <div className="flex flex-col gap-1">
              {files.map((f, i) => (
                <div key={i} className="flex items-center gap-2 px-3 py-2"
                  style={{
                    borderRadius: 'var(--r-card, 10px)',
                    background: 'var(--g1)',
                    border: 'var(--bw, 0.5px) solid var(--b2)',
                  }}>
                  <span className="text-[13px]">📄</span>
                  <span className="flex-1 text-[11px] text-[var(--t2)] truncate">{f.name}</span>
                  <span className="text-[10px] text-[var(--t3)] tabular-nums">{formatSize(f.size)}</span>
                  <span className="text-[12px] cursor-pointer text-[var(--t4)]" onClick={() => removeFile(i)}>✕</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Quality selector */}
        <div className="mb-2 text-[9.5px] tracking-[.1em] text-[var(--t4)] uppercase">QUALITÉ</div>
        <div className="flex gap-[6px] justify-center mb-[10px] flex-wrap">
          {(['archive', 'standard', 'eco'] as Quality[]).map(q => {
            const labels = { archive: '📦 Archive', standard: '⭐ Standard', eco: '🌱 Éco' }
            const isActive = quality === q
            const descs = { archive: 'Max compression', standard: 'Équilibre', eco: 'Rapide' }
            return (
              <div key={q} className="flex flex-col items-center">
                <span
                  className={`inline-flex items-center px-[10px] py-[4px] text-[10.5px] font-medium cursor-pointer ${
                    isActive
                      ? q === 'eco'
                        ? 'bg-[rgba(240,149,149,0.12)] text-[var(--coral)]'
                        : 'bg-[var(--life-d)] text-[var(--life)]'
                      : 'bg-[var(--g1)] text-[var(--t3)]'
                  }`}
                  style={{
                    borderRadius: 'var(--r-pill, 20px)',
                    border: isActive
                      ? 'var(--bw, 0.5px) solid ' + (q === 'eco' ? 'rgba(240,149,149,0.3)' : 'var(--life-g)')
                      : 'var(--bw, 0.5px) solid var(--b2)',
                  }}
                  onClick={() => { setQuality(q); setResults([]) }}
                >
                  {labels[q]}
                </span>
                {isActive && (
                  <span className="text-[8px] text-[var(--t4)] mt-1">{descs[q]}</span>
                )}
              </div>
            )
          })}
        </div>

        {/* Upload zone */}
        <div
          className="border-2 border-dashed py-7 px-3 text-center cursor-pointer mb-3 transition-all hover:border-[var(--soul-g)]"
          style={{
            borderRadius: 'var(--r-card, 14px)',
            borderColor: files.length > 0 ? 'var(--soul-g)' : 'var(--b2)',
          }}
          onClick={() => fileInputRef.current?.click()}
        >
          <div className="text-[28px] mb-[6px]">📁</div>
          <div className="text-[13px] font-semibold text-[var(--t2)]">
            {files.length > 0 ? 'Ajouter des fichiers' : 'Choisir des fichiers'}
          </div>
          <div className="text-[11px] text-[var(--t4)] mt-[3px]">Photos · Vidéos · Documents</div>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          onChange={e => e.target.files && handleFiles(e.target.files)}
        />

        {/* Progression */}
        {optimizing && (
          <div className="mb-[14px]">
            <div className="flex justify-between mb-[6px]">
              <span className="text-[9.5px] tracking-[.1em] text-[var(--t4)] uppercase">COMPRESSION HCV2</span>
              <span className="text-[12px] text-[var(--t2)]">{progress}/{totalFiles}</span>
            </div>
            <div className="h-2 bg-[var(--g1)] overflow-hidden progress-bar"
              style={{ borderRadius: 'var(--r-card, 4px)' }}>
              <div
                className="h-full transition-all duration-300 progress-bar"
                style={{
                  width: (progress / totalFiles * 100) + '%',
                  borderRadius: 'var(--r-card, 4px)',
                  background: 'linear-gradient(90deg, var(--soul), var(--life))',
                }}
              />
            </div>
          </div>
        )}

        {/* Gauge des résultats */}
        {results.length > 0 && !optimizing && (
          <div className="mb-[14px] animate-[fu_0.3s_ease-out]">
            <div className="flex justify-between items-baseline mb-[6px]">
              <span className="text-[9.5px] tracking-[.1em] text-[var(--t4)] uppercase">GAIN TOTAL</span>
              <span className="text-[22px] font-bold text-[var(--life)]">{formatSize(totalSaved)}</span>
            </div>
            <div className="h-2 rounded-[4px] bg-[var(--g1)] overflow-hidden">
              <div
                className="h-full rounded-[4px] transition-all duration-500"
                style={{
                  width: Math.min(savingsPct, 100) + '%',
                  background: 'linear-gradient(90deg, var(--life), #6fcf97)',
                }}
              />
            </div>
            <div className="flex justify-between mt-1">
              <span className="text-[11px] text-[var(--t4)]">{formatSize(totalOrig)}</span>
              <span className="text-[11px] text-[var(--life)]">{formatSize(totalComp)}</span>
            </div>
          </div>
        )}

        {/* Résultats détaillés */}
        <div className="flex flex-col gap-2 mb-4">
          {results.map((r, i) => (
            <div key={i} className="p-3 bg-[var(--g1)] animate-[fu_0.25s_ease-out]"
              style={{
                borderRadius: 'var(--r-card, 14px)',
                border: 'var(--bw, 0.5px) solid var(--b2)',
                animationDelay: `${i * 50}ms`,
              }}>
              <div className="flex justify-between items-center">
                <div>
                  <div className="text-[12px] font-medium text-[var(--t1)]">{r.name}</div>
                  <div className="flex items-center gap-2 mt-[2px]">
                    <span className="text-[10px] text-[var(--t4)]">
                      {formatSize(r.origSize)} → {formatSize(r.compSize)}
                    </span>
                    <Pill color={r.method === 'wasm' ? 'soul' : r.method === 'server' ? 'life' : 'wisdom'} size="xs">
                      {r.method === 'wasm' ? 'WASM' : r.method === 'server' ? 'Serveur' : 'Estimé'}
                    </Pill>
                    {r.format && r.format !== 'unknown' && (
                      <span className="text-[8px] text-[var(--t4)]">{r.format}</span>
                    )}
                  </div>
                </div>
                <div className="text-[16px] font-bold text-[var(--life)]">-{r.ratio}%</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* CTA */}
      <div className="flex gap-2 px-5 pb-[calc(14px+var(--sb))] pt-[10px] shrink-0">
        <button
          onClick={handleOptimize}
          disabled={files.length === 0 || optimizing}
          className={`px-[13px] py-[13px] text-center text-[13px] font-normal tracking-[.02em] cursor-pointer transition-all active:scale-[.97] flex-1 ${
            files.length === 0 || optimizing ? 'opacity-50 pointer-events-none' : ''
          }`}
          style={{
            borderRadius: 'var(--r-button, 26px)',
            background: 'var(--life-d)',
            border: 'var(--bw, 0.5px) solid var(--life-g)',
            color: 'var(--life)',
          }}
        >
          {optimizing ? (
            <span className="flex items-center justify-center gap-2">
              <span className="w-3 h-3 rounded-full border-2 border-transparent border-t-[var(--life)] animate-spin" />
              Compression {progress}/{totalFiles}
            </span>
          ) : results.length > 0 ? (
            '▶ Recomprimer'
          ) : (
            '▶ Compresser (HCV2)'
          )}
        </button>
        <Button color="ghost" onClick={() => navigate('/')}>Fermer</Button>
      </div>
    </div>
  )
}