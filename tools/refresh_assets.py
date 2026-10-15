"""Regenerate every derived asset from the built fonts: specimen images, design-doc PDF and page
images, README images, webfonts, social preview and download zip. Run after `make build`."""
import glob, os, shutil, subprocess, sys, zipfile
from PIL import Image, ImageFilter, ImageDraw
from fontTools.ttLib import TTFont

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.chdir(ROOT)
py = sys.executable
subprocess.run([py, 'sources/generator/specimen.py'], check=True)
subprocess.run([py, 'documentation/design-doc/make_doc.py'], check=True)
subprocess.run(['pdftoppm', '-r', '110', '-png', 'documentation/design-doc/Sutra-Mono-Design-Document.pdf', 'docs/pages/page'], check=True)
for p in sorted(glob.glob('docs/pages/page-*.png')):
    Image.open(p).convert('RGB').save(p.replace('.png', '.jpg'), quality=86, optimize=True, progressive=True)
    os.remove(p)
pages = [Image.open(p).convert('RGB') for p in sorted(glob.glob('docs/pages/page-*.jpg'))]
BG = (228, 232, 231)

def shadowed(canvas, im, x, y, blur=22, off=14, alpha=70):
    sh = Image.new('L', (im.width + blur * 4, im.height + blur * 4), 0)
    ImageDraw.Draw(sh).rectangle([blur * 2, blur * 2, blur * 2 + im.width, blur * 2 + im.height], fill=alpha)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    canvas.paste(Image.new('RGB', sh.size, (30, 40, 46)), (x - blur * 2 + off // 3, y - blur * 2 + off), sh)
    canvas.paste(im, (x, y))

pw = 620; ph = int(pages[0].height * pw / pages[0].width)
hero = Image.new('RGB', (3 * pw + 4 * 70, ph + 160), BG)
for i, im in enumerate([pages[0], pages[5], pages[8]]):
    shadowed(hero, im.resize((pw, ph), Image.LANCZOS), 70 + i * (pw + 70), 70)
hero.save('documentation/readme/design-doc-spread.jpg', quality=88, optimize=True, progressive=True)
tw = 300; th = int(pages[0].height * tw / pages[0].width); cols = 6; gap = 34
sheet = Image.new('RGB', (cols * tw + (cols + 1) * gap, 2 * th + 3 * gap), BG)
for i, im in enumerate(pages):
    r, c = divmod(i, cols)
    shadowed(sheet, im.resize((tw, th), Image.LANCZOS), gap + c * (tw + gap), gap + r * (th + gap), blur=10, off=6, alpha=60)
sheet.save('documentation/readme/design-doc-pages.jpg', quality=86, optimize=True, progressive=True)
for w in ('Light', 'Regular', 'Bold'):
    f = TTFont(f'fonts/ttf/SutraMono-{w}.ttf'); f.flavor = 'woff2'; f.save(f'docs/fonts/SutraMono-{w}.woff2')
im = Image.open('documentation/specimen.png').convert('RGB'); W, H = 1200, 630
r = max(W / im.width, H / im.height); im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
x = (im.width - W) // 2; im.crop((x, 0, x + W, H)).save('docs/og.png', optimize=True)
shutil.copy('documentation/design-doc/Sutra-Mono-Design-Document.pdf', 'docs/')
with zipfile.ZipFile('docs/SutraMono.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for w in ('Light', 'Regular', 'Bold'):
        z.write(f'fonts/ttf/SutraMono-{w}.ttf', f'SutraMono-{w}.ttf')
    z.write('OFL.txt', 'OFL.txt')
print('assets refreshed:', len(pages), 'doc pages')
