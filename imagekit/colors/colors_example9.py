# SORTING COLOR LISTS

# Import the library
try:
    colors = ximport("colors")
except ImportError:
    colors = ximport("__init__")
    reload(colors)

# A list of a 100 random colors.
l = colors.list([color(random(), random(), random()) for i in range(100)])
l.swatch(10, 10, h=4)

# Take the darkest color, put the nearest next to it, etc.
l = l.sort_by_distance()
l.swatch(60, 10, h=4)

# Sort by color property.
l = l.sort_by_brightness()
l.swatch(110, 10, h=4)

# Sort by two color properties.
l = l.cluster("hue", "saturation")
l.swatch(160, 10, h=4)