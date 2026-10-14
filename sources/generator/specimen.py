"""Render documentation/specimen.png and documentation/article/sutra-mono-code.png from the built fonts."""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
TTF = lambda w: os.path.join(ROOT, 'fonts', 'ttf', f'SutraMono-{w}.ttf')
PAPER, INK, MUTED, BLUE = (241, 243, 242), (22, 33, 42), (94, 107, 114), (30, 92, 115)
NIGHT, NFG, NMUTED, NBLUE, NWARM = (18, 27, 33), (220, 228, 231), (125, 142, 150), (116, 182, 203), (217, 185, 140)


def specimen(path):
    W, H = 2400, 1500
    im = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(im)
    f = lambda w, s: ImageFont.truetype(TTF(w), s)
    d.text((120, 110), 'Sutra Mono', font=f('Regular', 190), fill=INK)
    d.text((124, 330), 'a monospace drawn as a single thread', font=f('Light', 52), fill=MUTED)
    rows = [('Light', 'abcdefghijklmnopqrstuvwxyz'), ('Regular', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
            ('Bold', '0123456789 {}[]() <=> #$%&@')]
    y = 520
    for w, s in rows:
        d.text((120, y), s, font=f(w, 96), fill=INK)
        d.text((W - 300, y + 40), w.lower(), font=f('Regular', 36), fill=MUTED)
        y += 170
    d.text((120, y + 40), 'fold = alg ∘ fmap (fold alg) ∘ unfix', font=f('Regular', 88), fill=BLUE)
    d.text((120, y + 190), 'Ærøskøbing  Łódź  Șișli  İstanbul  straße  0O Il1|', font=f('Regular', 64), fill=INK)
    im.save(path)


def code(path):
    W, H = 2400, 1260
    im = Image.new('RGB', (W, H), NIGHT)
    d = ImageDraw.Draw(im)
    F = ImageFont.truetype(TTF('Regular'), 54)
    lines = [
        [(NMUTED, '-- ad format spec ⇒ deterministic Moore machine')],
        [(NBLUE, 'compile '), (NMUTED, '= '), (NFG, 'emit ∘ minimise ∘ determinise ∘ parse')],
        [],
        [(NBLUE, 'fold '), (NMUTED, ':: '), (NWARM, '(F a → a) → Fix F → a')],
        [(NBLUE, 'fold alg '), (NMUTED, '= '), (NFG, 'alg ∘ fmap (fold alg) ∘ unfix')],
        [],
        [(NBLUE, 'const '), (NFG, 'step '), (NMUTED, '= '), (NFG, '(s: State, e: Event): State =>')],
        [(NFG, '  s.on[e.kind]?.(e) ?? s;   '), (NMUTED, '// total, never throws')],
        [],
        [(NBLUE, 'if '), (NFG, '(bid >= floor && fill != 0) { render('), (NWARM, '"banner"'), (NFG, ') }')],
        [(NMUTED, '// 0O o Il1| {}[]() #$%&@ → ← ↦ ⊗ ⊕ ⊥ ⊤ ∈ ≅ ¬')],
    ]
    y = 110
    for i, ln in enumerate(lines):
        d.text((90, y), f'{i + 1:>2}', font=F, fill=(58, 75, 84))
        x = 260
        for col, s in ln:
            d.text((x, y), s, font=F, fill=col)
            x += F.getlength(s)
        y += 94
    im.save(path)


if __name__ == '__main__':
    os.makedirs(os.path.join(ROOT, 'documentation', 'article'), exist_ok=True)
    specimen(os.path.join(ROOT, 'documentation', 'specimen.png'))
    code(os.path.join(ROOT, 'documentation', 'article', 'sutra-mono-code.png'))
    specimen(os.path.join(ROOT, 'documentation', 'article', 'sutra-mono-specimen.png'))
    print('specimens written')
