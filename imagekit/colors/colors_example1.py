# ANALOG COLORS

# Import the library
try:
    # This is the statement you normally use.
    colors = ximport("colors")
except ImportError:
    # But since these examples are "inside" the library
    # we may need to try something different when
    # the library is not located in /Application Support
    colors = ximport("__init__")
    reload(colors)

size(600, 600)

nofill()
stroke(0.4, 0.5, 0)
strokewidth(0.1)
autoclosepath(False)

clr = colors.color(0.6, 0.4, 0)

# Get a very dark variation of the color for the background.
background(colors.dark(clr).darken(0.1))
clr.alpha = 0.5

# Each curve has a shadow and there are a lot of them,
# so we have to use a very subtle shadow:
# very transparent and thin (little blur).
colors.shadow(alpha=0.05, blur=0.2)

for i in range(50):
    # Each strand of curves has an analogous color
    # (i.e. hues that are next to each other on the color wheel).
    # This yields a very natural effect.
    stroke(clr.analog(angle=10, d=0.3))
    # Start drawing strands of curves from the center.
    x0 = WIDTH/2
    y0 = HEIGHT/2
    # Each strand of curves bends in a certain way.
    vx0 = random(-200, 200)
    vy0 = random(-200, 200)
    vx1 = random(-200, 200) 
    vy1 = random(-200, 200)
    # A strand ends up either left or right outside the screen.
    # Each curve in a strand ends up at the same place 
    # (identical x1 and y1).
    x1 = choice((-10, WIDTH))
    y1 = random(HEIGHT)
    
    # This code gives interesting effects as well:
    #from math import radians, sin, cos
    #angle = random(360)
    #x1 = x0 + cos(radians(angle)) * 100
    #y1 = y0 + sin(radians(angle)) * 100
    
    for j in range(100):
        beginpath(x0, y0)
        curveto(
            # The bend of each curve in a strand differs slightly
            # at the start, so the strand looks thicker at the start
            # and then all the curves come together at x1 and y1.
            x0+vx0+random(80), 
            y0+vy0+random(80), 
            x1+vx1, 
            y1+vy1, 
            x1, 
            y1
        )
        endpath()

"""
# Some type, with a heart symbol!
heart = u"\u2665"
s1 = "strands of analogous curves "+heart
s2 = "gratuitous type always looks cool on these things"   
fill(1, 1, 1, 0.85)
fontsize(18)
text(s1, 65, HEIGHT/2)
fontsize(9)
text(s2.upper(), 65, HEIGHT/2+12)
stroke(1)
strokewidth(1)
line(0, HEIGHT/2, 60, HEIGHT/2)
"""