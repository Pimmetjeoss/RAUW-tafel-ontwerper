# Next.js Integratiegids - RAUW Tafel Designer API

Deze gids laat zien hoe je de RAUW Tafel Designer API koppelt aan een bestaande Next.js React website.

---

## 📋 Overzicht

De API maakt het mogelijk om:
- Beschikbare tafelvormen, onderstellen en kleuren op te halen
- Preview afbeeldingen te tonen
- Custom tafels te genereren (met of zonder klant's eigen ruimtefoto)
- Gegenereerde resultaten op te halen

**API Base URL (local development):** `http://localhost:8000`
**API Base URL (production):** `https://jouw-api-domein.nl`

---

## 🚀 Stap 1: Start de API Server

```bash
# In de nano-banana-python directory
uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```

**Verifieer dat de API draait:**
```bash
curl http://localhost:8000/
```

---

## 🔧 Stap 2: Next.js Setup

### 2.1 Environment Variables

Maak of update `.env.local` in je Next.js project:

```bash
# .env.local
NEXT_PUBLIC_RAUW_API_URL=http://localhost:8000
# Voor productie:
# NEXT_PUBLIC_RAUW_API_URL=https://api.rauw.nl
```

### 2.2 API Client Utility

Maak `lib/rauw-api.ts` (of `.js` als je geen TypeScript gebruikt):

```typescript
// lib/rauw-api.ts

const API_BASE_URL = process.env.NEXT_PUBLIC_RAUW_API_URL || 'http://localhost:8000';

export interface CategoryResponse {
  category: string;
  images: string[];
  count: number;
}

export interface GenerateTableResponse {
  success: boolean;
  output_url: string;
  filename: string;
  message: string;
}

export interface GenerateTableRequest {
  vorm: string;
  onderstel: string;
  kleur: string;
  room_photo?: File;
}

/**
 * Health check - controleer of API beschikbaar is
 */
export async function checkApiHealth() {
  const response = await fetch(`${API_BASE_URL}/`);
  if (!response.ok) throw new Error('API not available');
  return response.json();
}

/**
 * Haal alle beschikbare afbeeldingen op voor een categorie
 * @param category - 'vorm', 'onderstel', of 'kleur'
 */
export async function getCategoryImages(category: 'vorm' | 'onderstel' | 'kleur'): Promise<CategoryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/categories/${category}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch ${category} images`);
  }

  return response.json();
}

/**
 * Bouw de URL voor een preview afbeelding
 * @param category - 'vorm', 'onderstel', of 'kleur'
 * @param filename - Bestandsnaam (bijv. 'rond.jpeg')
 */
export function getImageUrl(category: 'vorm' | 'onderstel' | 'kleur', filename: string): string {
  return `${API_BASE_URL}/api/images/${category}/${filename}`;
}

/**
 * Genereer een custom tafel
 * @param data - Vorm, onderstel, kleur en optioneel ruimtefoto
 */
export async function generateTable(data: GenerateTableRequest): Promise<GenerateTableResponse> {
  const formData = new FormData();
  formData.append('vorm', data.vorm);
  formData.append('onderstel', data.onderstel);
  formData.append('kleur', data.kleur);

  if (data.room_photo) {
    formData.append('room_photo', data.room_photo);
  }

  const response = await fetch(`${API_BASE_URL}/api/generate`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to generate table');
  }

  return response.json();
}

/**
 * Bouw de volledige URL voor een gegenereerde tafel
 * @param outputUrl - De output_url uit de generateTable response (bijv. '/api/output/remixed_image_...')
 */
export function getOutputImageUrl(outputUrl: string): string {
  return `${API_BASE_URL}${outputUrl}`;
}
```

---

## 🎨 Stap 3: React Components

### 3.1 Image Selector Component

Herbruikbare component voor het selecteren van vorm/onderstel/kleur:

```typescript
// components/ImageSelector.tsx
'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
import { getCategoryImages, getImageUrl } from '@/lib/rauw-api';

interface ImageSelectorProps {
  category: 'vorm' | 'onderstel' | 'kleur';
  label: string;
  selectedImage: string | null;
  onSelect: (filename: string) => void;
}

export default function ImageSelector({ category, label, selectedImage, onSelect }: ImageSelectorProps) {
  const [images, setImages] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadImages() {
      try {
        setLoading(true);
        const data = await getCategoryImages(category);
        setImages(data.images);
      } catch (err) {
        setError('Kon afbeeldingen niet laden');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    loadImages();
  }, [category]);

  if (loading) {
    return (
      <div className="space-y-2">
        <h3 className="font-semibold text-lg">{label}</h3>
        <p className="text-gray-500">Laden...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-2">
        <h3 className="font-semibold text-lg">{label}</h3>
        <p className="text-red-500">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="font-semibold text-lg">{label}</h3>
      <div className="grid grid-cols-3 gap-4">
        {images.map((filename) => {
          const isSelected = selectedImage === filename;
          return (
            <button
              key={filename}
              onClick={() => onSelect(filename)}
              className={`
                relative aspect-square rounded-lg overflow-hidden border-2 transition-all
                ${isSelected ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-200 hover:border-gray-400'}
              `}
            >
              <Image
                src={getImageUrl(category, filename)}
                alt={filename}
                fill
                className="object-cover"
              />
              {isSelected && (
                <div className="absolute top-2 right-2 bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center">
                  ✓
                </div>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
```

### 3.2 Room Photo Upload Component

```typescript
// components/RoomPhotoUpload.tsx
'use client';

import { useState, useRef } from 'react';
import Image from 'next/image';

interface RoomPhotoUploadProps {
  onPhotoChange: (file: File | null) => void;
}

export default function RoomPhotoUpload({ onPhotoChange }: RoomPhotoUploadProps) {
  const [preview, setPreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];

    if (!file) {
      setPreview(null);
      onPhotoChange(null);
      return;
    }

    // Validatie
    if (file.size > 10 * 1024 * 1024) {
      alert('Bestand is te groot. Maximum 10MB.');
      return;
    }

    if (!file.type.startsWith('image/')) {
      alert('Alleen afbeeldingen zijn toegestaan.');
      return;
    }

    // Preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setPreview(reader.result as string);
    };
    reader.readAsDataURL(file);

    onPhotoChange(file);
  };

  const handleRemove = () => {
    setPreview(null);
    onPhotoChange(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="space-y-4">
      <h3 className="font-semibold text-lg">Plaats tafel in uw eigen ruimte (optioneel)</h3>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm">
        <p className="font-semibold mb-2">💡 Tips voor beste resultaat:</p>
        <ul className="list-disc list-inside space-y-1 text-gray-700">
          <li>Goede belichting (natuurlijk licht)</li>
          <li>Lege vloerruimte zichtbaar</li>
          <li>Foto op ooghoogte</li>
          <li>Hogere resolutie = beter resultaat</li>
        </ul>
      </div>

      {!preview ? (
        <div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="hidden"
            id="room-photo-input"
          />
          <label
            htmlFor="room-photo-input"
            className="block w-full p-8 border-2 border-dashed border-gray-300 rounded-lg text-center cursor-pointer hover:border-gray-400 transition-colors"
          >
            <div className="text-gray-600">
              <svg className="mx-auto h-12 w-12 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <p className="font-semibold">Upload foto van uw ruimte</p>
              <p className="text-sm">of klik om te bladeren</p>
            </div>
          </label>
        </div>
      ) : (
        <div className="relative">
          <div className="relative aspect-video rounded-lg overflow-hidden">
            <Image
              src={preview}
              alt="Preview"
              fill
              className="object-cover"
            />
          </div>
          <button
            onClick={handleRemove}
            className="absolute top-2 right-2 bg-red-500 text-white rounded-full p-2 hover:bg-red-600 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
}
```

### 3.3 Hoofdcomponent - Table Designer

```typescript
// app/tafel-designer/page.tsx (of components/TableDesigner.tsx)
'use client';

import { useState } from 'react';
import Image from 'next/image';
import ImageSelector from '@/components/ImageSelector';
import RoomPhotoUpload from '@/components/RoomPhotoUpload';
import { generateTable, getOutputImageUrl, type GenerateTableResponse } from '@/lib/rauw-api';

export default function TableDesignerPage() {
  // Selecties
  const [vorm, setVorm] = useState<string | null>(null);
  const [onderstel, setOnderstel] = useState<string | null>(null);
  const [kleur, setKleur] = useState<string | null>(null);
  const [roomPhoto, setRoomPhoto] = useState<File | null>(null);

  // Generatie status
  const [isGenerating, setIsGenerating] = useState(false);
  const [result, setResult] = useState<GenerateTableResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const canGenerate = vorm && onderstel && kleur;

  const handleGenerate = async () => {
    if (!vorm || !onderstel || !kleur) return;

    try {
      setIsGenerating(true);
      setError(null);
      setResult(null);

      const response = await generateTable({
        vorm,
        onderstel,
        kleur,
        room_photo: roomPhoto || undefined,
      });

      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Er is iets misgegaan');
      console.error('Generation error:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleReset = () => {
    setVorm(null);
    setOnderstel(null);
    setKleur(null);
    setRoomPhoto(null);
    setResult(null);
    setError(null);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold mb-2">RAUW Tafel Designer</h1>
        <p className="text-gray-600">Ontwerp uw eigen custom tafel</p>
      </div>

      {/* Stap 1-3: Selecties */}
      <div className="space-y-8 mb-8">
        <ImageSelector
          category="vorm"
          label="Stap 1: Kies uw tafelvorm"
          selectedImage={vorm}
          onSelect={setVorm}
        />

        <ImageSelector
          category="onderstel"
          label="Stap 2: Kies uw onderstel"
          selectedImage={onderstel}
          onSelect={setOnderstel}
        />

        <ImageSelector
          category="kleur"
          label="Stap 3: Kies uw houtkleur"
          selectedImage={kleur}
          onSelect={setKleur}
        />

        <RoomPhotoUpload onPhotoChange={setRoomPhoto} />
      </div>

      {/* Generate knop */}
      <div className="flex justify-center mb-8">
        <button
          onClick={handleGenerate}
          disabled={!canGenerate || isGenerating}
          className={`
            px-8 py-4 rounded-lg font-semibold text-white text-lg transition-all
            ${canGenerate && !isGenerating
              ? 'bg-blue-600 hover:bg-blue-700 cursor-pointer'
              : 'bg-gray-300 cursor-not-allowed'
            }
          `}
        >
          {isGenerating ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Genereren... (10-20 seconden)
            </span>
          ) : (
            'Genereer mijn tafel'
          )}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-8">
          <p className="text-red-700 font-semibold">Fout bij genereren:</p>
          <p className="text-red-600">{error}</p>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="bg-white border border-gray-200 rounded-lg p-8 shadow-lg">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold mb-2">✨ Uw custom tafel</h2>
            <p className="text-gray-600">{result.message}</p>
          </div>

          <div className="relative aspect-video rounded-lg overflow-hidden mb-6">
            <Image
              src={getOutputImageUrl(result.output_url)}
              alt="Generated table"
              fill
              className="object-contain"
            />
          </div>

          <div className="flex gap-4 justify-center">
            <a
              href={getOutputImageUrl(result.output_url)}
              download={result.filename}
              className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-semibold transition-colors"
            >
              Download afbeelding
            </a>
            <button
              onClick={handleReset}
              className="px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-semibold transition-colors"
            >
              Nieuwe tafel ontwerpen
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## 🎯 Stap 4: Implementatie in bestaande website

### Optie A: Dedicated Page

Voeg een nieuwe route toe aan je Next.js app:

```typescript
// app/tafel-designer/page.tsx
import TableDesignerPage from '@/components/TableDesigner';

export default TableDesignerPage;
```

### Optie B: Modal/Dialog

Integreer de designer als modal in een bestaande pagina:

```typescript
// components/TableDesignerModal.tsx
'use client';

import { useState } from 'react';
import { Dialog } from '@headlessui/react'; // of jouw preferred modal library
import TableDesigner from '@/components/TableDesigner';

export default function TableDesignerModal() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
      >
        Ontwerp je tafel
      </button>

      <Dialog open={isOpen} onClose={() => setIsOpen(false)}>
        <div className="fixed inset-0 bg-black/30" aria-hidden="true" />
        <div className="fixed inset-0 flex items-center justify-center p-4">
          <Dialog.Panel className="bg-white rounded-lg max-w-7xl w-full max-h-[90vh] overflow-y-auto">
            <TableDesigner />
          </Dialog.Panel>
        </div>
      </Dialog>
    </>
  );
}
```

---

## 🔒 Stap 5: Productie Setup

### 5.1 CORS Configuratie

Update `src/api.py` in de Python backend met je productie domein:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.rauw.nl",
        "https://rauw.nl",
        "http://localhost:3000"  # Voor development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 5.2 Environment Variables (Productie)

```bash
# .env.production
NEXT_PUBLIC_RAUW_API_URL=https://api.rauw.nl
```

### 5.3 API Deployment

Deploy de FastAPI backend naar een server (bijv. DigitalOcean, AWS, Railway):

```bash
# Production start command
uvicorn src.api:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 📊 Rate Limits

Let op deze limits bij het bouwen van je UI:

| Endpoint | Limit | Actie |
|----------|-------|-------|
| `GET /api/categories/*` | 30/min | Toon melding als limiet bereikt |
| `GET /api/images/*` | 60/min | Cache preview afbeeldingen |
| `POST /api/generate` | **5/uur** | Disable knop na 5 generaties |

### Rate Limit Handling

```typescript
// lib/rauw-api.ts
export class RateLimitError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'RateLimitError';
  }
}

export async function generateTable(data: GenerateTableRequest): Promise<GenerateTableResponse> {
  const formData = new FormData();
  // ... (rest of implementation)

  const response = await fetch(`${API_BASE_URL}/api/generate`, {
    method: 'POST',
    body: formData,
  });

  if (response.status === 429) {
    throw new RateLimitError('Te veel aanvragen. Probeer het over een uur opnieuw.');
  }

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to generate table');
  }

  return response.json();
}
```

---

## 🧪 Testing

### Test de integratie:

```bash
# 1. Start de API
cd nano-banana-python
uvicorn src.api:app --reload

# 2. Start Next.js (in andere terminal)
cd jouw-nextjs-project
npm run dev

# 3. Open browser
# http://localhost:3000/tafel-designer
```

### Test checklist:

- [ ] Preview afbeeldingen laden correct
- [ ] Selecties werken (vorm/onderstel/kleur)
- [ ] Room photo upload werkt (optioneel)
- [ ] Generatie duurt 10-20 seconden
- [ ] Resultaat wordt getoond
- [ ] Download werkt
- [ ] Error handling werkt (bij ongeldige input)
- [ ] Rate limiting wordt gerespecteerd

---

## 🎨 Styling Aanpassingen

De voorbeeldcode gebruikt Tailwind CSS. Pas het aan aan jouw design system:

```typescript
// Voorbeeld met CSS Modules
import styles from './TableDesigner.module.css';

<button className={styles.generateButton}>
  Genereer tafel
</button>
```

Of met styled-components/emotion:

```typescript
import styled from 'styled-components';

const GenerateButton = styled.button`
  background: ${props => props.theme.colors.primary};
  padding: 1rem 2rem;
  border-radius: 8px;
  // ...
`;
```

---

## 🐛 Troubleshooting

### CORS errors

**Probleem:** `Access to fetch at 'http://localhost:8000' has been blocked by CORS policy`

**Oplossing:**
1. Check of API draait: `curl http://localhost:8000/`
2. Verifieer CORS origins in `src/api.py`
3. Restart API server na wijzigingen

### Afbeeldingen laden niet

**Probleem:** Preview afbeeldingen tonen niet

**Oplossing:**
1. Check `next.config.js`:
```javascript
module.exports = {
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
        pathname: '/api/**',
      },
    ],
  },
};
```

### Generatie faalt

**Probleem:** "Generation failed: GEMINI_API_KEY not configured"

**Oplossing:**
1. Check `.env` in Python project
2. Restart API server

---

## 📞 Support

- **API Docs:** http://localhost:8000/docs (tijdens development)
- **GitHub:** https://github.com/Pimmetjeoss/RAUW-tafel-ontwerper
- **Response times:** Generatie duurt 10-20 seconden (normaal!)

---

## ✅ Checklist voor Go-Live

- [ ] Environment variables ingesteld (productie)
- [ ] CORS geconfigureerd voor productie domein
- [ ] API gedeployed en bereikbaar
- [ ] Rate limiting getest
- [ ] Error handling geïmplementeerd
- [ ] Loading states toegevoegd
- [ ] Mobile responsive getest
- [ ] Image optimization (Next.js)
- [ ] Analytics tracking toegevoegd (optioneel)
- [ ] Backup/monitoring voor API server

---

Veel succes met de integratie! 🚀
