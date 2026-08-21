import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import SpaceHeader from '@/components/layout/SpaceHeader'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'

interface GalleryItem {
  url: string
  type: 'photo' | 'video'
  date: number
}

export default function CameraScreen() {
  const navigate = useNavigate()
  const [gallery, setGallery] = useState<GalleryItem[]>(() => {
    try {
      return JSON.parse(localStorage.getItem('ka_cam_gallery') || '[]')
    } catch { return [] }
  })
  const [mode, setMode] = useState<'photo' | 'video'>('photo')
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const [camActive, setCamActive] = useState(false)

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
        audio: mode === 'video',
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }
      setCamActive(true)
    } catch {
      alert('Caméra non disponible')
    }
  }

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop())
      streamRef.current = null
    }
    setCamActive(false)
  }

  const takePhoto = () => {
    if (!videoRef.current) return
    const canvas = document.createElement('canvas')
    canvas.width = videoRef.current.videoWidth
    canvas.height = videoRef.current.videoHeight
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.drawImage(videoRef.current, 0, 0)
    const url = canvas.toDataURL('image/jpeg', 0.9)
    const item: GalleryItem = { url, type: 'photo', date: Date.now() }
    const newGallery = [item, ...gallery].slice(0, 12)
    setGallery(newGallery)
    localStorage.setItem('ka_cam_gallery', JSON.stringify(newGallery))
  }

  const removeFromGallery = (index: number) => {
    const newGallery = gallery.filter((_, i) => i !== index)
    setGallery(newGallery)
    localStorage.setItem('ka_cam_gallery', JSON.stringify(newGallery))
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden min-h-0"
      style={{ background: '#000' }}>
      <div className="flex shrink-0 items-center justify-between px-[22px] pt-[14px]">
        <div
          className="cursor-pointer rounded-xl px-2 py-1 text-[13px] text-[var(--t3)] transition-colors active:bg-[var(--g2)]"
          onClick={() => { stopCamera(); navigate('/') }}
          role="button"
        >
          ‹ KA
        </div>
        <div className="text-[11px] tracking-[.08em] text-[var(--life)] opacity-65">KA CAMÉRA</div>
        <div style={{ width: '48px' }} />
      </div>

      <div className="flex-1 flex flex-col overflow-hidden min-h-0">
        {/* Camera view */}
        {camActive ? (
          <div className="relative flex-1 bg-black flex items-center justify-center">
            <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
            {/* Mode controls overlay */}
            <div className="absolute bottom-4 left-0 right-0 flex justify-center gap-4">
              <button
                onClick={takePhoto}
                className="w-16 h-16 rounded-full border-4 border-white flex items-center justify-center"
              >
                <div className="w-12 h-12 rounded-full bg-white" />
              </button>
            </div>
            <button
              onClick={stopCamera}
              className="absolute top-4 right-4 text-[12px] px-3 py-1 rounded-full bg-[rgba(255,255,255,0.2)] text-white"
            >
              ✕
            </button>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center gap-4 px-5">
            <div className="w-20 h-20 rounded-full bg-[var(--soul-d)] flex items-center justify-center text-3xl"
              style={{ border: '0.5px solid var(--soul-g)' }}>
              📷
            </div>
            <div className="text-[var(--t2)] text-center">
              <div className="text-[16px] font-medium">Caméra KA</div>
              <div className="text-[12px] text-[var(--t4)] mt-1">Photos et vidéos avec compression auto</div>
            </div>
            <button
              onClick={startCamera}
              className="rounded-[26px] px-8 py-3 text-[14px] font-medium cursor-pointer border-[0.5px]"
              style={{ background: 'var(--life-d)', borderColor: 'var(--life-g)', color: 'var(--life)' }}
            >
              📸 Ouvrir la caméra
            </button>
          </div>
        )}

        {/* Gallery */}
        {gallery.length > 0 && !camActive && (
          <div className="bg-[#000508] px-4 pb-4 pt-2">
            <div className="flex justify-between items-center mb-2">
              <span className="text-[9.5px] tracking-[.1em] text-[var(--t4)] uppercase">GALERIE</span>
              <span className="text-[10px] text-[var(--t4)]">{gallery.length} média{gallery.length > 1 ? 's' : ''}</span>
            </div>
            <div className="grid grid-cols-4 gap-[4px]">
              {gallery.map((item, i) => (
                <div key={i} className="relative aspect-square rounded-[6px] overflow-hidden cursor-pointer group"
                  onClick={() => removeFromGallery(i)}>
                  <img src={item.url} alt="" className="w-full h-full object-cover" />
                  <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                    <span className="text-white text-lg">✕</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}