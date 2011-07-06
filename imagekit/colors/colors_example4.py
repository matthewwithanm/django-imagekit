# GRADIENT LIST

try:
    colors = ximport("colors")
except ImportError:
    colors = ximport("__init__")
    reload(colors)

size(550, 330)
background(0, 0.1, 0.2)

# Create a list of 60 colors that form a smooth transition
# from light blue to dark blue.
clr1 = colors.rgb(0.6, 0.8, 1.0)
clr2 = colors.rgb(0.0, 0.2, 0.4)
g = colors.gradient(clr1, clr2, steps=60)

# Draw an oval in each color.
# Reduce the radius of each oval and shift it right and down,
# this way we get a radial gradient.
for i in range(len(g)):
    fill(g[i])
    r = 700-i*10
    oval(-75+i*5, -170+i*5, r, r)

# Some nice dropshadows.
colors.shadow(blur=12, alpha=0.3)

# Expand the gradient list, for the next element
# we're going to need more than 60 colors.
# All of the normal methods on color lists (like reverse())
# work as well.
g.steps = 200
g = g.reverse()

# Draw a spiral of ovals for each of the 200 gradient steps:
transform(CORNER)
translate(WIDTH/2, HEIGHT/2)
for i in range(len(g)):
    fill(g[i])
    #fill(choice(g))
    rotate(3)
    oval(i*0.5, i*0.5, 200-i, 200-i)

reset()
    
# All of the colors in the gradient:
i = 0
for x, y in grid(10, len(g)/10, 10, 10):
    if i < len(g):
        fill(g[i])
        rect(x, y, 8, 8)
        i += 1