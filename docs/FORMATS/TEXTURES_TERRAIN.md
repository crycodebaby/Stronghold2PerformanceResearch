# Textures & terrain

## Textures
| Format | Count | Notes | Status |
|---|---|---|---|
| DDS DXT1 | 937 | | [verifiziert] |
| DDS DXT3 | 806 | | [verifiziert] |
| DDS uncompressed 32bpp | 143 | | [verifiziert] |
| DDS DXT5 | 5 | | [verifiziert] |
| DDS 8bpp | 1 | | [verifiziert] |
| TGA RLE 32bpp / raw 32bpp / RLE 24 / raw 24 | 135 / 84 / 6 / 2 | | [verifiziert] |
| PNG, JPG, BMP | 1,078 / 193 / 283 | UI, crests, help | [verifiziert] count |

All standard formats → readable with any DDS/TGA tool (texconv, GIMP, Pillow).

## Terrain
- `terrain/*.dds`: tiling ground textures (grass, mud, sand, rock, marsh…) + `cliff_face_normalmap.DDS`. [verifiziert]
- `terrain/river/`: water textures + Bink videos (`moat.bik`, `sea.bik`, `river_full_.bik`, `waterfall_0.bik`) → animated water via Bink. [verifiziert files]
- `landtex.txt`: maps ground slots (`GROUND1` …) to texture names + flags (`R`, `4`, `R4`) with comments (`// MOUNTAIN`). Flags meaning unknown. [verifiziert content; flags Hypothese]
- `TextureMixer.dll`: terrain texture blending at runtime. [Hypothese, from name]
- Heightmap: inside map body (S2M stream 3). [Hypothese]
