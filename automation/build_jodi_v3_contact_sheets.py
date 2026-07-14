import json
from pathlib import Path
import av
from PIL import Image, ImageDraw

root = Path(r"C:\Youtube Automation Obsidian\Brody's Vault\2_IN_PRODUCTION\Jodi Huisentruit")
items = [x for x in json.loads((root / "Assembly" / "Pexels_Sourcing_v3.json").read_text())["assets"] if x["status"] == "matched"]
out = root / "Assembly"
for page, chunk_start in enumerate(range(0, len(items), 14), 1):
    chunk = items[chunk_start:chunk_start + 14]
    sheet = Image.new("RGB", (1280, 7 * 210), "#111111"); draw = ImageDraw.Draw(sheet)
    for n, item in enumerate(chunk):
        row, col = divmod(n, 2); x, y = col * 640, row * 210
        c = av.open(item["local_path"]); frame = next(c.decode(video=0)); c.close()
        image = frame.to_image().convert("RGB"); image.thumbnail((620, 180))
        sheet.paste(image, (x + 10, y + 22)); draw.text((x + 10, y + 4), f"{item['beat']:02d}  {item['name'][:48]}", fill="white")
    sheet.save(out / f"Pexels_Contact_Sheet_v3_{page:02d}.jpg", quality=88)
