from widget import *
from random import randint, choice
import numpy
def roll_dice(n):
    res = []
    for i in range(n):
        res.append(choice(dice))
    
    return tuple(sorted(res))

def merge(r1, r2):
    assert(len(r1) + len(r2) == 5)
    r = []
    r.extend(list(r1))
    r.extend(list(r2))
    return tuple(sorted(r))

def display_keep_options(roll, opt):
    for k,v in sorted(opt.items(), key=lambda x:x[1]):
        logger.info("%18s -> %18s: %8.4f",id_to_dice[roll], id_to_kept[k], v)
        
def display_category_options(roll, opt):
    for k,v in sorted(opt.items(), key=lambda x:x[1]):
        logger.info("%18s -> %2s: earn %2d, expected %8.4f",id_to_dice[roll], k, Roll(id_to_dice[roll]).eval_point(k), v)
       
def get_strategy(opt, diff_level=10):
    max_diff = 10
    min_diff = 1
    options = sorted(opt.items(), key=lambda x:x[1])
    n_options = len(options)
    
    if randint(min_diff,max_diff) <= diff_level:
        # use optimal strategy
        return options[-1]
            
    diff_level = max(min(diff_level, max_diff), min_diff)
    idx = n_options*diff_level/max_diff - 1
    return options[idx]
      
def run_game(trial, diff_level):
    state = (0,0)
    i=1
    total_pts = 0
    while i<=13:
        logger.info("%s,%d-%d", '='*20, trial,i)
        i+=1
        e0,e0_action,e0_full,\
        e1,e1_action,e1_full,\
        e2,e2_action,e2_full = process_main(state)
        roll0 = dice_to_id[roll_dice(5)]
        logger.info('dice0, %s', id_to_dice[roll0])
        display_keep_options (roll0, e2_full[roll0])
        kid0,exp0 = get_strategy(e2_full[roll0], diff_level)
        keep0 = id_to_kept[kid0]
        logger.info('keep0,%s,%f', keep0, total_pts+exp0)
        
        roll1 = dice_to_id[merge(keep0, roll_dice(5-len(keep0)))]
        logger.info('dice1,%s', id_to_dice[roll1])
        display_keep_options (roll1, e1_full[roll1])
        kid1,exp1 = get_strategy(e1_full[roll1], diff_level)
        keep1 = id_to_kept[kid1]
        logger.info('keep1,%s,%f', keep1, total_pts+exp1)
        
        roll2 = dice_to_id[merge(keep1, roll_dice(5-len(keep1)))]
        logger.info('dice2,%s', id_to_dice[roll2])
        display_category_options (roll2, e0_full[roll2])
        act,exp2 = get_strategy(e0_full[roll2], diff_level=10)
        logger.info('choice,%s,%f', act, total_pts+exp2)
        
        state = get_next_state(state, id_to_dice[roll2], e0_action[roll2])
        pts = eval_points[e0_action[roll2]][id_to_dice[roll2]]
        total_pts += pts        
            
        logger.info('this turn: %d, total pts: %d, upper score: %d',pts, total_pts, state[1])
        logger.info('state: %s', bin(state[0]))
        
    if state[1] == 63:
        total_pts += 35
        logger.info( 'extra bonus added, total: %s', total_pts)
    return total_pts

import time
import sys
if __name__ == '__main__':
    load_expectation()
    tp = []
    if len(sys.argv) == 2:
        difficulty = int(sys.argv[1])
    else:
        difficulty = 7
        
    n_trial = 200
    for trial in range(n_trial):
        t = run_game(trial, difficulty)
        tp.append(t)
        logger.warning("%3d, %f, %f, %f", trial, t, numpy.mean(tp), numpy.std(tp))
        time.sleep(1)
    