# RAUW Tafel Ontwerper

Een AI-powered tafel designer die custom tafels visualiseert door tafelvorm, onderstel en houtafwerking te combineren met Google Gemini Flash Image.

## Features

- 🌐 **REST API** voor integratie met externe websites
- 🤖 **AI-gebaseerde beeldcombinatie** met Google Gemini 2.5 Flash Image
- 🏠 **Ruimte visualisatie** - Plaats gegenereerde tafel in eigen woon-/eetkamer
- ⚡ **CLI mode** - Interactief of command-line gebruik
- 📚 **Auto-documentatie** - OpenAPI docs op `/docs`

## Vereisten

- Python 3.10+
- Google Gemini API key ([verkrijg hier](https://ai.google.dev/))
- uv (aanbevolen) of pip

## Installatie

```bash
# Clone de repository
git clone https://github.com/Pimmetjeoss/RAUW-tafel-ontwerper.git
cd RAUW-tafel-ontwerper

# Installeer dependencies
uv sync

# Maak .env bestand met API key
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

## Gebruik

### 🌐 Web API (voor externe websites)

**Start de server:**
```bash
# Development mode (met auto-reload)
uvicorn src.api:app --reload --host 0.0.0.0 --port 8000

# Of met Python direct
python src/api.py
```

**API beschikbaar op:** http://localhost:8000
- **Interactive docs:** http://localhost:8000/docs
- **Alternative docs:** http://localhost:8000/redoc

---

### 📋 API Endpoints

#### 1. Health Check
```bash
GET /
```
**Response:**
```json
{
  "name": "RAUW Tafel Designer API",
  "status": "operational",
  "docs": "/docs"
}
```

#### 2. List Available Images
```bash
GET /api/categories/{category}
```
**Parameters:**
- `category`: `vorm`, `onderstel`, of `kleur`

**Response:**
```json
{
  "category": "vorm",
  "images": ["rechthoek.jpeg", "rond.jpeg", "speciaal.jpeg"],
  "count": 3
}
```

#### 3. Get Preview Image
```bash
GET /api/images/{category}/{filename}
```
**Example:** `GET /api/images/vorm/rond.jpeg`

Returns: Image file

#### 4. Generate Custom Table
```bash
POST /api/generate
Content-Type: multipart/form-data
```

**Form Parameters:**
- `vorm` (string, required): Filename van tafelvorm (bijv. "rond.jpeg")
- `onderstel` (string, required): Filename van onderstel (bijv. "x_onderstel.jpeg")
- `kleur` (string, required): Filename van houtkleur (bijv. "eiken_donker.jpg")
- `room_photo` (file, optional): Upload foto van eigen ruimte

**Response:**
```json
{
  "success": true,
  "output_url": "/api/output/remixed_image_1759863020_0.png",
  "filename": "remixed_image_1759863020_0.png",
  "message": "Table generated successfully"
}
```

**cURL Voorbeeld:**
```bash
# Zonder ruimtefoto (standaard showroom)
curl -X POST http://localhost:8000/api/generate \
  -F "vorm=rond.jpeg" \
  -F "onderstel=x_onderstel.jpeg" \
  -F "kleur=eiken_donker.jpg"

# Met eigen ruimtefoto
curl -X POST http://localhost:8000/api/generate \
  -F "vorm=rond.jpeg" \
  -F "onderstel=x_onderstel.jpeg" \
  -F "kleur=eiken_donker.jpg" \
  -F "room_photo=@/pad/naar/mijn_woonkamer.jpg"
```

**JavaScript Voorbeeld:**
```javascript
const formData = new FormData();
formData.append('vorm', 'rond.jpeg');
formData.append('onderstel', 'x_onderstel.jpeg');
formData.append('kleur', 'eiken_donker.jpg');

// Optioneel: eigen ruimtefoto
const roomPhoto = document.querySelector('#roomPhotoInput').files[0];
if (roomPhoto) {
  formData.append('room_photo', roomPhoto);
}

const response = await fetch('http://localhost:8000/api/generate', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log(result.output_url); // "/api/output/remixed_image_..."
```

#### 5. Get Generated Table Image
```bash
GET /api/output/{filename}
```
**Example:** `GET /api/output/remixed_image_1759863020_0.png`

Returns: Generated table image (PNG)

---

### ⚙️ CORS Configuration

CORS is standaard enabled voor alle origins. **Configureer dit in productie:**

```python
# src/api.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://jouwwebsite.nl"],  # Specifieke origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

---

### 🖥️ CLI Mode (Interactief)

```bash
python src/mix_images.py
```

**Stappen:**
1. Kies tafelvorm (vorm/)
2. Kies onderstel (onderstel/)
3. Kies houtkleur (kleur/)
4. **Optioneel:** Upload ruimtefoto voor visualisatie in eigen ruimte

**Tips voor ruimtefoto:**
- ✓ Goede belichting (natuurlijk licht)
- ✓ Lege vloerruimte zichtbaar
- ✓ Foto op ooghoogte
- ✓ Hogere resolutie = beter resultaat
- ✓ Rechte hoek > schuine hoek

---

### 🔧 CLI Mode (Command-line)

```bash
# Standaard tafel (3 componenten)
python src/mix_images.py \
  -i vorm/rond.jpeg \
  -i onderstel/x_onderstel.jpeg \
  -i kleur/eiken_donker.jpg

# Tafel in eigen ruimte (4 componenten)
python src/mix_images.py \
  -i vorm/rond.jpeg \
  -i onderstel/x_onderstel.jpeg \
  -i kleur/eiken_donker.jpg \
  -r mijn_woonkamer.jpg

# Eén afbeelding verbeteren (studio quality)
python src/mix_images.py -i input/tafel.jpg

# Custom prompt
python src/mix_images.py \
  -i image1.jpg \
  -i image2.jpg \
  --prompt "Combine elegantly with modern lighting"

# Custom output directory
python src/mix_images.py -i image1.jpg --output-dir results/
```

---

## 📁 Structuur

```
.
├── src/
│   ├── api.py           # FastAPI REST API (190 regels)
│   └── mix_images.py    # Core AI logic + CLI (247 regels)
├── vorm/                # 3 tafelvormen (rechthoek, rond, speciaal)
├── onderstel/           # 3 onderstellen (2x simpel, midden, x-onderstel)
├── kleur/               # 3 houtafwerkingen (eiken donker/blad, visgraat)
├── output/              # Gegenereerde resultaten (auto-created)
├── .env                 # API key configuratie (NIET in git)
└── pyproject.toml       # Dependencies
```

**Beschikbare combinaties:** 27 (3 × 3 × 3) + optionele ruimte-integratie

---

## 🧪 Testing

**Test de API met Swagger UI:**
1. Start server: `uvicorn src.api:app --reload`
2. Open browser: http://localhost:8000/docs
3. Test endpoints interactief

**Test met cURL:**
```bash
# Health check
curl http://localhost:8000/

# List vormen
curl http://localhost:8000/api/categories/vorm

# Generate tafel
curl -X POST http://localhost:8000/api/generate \
  -F "vorm=rond.jpeg" \
  -F "onderstel=x_onderstel.jpeg" \
  -F "kleur=eiken_donker.jpg"
```

**Run unit tests:**
```bash
uv run pytest tests/
```

---

## 🚀 Deployment

**Development:**
```bash
uvicorn src.api:app --reload --host 127.0.0.1 --port 8000
```

**Production:**
```bash
uvicorn src.api:app --host 0.0.0.0 --port 8000 --workers 4
```

**Docker (optioneel):**
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync
ENV GEMINI_API_KEY=your_key_here
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🔐 Security

- **API Key:** Bewaar `GEMINI_API_KEY` in `.env` (nooit committen!)
- **CORS:** Configureer `allow_origins` voor productie
- **Rate Limiting:** Overweeg rate limiting voor productie API
- **File Upload:** Max file size is niet gelimiteerd (voeg toe indien nodig)

---

## 📊 API Response Times

| Endpoint | Avg Response Time |
|----------|-------------------|
| `GET /api/categories/*` | ~10ms |
| `GET /api/images/*` | ~50ms (image serving) |
| `POST /api/generate` | ~10-20s (Gemini AI processing) |
| `GET /api/output/*` | ~100ms (2-3MB PNG) |

---

## 🐛 Troubleshooting

**"ModuleNotFoundError: No module named 'mix_images'"**
```bash
# Zorg dat src/__init__.py bestaat
touch src/__init__.py
```

**"GEMINI_API_KEY not configured"**
```bash
# Check .env bestand
cat .env
# Moet bevatten: GEMINI_API_KEY=your_key_here
```

**CORS errors in browser:**
```python
# Voeg jouw frontend domain toe in src/api.py
allow_origins=["https://jouwwebsite.nl"]
```

---

## 📝 Licentie

MIT License - zie [LICENSE](LICENSE)

---

## 🤝 Contributing

1. Fork het project
2. Maak feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push naar branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📧 Contact

Pim - [@Pimmetjeoss](https://github.com/Pimmetjeoss)

Project Link: [https://github.com/Pimmetjeoss/RAUW-tafel-ontwerper](https://github.com/Pimmetjeoss/RAUW-tafel-ontwerper)
