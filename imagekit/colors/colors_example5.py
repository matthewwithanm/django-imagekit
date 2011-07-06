# SHADES

try:
    colors = ximport("colors")
except ImportError:
    colors = ximport("__init__")
    reload(colors)
    
var("hue", NUMBER, 0.8, 0.0, 1.0)
clr = colors.hsb(hue, 1, 1)

x = 20
y = 20
for shade in colors.shades:
    fill(0)
    fontsize(12)
    text(str(shade), x, y-5)
    snapshot = shade.colors(clr, 10)
    snapshot.swatch(x, 20, padding=5)
    y = 20
    x += 50

# New color range from the sum of two shades:
colors.intense(colors.olive(), n=8).swatch(50, 450, w=15, h=15)
colors.neutral(colors.olive(), n=8).swatch(70, 450, w=15, h=15)
r = colors.intense + colors.neutral
r = r(colors.olive(), n=8).swatch(90, 450, w=15, h=15)