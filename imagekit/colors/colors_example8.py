# INFERENCE FUN!
# Categorize the tags associated to each color in the context.
# Keep a score how much each color is present in a category.
# Find out the category of a given search word.
# Since the word is part of the category,
# the infered color for that category should apply to the word.

colors = ximport("colors")
en = ximport("en")

# WordNet has a set of global categories (or lexnames)
# into which it classifies all words.
# Examples: verb.weather, noun.artifactm nou.animal, ...
lexname_scores = {}
for lexname in en.wordnet.wn.Lexname.dict.keys():
    lexname_scores[lexname] = []

# Traverse all colors in the context (blue, green, ...)
for clr in colors.context.keys():
    
    # Each color has associated tags: blue -> air, cold, calm, ...
    # Calculate the weight of each tag,
    # if there os a total of 100 tags each weighs 0.01,
    # if there are 20 tags each weighs 0.05, etc. 
    weight = 1.0 / len(colors.context[clr])

    # Each tag will obviously appear in the WordNet dictionary,
    # therefore it will also be classified in a lexname category.
    # Count the number of tags in each lexname category.
    count = {}
    for tag in colors.context[clr]:
        for pos, ref in [("noun", en.wordnet.NOUNS), 
                         ("verb", en.wordnet.VERBS), 
                         ("adj",  en.wordnet.ADJECTIVES)]:
            try:
                lexname = pos+"." + en.wordnet.lexname(tag, pos=ref)
                if not count.has_key(lexname):
                    count[lexname] = 0
                count[lexname] += weight
            except:
                pass
    
    # Each lexname then points to a list of colors
    # that have tags categorized under this lexname,
    # together with the tag score from the count dict.
    # noun.feeling -> (blue, 0.09)
    for lexname in count.keys():
        if not lexname_scores.has_key(lexname):
            lexname_scores[lexname] = []
        lexname_scores[lexname].append((clr, count[lexname]))

# So now each lexname in the scores dict points to a number of (color, weight) tuples.
# We normalize the weight so their total weight is 1.0.
# So now we have a percentage of each color's importance for the lexname.
# verb.weather -> grey 24%, orange 19%, white 57%
for lexname in lexname_scores.keys():
    s = sum([weight for clr, weight in lexname_scores[lexname]])
    normalized = [(clr, weight/s) for clr, weight in lexname_scores[lexname]]
    lexname_scores[lexname] = normalized

# This prints out the full list of colors scores per lexname category.
from pprint import pprint
#pprint(lexname_scores)

q = "rabbit" # try out: rave, keyboard, love
q = str(q)

# Now we can do some guessing!
# If we supply "fox" as a query, we can find out that fox is an animal.
# Since we have color scores for noun.animal, these might also apply to foxes.
if   en.is_noun(q): 
    l = "noun."+en.noun.lexname(q)
elif en.is_verb(q): 
    l = "verb."+en.verb.lexname(q)
elif en.is_adjective(q): 
    l = "adj."+en.adjective.lexname(q)
    
print q, "is-a", l

clrs = colors.list()
for clr, weight in lexname_scores[l]:
    for i in range(int(weight*100)):
        clrs += colors.color(clr)

clrs.swarm(150, 150)
