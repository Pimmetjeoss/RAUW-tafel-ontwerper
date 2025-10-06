# RAUW Tafel Ontwerper

Een interactieve tafel designer die AI gebruikt om custom tafels te visualiseren door tafelvorm, onderstel en houtafwerking te combineren.

## Features

- ✨ Interactieve tafel designer met 4 stappen (vorm, onderstel, kleur, ruimte)
- 🏠 **NIEUW!** Visualiseer de tafel in jouw eigen woon- of eetkamer
- 🤖 AI-gebaseerde beeldcombinatie met Google Gemini Flash Image
- ⚡ CLI mode voor algemeen gebruik met 1-5 afbeeldingen

## Vereisten

- Python 3.10+
- Google Gemini API key

## Installatie

```bash
# Clone de repository
git clone https://github.com/Pimmetjeoss/RAUW-tafel-ontwerper.git
cd RAUW-tafel-ontwerper

# Installeer dependencies met uv
uv sync

# Of met pip
pip install -r requirements.txt

# Maak een .env bestand met je API key
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

## Gebruik

### Interactieve Tafel Designer

```bash
python src/mix_images.py
```

Dit start de interactieve mode waar je kunt kiezen uit:
1. Tafelvorm (vorm/)
2. Onderstel (onderstel/)
3. Houtkleur/afwerking (kleur/)
4. **NIEUW!** Plaats tafel in jouw eigen ruimte (optioneel)

### ✨ Tafel in Jouw Eigen Ruimte (NIEUW!)

Visualiseer hoe jouw custom tafel eruit ziet in jouw eigen woon- of eetkamer!

**Interactieve Mode:**
```bash
python src/mix_images.py
# Volg de stappen en upload bij stap 4 je ruimtefoto
```

**CLI Mode met eigen ruimte:**
```bash
python src/mix_images.py -i vorm/rond.jpeg -i onderstel/x_onderstel.jpeg -i kleur/eiken_donker.jpg -r mijn_woonkamer.jpg
```

**Tips voor beste resultaat:**
- ✓ Gebruik goede belichting (natuurlijk licht of goede verlichting)
- ✓ Zorg dat er lege vloerruimte zichtbaar is waar de tafel kan staan
- ✓ Neem de foto op ooghoogte
- ✓ Hogere resolutie = beter resultaat
- ✓ Rechte hoek geeft beter perspectief dan schuine hoeken

### CLI Mode

```bash
# Eén afbeelding verbeteren
python src/mix_images.py -i input/image.jpg

# Meerdere afbeeldingen combineren
python src/mix_images.py -i image1.jpg -i image2.jpg -i image3.jpg

# Met custom prompt
python src/mix_images.py -i image1.jpg -i image2.jpg --prompt "Combine these elegantly"

# Custom output directory
python src/mix_images.py -i image1.jpg --output-dir my_output
```

## Structuur

```
vorm/           # Tafelvormen (rond, rechthoekig, etc.)
onderstel/      # Onderstellen (kruispoot, spinpoot, etc.)
kleur/          # Houtafwerkingen (eiken, walnoot, etc.)
output/         # Gegenereerde resultaten
src/
    mix_images.py  # Hoofdapplicatie
```

## Licentie

MIT
