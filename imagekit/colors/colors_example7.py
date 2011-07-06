# SHADER

try:
    colors = ximport("colors")
except ImportError:
    colors = ximport("__init__")
    reload(colors)

# Deep green gradient background.
size(400, 400)
bg = rect(0,0,WIDTH,HEIGHT,draw=False)
colors.gradientfill(bg, color(0.15,0.2,0), color(0,0,0))
colors.shadow()

for i in range(800):
    
    x = random(400)
    y = random(400)
    
    # A lightsource positioned at the centre of the canvas.
    d = colors.shader(x, y, WIDTH/2, HEIGHT/2, angle=None, radius=150)
    
    # Ovals become smaller when further away from the light.
    # If they become too small, don't draw them.
    r = d*40
    if r < 4: continue
    p = oval(x, y, r*2, r*2, draw=False)
    
    # Two colors for an oval gradient fill.
    # The green becomes lighter and more opaque
    # when elements are nearer the light.
    nostroke()
    clr1 = color(0.4+d*0.5, 0.6+d*0.3, 0, 0.75)
    clr2 = color(0, 0, 0, d)
    colors.gradientpath(p, clr1, clr2, alpha=0.5+d, dx=r, dy=r)
    
    ###########################################
    # The code below just adds a few more bells.
    
    # Curves lead from the atoms near the edge
    # towards the center of the cluster.
    nofill()
    stroke(clr1)
    strokewidth(0.25)
    autoclosepath(False)
    if d < 0.3:
        for j in range(random(10)):
            v = (1-d) * 150
            beginpath(x, y)
            curveto(
                x, y, 
                x+random(-v,v), y+random(-v,v), 
                WIDTH/2, HEIGHT/2
            )
            endpath()
    
    try:
        # Draw an organic pattern on the atoms
        # in the center.
        supershape = ximport("supershape")
        strokewidth(d*0.75)
        if d > 0.25:
            p = supershape.path(x+r, y+r, r, r, 10, 1.5, -0.5, 1.5)
            drawpath(p)
    except:
        # Couldn't find the Supershape library.
        pass