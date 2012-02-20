from array import array
from random import randint, choice
import numpy
from pprint import pprint
import json
from combinatorics_class import *
from widget import load_expectation, get_next_state, get_state_big_mask
from widget import get_expected_score
from random import randint
import logging
logging.basicConfig(format='%(message)s',level=logging.INFO)
logger = logging.getLogger('dice_bot')


state_to_id = {}
action_blob = array('B')

N_STATES = 357568
N_BYTES = 1386
DIFF_MIN = 0
DIFF_MAX = 100
ACTION_OFFSET = 1134
BLOCK_SIZE = 252
BLOCK_PLUS_SIZE = (BLOCK_SIZE/4)*9

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

def load_optimal_strategy():
    id_to_state_json = json.load(open('id_to_state.json'))
    for k,v in id_to_state_json.iteritems():
        state_to_id[int(v)] = int(k)

    action_blob.fromfile(file('options.dat'),N_STATES*N_BYTES)
    
def pass_rand_test(diff_level):
    if randint(DIFF_MIN, DIFF_MAX) <= diff_level:
        return True
    return False

def get_option_by_decoding(state, rid, roll_left, diff_level=10):
    """ 
    state: the 19 bit bitmask to represent the current game state
    rid: the 8 bit roll id representing the roll result
    roll_left: 0,1 or 2, how many rolls left in this turn, start with 2 and end with 0
    diff_level: how intelligent the bot move is, 0 - 100, integer
    """
    
    state_id = state_to_id[state]
    state_base = N_BYTES * state_id
    
    state_segment = action_blob[state_base:state_base+N_BYTES]
    
    if roll_left == 0:
        move_offset = 0
    elif roll_left == 1:
        move_offset = BLOCK_SIZE
    else:
        move_offset = BLOCK_SIZE+BLOCK_PLUS_SIZE
    
    if roll_left == 0:
        mask = (1<<4)-1
        pos_idx = move_offset + rid
        opt1 = state_segment[pos_idx] & mask
        opt2 = (state_segment[pos_idx]>>4) & mask
        
    else:
        mask = (1<<9)-1        
        opt_lower_idx = move_offset + (rid/4)*9 + (rid%4)*2
        opt_higher_idx = move_offset + (rid/4)*9 + 8
       
        highest_bit_1 = ((state_segment[opt_higher_idx] >> ((rid%4)*2))) & 1
        highest_bit_2 = ((state_segment[opt_higher_idx] >> ((rid%4)*2+1))) & 1
         
        opt1 = state_segment[opt_lower_idx] | (highest_bit_1<<8)
        opt2 = state_segment[opt_lower_idx+1] | (highest_bit_2<<8)
    
    if pass_rand_test(diff_level) or opt2 == mask:
        return opt1
    return opt2
    #if roll_left == 0 :
    #    return opt1
    
def run_game(trial,diff_level=10):
    state = (0,0)
    i=1
    total_pts = 0
    while i<=13:
        logger.info("%s,diff %2d, trial %d, turn %d", '='*20, diff_level,trial,i)
        i+=1
        roll_left = 2
        bigstate = get_state_big_mask(state)
        roll0 = dice_to_id[roll_dice(5)]
        logger.info('dice0, %s', id_to_dice[roll0])
        kid0 = get_option_by_decoding(bigstate, roll0, roll_left, diff_level)
        keep0 = id_to_kept[kid0]
        logger.info('keep0,%s', keep0)
        roll_left -= 1
        
        roll1 = dice_to_id[merge(keep0, roll_dice(5-len(keep0)))]
        logger.info('dice1,%s', id_to_dice[roll1])
        
        kid1 = get_option_by_decoding(bigstate, roll1, roll_left, diff_level)
        keep1 = id_to_kept[kid1]
        logger.info('keep1,%s', keep1)
        roll_left -= 1
        
        roll2 = dice_to_id[merge(keep1, roll_dice(5-len(keep1)))]
        logger.info('dice2,%s', id_to_dice[roll2])
        
        act = get_option_by_decoding(bigstate, roll2, roll_left, diff_level)
        state = get_next_state(state, id_to_dice[roll2], Category.CATEGORY_ID_TO_NAME[act])
        pts = eval_points[Category.CATEGORY_ID_TO_NAME[act]][id_to_dice[roll2]]
        logger.info('choice,%s, earn %f', Category.CATEGORY_ID_TO_NAME[act], pts)
        
        total_pts += pts        
            
        logger.info('this turn: %d, total pts: %d, upper score: %d',pts, total_pts, state[1])
        logger.info('state: %s', bin(state[0]))
        
    if state[1] == 63:
        total_pts += 35
        logger.info( 'extra bonus added, total: %s', total_pts)
    return total_pts

def get_adaptive_diff(turn, delta_pts, diff_level=50):
    #if turn <= 4:
    #    return diff_level
    return max(DIFF_MIN,min(DIFF_MAX, diff_level - .5*delta_pts))
    

def run_game_two_players(trial, diff_level=50):
    """
    the first player is the bot player with fixed difficulty level
    the second player is the adaptive bot that tries to get a 
    final score as close as to the first play's.
    """
    state = (0,0)   # first player state
    my_state = (0,0) # second player state
    turn = 1
    total_pts = 0
    my_total_pts = 0
    while turn<=13:
        
        # first player begin
        logger.info("%s,diff %2d, trial %d, p1-turn %d", '='*20, diff_level,trial,turn)

        roll_left = 2
        bigstate = get_state_big_mask(state)
        roll0 = dice_to_id[roll_dice(5)]
        logger.info('dice0, %s', id_to_dice[roll0])
        kid0 = get_option_by_decoding(bigstate, roll0, roll_left, diff_level)
        keep0 = id_to_kept[kid0]
        logger.info('keep0,%s', keep0)
        roll_left -= 1
        
        roll1 = dice_to_id[merge(keep0, roll_dice(5-len(keep0)))]
        logger.info('dice1,%s', id_to_dice[roll1])
        
        kid1 = get_option_by_decoding(bigstate, roll1, roll_left, diff_level)
        keep1 = id_to_kept[kid1]
        logger.info('keep1,%s', keep1)
        roll_left -= 1
        
        roll2 = dice_to_id[merge(keep1, roll_dice(5-len(keep1)))]
        logger.info('dice2,%s', id_to_dice[roll2])
        
        act = get_option_by_decoding(bigstate, roll2, roll_left, diff_level)
        state = get_next_state(state, id_to_dice[roll2], Category.CATEGORY_ID_TO_NAME[act])
        pts = eval_points[Category.CATEGORY_ID_TO_NAME[act]][id_to_dice[roll2]]
        
        
        my_diff_level = get_adaptive_diff(turn, my_total_pts - total_pts, diff_level)
        total_pts += pts
        logger.info('choice,%s, earn %f, exp-score %f', Category.CATEGORY_ID_TO_NAME[act], pts, total_pts + get_expected_score(state))
        
        logger.info('this turn: %d, total pts: %d, upper score: %d',pts, total_pts, state[1])
        logger.info("%s,diff %2d, trial %d, p2-turn %d", '='*20, diff_level,trial,turn)
        
        # second player begin
        # my intelligence is based on delta score and the current turn
        
        my_roll_left = 2
        my_bigstate = get_state_big_mask(my_state)
        my_roll0 = dice_to_id[roll_dice(5)]
        logger.info('dice0, %s', id_to_dice[my_roll0])
        my_kid0 = get_option_by_decoding(my_bigstate, my_roll0, my_roll_left, my_diff_level)
        my_keep0 = id_to_kept[my_kid0]
        logger.info('keep0,%s', my_keep0)
        my_roll_left -= 1
        
        my_roll1 = dice_to_id[merge(my_keep0, roll_dice(5-len(my_keep0)))]
        logger.info('dice1,%s', id_to_dice[my_roll1])
        
        my_kid1 = get_option_by_decoding(my_bigstate, my_roll1, my_roll_left, my_diff_level)
        my_keep1 = id_to_kept[my_kid1]
        logger.info('keep1,%s', my_keep1)
        my_roll_left -= 1
        
        my_roll2 = dice_to_id[merge(my_keep1, roll_dice(5-len(my_keep1)))]
        logger.info('dice2,%s', id_to_dice[my_roll2])
        
        my_act = get_option_by_decoding(my_bigstate, my_roll2, my_roll_left, my_diff_level)
        my_state = get_next_state(my_state, id_to_dice[my_roll2], Category.CATEGORY_ID_TO_NAME[my_act])
        my_pts = eval_points[Category.CATEGORY_ID_TO_NAME[my_act]][id_to_dice[my_roll2]]
        
        my_total_pts += my_pts
        logger.info('choice,%s, earn %f, exp-score %f', Category.CATEGORY_ID_TO_NAME[my_act], my_pts, my_total_pts + get_expected_score(my_state))
        
        logger.info('this turn: %d, total pts: %d, upper score: %d',my_pts, my_total_pts, my_state[1])
        
        #logger.info('state: %s', bin(state[0]))
        turn += 1
        
    if state[1] == 63:
        total_pts += 35
        logger.info( 'p1 extra bonus added, total: %s', total_pts)
    if my_state[1] == 63:
        my_total_pts += 35
        logger.info( 'p2 extra bonus added, total: %s', my_total_pts)
    return my_total_pts - total_pts

    
import time
from datetime import datetime
if __name__ == '__main__':
    load_optimal_strategy()
    E = load_expectation()
    n_trial = 1000
    for difficulty in range(100,-1,-10):
        t1 = datetime.now()
        tp=[]   
        for trial in range(n_trial):
            #t = run_game(trial, difficulty)
            t = run_game_two_players(trial, difficulty)
            tp.append(t)
            logger.warning("diff=%d, %f, (%f, %f)", difficulty, t, numpy.mean(tp), numpy.std(tp))
        t2 = datetime.now()
        logger.critical("diff=%3d, (%f, %f), time:%s", difficulty, numpy.mean(tp), numpy.std(tp), (t2-t1).total_seconds())
        time.sleep(2)
    
    