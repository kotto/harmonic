Architecture KA Phone
src/

├─ app/
│  ├─ page.tsx
│  ├─ layout.tsx
│
├─ components/
│  ├─ CoreOrb.tsx
│  ├─ NeuralRing.tsx
│  ├─ GlyphNode.tsx
│  ├─ PromptBar.tsx
│  ├─ Greeting.tsx
│  ├─ KeyboardClassic.tsx
│  ├─ KeyboardGlyph.tsx
│
├─ features/
│  ├─ intent-engine/
│  │   ├─ store.ts
│  │   ├─ intents.ts
│
├─ shaders/
│  ├─ orbVertex.glsl
│  ├─ orbFragment.glsl
│
├─ store/
│  ├─ useKAStore.ts
│
├─ styles/
│  ├─ globals.css
│
└─ types/
Dépendances
npm install

framer-motion

zustand

three

@react-three/fiber

@react-three/drei

tailwindcss

clsx

lucide-react
1. Page principale

app/page.tsx

import HomeScreen from "@/components/HomeScreen";

export default function Page() {
  return <HomeScreen />;
}
2. HomeScreen
"use client";

import Greeting from "./Greeting";
import CoreOrb from "./CoreOrb";
import NeuralRing from "./NeuralRing";
import PromptBar from "./PromptBar";

export default function HomeScreen() {
  return (
    <main className="relative h-screen overflow-hidden bg-[#020818]">

      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(88,165,255,.25),transparent_45%)]"/>

      <Greeting />

      <CoreOrb />

      <NeuralRing />

      <PromptBar />

    </main>
  );
}
3. Sphère IA

components/CoreOrb.tsx

"use client";

import { Canvas } from "@react-three/fiber";
import { Float } from "@react-three/drei";

function Orb() {
  return (
    <Float
      speed={2}
      rotationIntensity={1}
      floatIntensity={1}
    >
      <mesh>

        <sphereGeometry
          args={[1.2,128,128]}
        />

        <meshPhysicalMaterial
          color="#5bc0ff"
          emissive="#7d5cff"
          emissiveIntensity={1}
          roughness={0.05}
          transmission={1}
          thickness={1.5}
        />

      </mesh>
    </Float>
  );
}

export default function CoreOrb() {
  return (
    <div
      className="
      absolute
      left-1/2
      top-[48%]
      -translate-x-1/2
      -translate-y-1/2
      h-[320px]
      w-[320px]
      "
    >
      <Canvas>

        <ambientLight intensity={1} />

        <pointLight
          position={[5,5,5]}
          intensity={10}
        />

        <Orb />

      </Canvas>
    </div>
  );
}
4. Neural Ring
"use client";

import { motion } from "framer-motion";

const glyphs = [
  "✦",
  "◈",
  "◌",
  "◎",
  "△",
  "⬢",
];

export default function NeuralRing() {

  return (
    <div
      className="
      absolute
      left-1/2
      top-[48%]
      h-[540px]
      w-[540px]
      -translate-x-1/2
      -translate-y-1/2
      "
    >
      {glyphs.map((g,index)=>{

        const angle =
          (index/glyphs.length)
          *Math.PI*2;

        const radius = 250;

        const x =
          Math.cos(angle)*radius;

        const y =
          Math.sin(angle)*radius;

        return (

          <motion.button

            whileHover={{
              scale:1.2
            }}

            key={g}

            className="
            absolute
            h-20
            w-20
            rounded-full
            border
            border-cyan-500/30
            bg-white/5
            backdrop-blur-xl
            text-3xl
            "

            style={{
              left:`calc(50% + ${x}px - 40px)`,
              top:`calc(50% + ${y}px - 40px)`
            }}
          >
            {g}
          </motion.button>

        );
      })}
    </div>
  );
}
5. Greeting
export default function Greeting() {

  return (

    <section
      className="
      pt-24
      text-center
      "
    >
      <h1
        className="
        text-6xl
        font-light
        "
      >
        Bonjour Alexandre
      </h1>

      <p
        className="
        mt-4
        text-2xl
        text-white/60
        "
      >
        Que puis-je faire pour toi ?
      </p>
    </section>

  );
}
6. Prompt Bar
"use client";

import { Sparkles } from "lucide-react";

export default function PromptBar() {

  return (

    <div
      className="
      absolute
      bottom-8
      left-1/2
      flex
      h-24
      w-[90%]
      max-w-4xl
      -translate-x-1/2
      items-center
      rounded-full
      border
      border-violet-500/30
      bg-white/5
      px-8
      backdrop-blur-xl
      "
    >
      <Sparkles />

      <input

        placeholder="Exprime ton intention..."

        className="
        ml-4
        flex-1
        bg-transparent
        outline-none
        "
      />

      <div
        className="
        h-16
        w-16
        rounded-full
        bg-gradient-to-r
        from-cyan-400
        to-violet-500
        "
      />
    </div>
  );
}
Étape suivante

Pour obtenir un rendu vraiment proche de tes maquettes, il faudrait ensuite ajouter :

Shader GLSL liquide dans la sphère.
Anneau orbital rotatif au doigt.
Intent Engine Zustand.
Navigation Home → Créer → Texte → Image.
Clavier hybride Glyphes + AZERTY.
Effets VisionOS (verre, profondeur, parallaxe).
Mode Apple Vision Pro avec profondeur 3D réelle.
PWA installable sur iPhone et Android.