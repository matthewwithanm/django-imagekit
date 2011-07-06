# THEMES

try:
    colors = ximport("colors")
except ImportError:
    colors = ximport("__init__")
    reload(colors)

# Themes are groups of color ranges (like warm or dark)
# linked to a specific hue (like red or green).
# It's easy to make up color themes, like using plain English.
# For example:
t = colors.theme()
t.name = "ancient egypt"
t.add_range("soft ivory", weight=0.5)
t.add_range("dark goldenrod", weight=0.2)
t.add_range("intense gold", weight=0.2)
t.add_range("warm brown", weight=0.2)
# To supply the range and color separately:
t.add_range(colors.neutral, colors.teal(), weight=0.1)
t.add_range(colors.intense, colors.red(), weight=0.1)

stroke(0)
strokewidth(0.2)
t.swatch(50, 50, n=12)

# More than 4000 words (especially emotions, adjectives
# and everyday concepts) have been stored in database.
# Since they're harvested automatically from the web,
# they're not always that good, 
# but a good source of inspiration nonetheless.
t2 = colors.theme("love")
t2.swatch(50,550, w=10, h=10, padding=1)

# With the recombine() method, we can create
# new generations from two parent themes!
t3 = t.recombine(t2, d=0.7)
print "ancient egypt + love = ", t3.name
t3.swatch(200, 550, w=10, h=10, padding=1, grouped=False)
