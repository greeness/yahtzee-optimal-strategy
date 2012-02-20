from itertools import combinations_with_replacement, combinations, product, chain
from scoring import Roll, Category

def reverse_dict(d):
    rd = {}
    for k in d:
        for roll in d[k]:
            rd.setdefault(roll, set())
            rd[roll].add(k)
    return rd

""" dice throw experiment"""
def throw_dice(kept):
    n_dice_to_roll = 5-len(kept)
    outcomes  = set(product(dice, repeat=n_dice_to_roll))   
    hist = {}
    for trial in outcomes:
        sorted_trial = tuple(sorted(chain(kept, trial)))
        hist.setdefault(sorted_trial, 0)
        hist[sorted_trial] += 1
    normalizer = float(sum(hist.values()))
    for k in hist:
        hist[k] /= normalizer
    return hist
    
""" g3: the edges from g2 to g3"""        
def get_edges_and_prob():
    dice = range(1,7)
    for t in combinations_with_replacement(dice,5):
        for n_keep in range(0,6):
            for keep in combinations(t,n_keep):
                if keep not in distinct_keeper:
                    distinct_keeper.add(keep)
                    kept_to_id[keep] = len(distinct_keeper)-1
                    id_to_kept[len(distinct_keeper)-1] = keep
                
    reroller = {}
    for case in distinct_keeper:
        n_dice_to_reroll = 5 - len(case)
        for reroll in combinations_with_replacement(dice, n_dice_to_reroll):
            reroll_result = tuple(sorted(chain(case, reroll)))
            reroller.setdefault(case, {})
            reroller[case].setdefault(reroll_result,0)
            reroller[case][reroll_result] = 1
                
    for case in reroller:
        hist = throw_dice(case)
        for key in reroller[case]:
            reroller[case][key] = hist[key]
    return reroller

""" global shared data """
dice = range(1,7)
dice_to_id = {}
id_to_dice = {}
kept_to_id = {}    
id_to_kept = {}

distinct_keeper = set()
for i,t in enumerate(combinations_with_replacement(dice,5)):
    dice_to_id[t] = i
    id_to_dice[i] = t

edge_prob = get_edges_and_prob()
reverse_edge = reverse_dict(edge_prob)

#retro_back = get_retro_back()
single_throw = throw_dice(tuple())

all_5_dice_outcomes = [t for t in combinations_with_replacement(dice,5)]

eval_points = {}
for cat_name in Category.CATEGORY_ID_TO_NAME:
    for r in all_5_dice_outcomes:
        eval_points.setdefault(cat_name, {})
        eval_points[cat_name][r] = Roll(r).eval_point(cat_name)
        print cat_name, r, eval_points[cat_name][r] 

print 'length of dice_to_id', len(dice_to_id)
print 'length of kept_to_id', len(kept_to_id)

for key in id_to_dice:
    #print key, dice_to_id[id_to_dice[key]]
    assert key == dice_to_id[id_to_dice[key]]

for key in id_to_kept:
    #print key, kept_to_id[id_to_kept[key]]
    assert key == kept_to_id[id_to_kept[key]]
                
