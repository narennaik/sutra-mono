"""Render the 1600×900 social image (X / LinkedIn) from the built fonts. Output path is argv[1]."""
import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'documentation', 'social.png')
W, H = 3200, 1800
PAPER, INK, MUTED, BLUE, RULE = (241, 243, 242), (22, 33, 42), (94, 107, 114), (30, 92, 115), (214, 220, 221)
NIGHT, NFG, NM, NB, NW = (18, 27, 33), (220, 228, 231), (125, 142, 150), (116, 182, 203), (217, 185, 140)
F = lambda w, s: ImageFont.truetype(os.path.join(ROOT, 'fonts', 'ttf', f'SutraMono-{w}.ttf'), s)
im = Image.new('RGB', (W, H), PAPER); d = ImageDraw.Draw(im)
d.text((180, 210), '3 weights  ·  358 glyphs  ·  free', font=F('Regular', 46), fill=MUTED)
big = F('Regular', 330)
d.text((160, 330), 'Sutra', font=big, fill=INK); d.text((160, 680), 'Mono', font=big, fill=BLUE)
d.text((180, 1080), 'a typeface for code,\ndrawn as a single thread', font=F('Light', 72), fill=INK, spacing=26)
d.text((180, 1330), '0O Il1|  →  ⇒  ∘  λ  ≡', font=F('Regular', 86), fill=INK)
d.line((180, 1540, 1480, 1540), fill=RULE, width=4)
d.text((180, 1580), 'narennaik.github.io/sutra-mono', font=F('Regular', 52), fill=BLUE)
x0, y0, x1, y1 = 1640, 330, 3040, 1450
sh = Image.new('L', (W, H), 0); ImageDraw.Draw(sh).rounded_rectangle((x0 + 10, y0 + 40, x1 + 10, y1 + 40), 40, fill=110)
im.paste((20, 30, 36), (0, 0), sh.filter(ImageFilter.GaussianBlur(50)))
d = ImageDraw.Draw(im); d.rounded_rectangle((x0, y0, x1, y1), 40, fill=NIGHT)
for i, c in enumerate([(232, 106, 94), (232, 190, 90), (120, 190, 120)]):
    d.ellipse((x0 + 60 + i * 58, y0 + 56, x0 + 92 + i * 58, y0 + 88), fill=c)
d.text((x0 + 260, y0 + 50), 'compile.hs', font=F('Regular', 40), fill=NM)
cf = F('Regular', 50)
lines = [[(NM, '-- spec ⇒ Moore machine')], [(NB, 'compile '), (NM, '= '), (NFG, 'emit ∘ minimise')],
         [(NFG, '        ∘ determinise ∘ parse')], [],
         [(NB, 'fold '), (NM, ':: '), (NW, '(F a → a) → Fix F → a')], [(NB, 'fold alg '), (NM, '= '), (NFG, 'alg ∘ fmap (fold alg)')],
         [(NFG, '             ∘ unfix')], [],
         [(NB, 'step '), (NM, '= '), (NFG, 'λs e. s.on[e] ?? s')], [(NM, '-- ∀ f g h. (f∘g)∘h ≡ f∘(g∘h)')],
         [(NFG, '0O Il1| {}[]() #$%&@ ≠ ≤ ≥')]]
y = y0 + 170
for ln in lines:
    x = x0 + 80
    for col, s in ln:
        d.text((x, y), s, font=cf, fill=col); x += cf.getlength(s)
    y += 84
im.resize((1600, 900), Image.LANCZOS).save(out, optimize=True)
print(out)
