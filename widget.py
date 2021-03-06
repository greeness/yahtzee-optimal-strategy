from scoring import Category, set_bit, get_category_name_out_of_mask, Roll
from combinatorics_class import *
from datetime import datetime
from unreachable import get_all_cases_with_N_available_categories
import json
import logging
logging.basicConfig(format='%(message)s',level=logging.DEBUG)
logger = logging.getLogger('dice')

N_OUTCOMES_ROLL = 252
N_OUTCOMES_KEEP = 462
UPPER_POINTS_THRESHOLD = 63
UPPER_POINTS_EXTRA = 35

E = {}  # this is for yahtzee bit = 0
E1 = {} # this is for yahtzee bit = 1
def get_expected_score_by_mask(big_state):
    m = big_state>>13
    C = big_state & ((1<<13)-1)
    return get_expected_score((C,m))

# extension for M5OK
# state is the 13-bit state integer
def is_m5ok_possible(state):
    # if yahtzee bit is set, it's possible
    if (state & (1<<12)):
        return True
    # otherwise, don't even think about it
    return False

def get_expected_score(state, yahtzee=0):
    """
    m: upper section score
    C: 13-bit integer representing current state of the 13 categories
    """
    C, m = state
    if yahtzee == 0: 
        if m in E and C in E[m]:
            return E[m][C]
    else:
        if m in E1 and C in E1[m]:
            return E1[m][C]
    print 'key does not exist (state,upper_score)=(%d,%d)' %(C, m)
    return -1

def get_next_state((mask, upper_score), roll_tuple, cat, yahtzee=0):
    C1 = set_bit(mask, Category.CATEGORY_NAME_TO_ID[cat])
    earned_points = eval_points[cat][roll_tuple]

    #print 'earned %d points from roll %s' % (earned_points, r._roll)
    m1 = upper_score
    if Category.is_upper_category(cat):
        m1 = min(UPPER_POINTS_THRESHOLD, m1 + earned_points)
    
    # if we are 
    #   -- coming from a 'has yahtzee state' or 
    #   -- we scored on 'Y' category this turn or
    #   -- we made yahtzee in current turn and `yahtzee` has already been marked yet, 
    # we keep the flag on
    if yahtzee or (cat == 'Y' and earned_points > 0) or \
       ( Roll(roll_tuple).has_yahtzee() and not (( mask & (1<<12)) == 0)): 
        
        next_yahtzee = 1
    else:
        next_yahtzee = 0
        
    return ((C1, m1), next_yahtzee)

def push_expected_score(state, exp, yahtzee=0):
    C, m = state
    if yahtzee == 0:
        if m not in E:
            E[m] = {}
        E[m][C] = exp
    else:
        if m not in E1:
            E1[m] = {}
        E1[m][C] = exp
    
def get_state_big_mask((mask,upper_score)):
    return (upper_score<<13) | mask

def get_top_options(opt, n):
    options = sorted(opt.items(), key=lambda x:x[1],reverse=True)
    ret = []
    for option in options[:n]:
        #ret.append("%s,%.3f" % (str(option[0]),option[1]))
        ret.append(option[0])
    return ret
  
"""
r: dice roll result
c: category
s: state
E(s, r, 0) = max ( score of r in c + E (final state using r for c) ) 
    for all possible c that is still available
"""

def expectation_exit((mask, upper_score), yahtzee=0):
    available_categories = get_category_name_out_of_mask(mask)
    
    e0 = [0]*N_OUTCOMES_ROLL
    e0_action = [0]*N_OUTCOMES_ROLL
    e0_full = {}
    #for cat_name in available_categories:
    #    logger.debug('available categories: %s', cat_name)
    
    bigstate = get_state_big_mask((mask, upper_score))
    #print '### %d' % (bigstate)
    # iterate all possible outcomes of final rolls
    for i,t in enumerate(all_5_dice_outcomes):
        max_expected_score = 0
        max_category = ''
        tid = dice_to_id[t]
        e0_full[tid] = {}
        for cat_name in available_categories:
            score = eval_points[cat_name][t]
            
            # considerting multiple 5-of-a-kind bonus
            if Roll(t).has_yahtzee() and yahtzee:
                score += 50    
            next_state, next_yahtzee = get_next_state((mask,upper_score), t, cat_name, yahtzee)
            next_exp_score = get_expected_score(next_state, yahtzee=next_yahtzee)
            if next_exp_score == -1:
                logger.critical("current state (%d,%d)", mask, upper_score)
                logger.critical("roll %s in category %s", t, cat_name)
                logger.critical("next state mask %s", next_state)
                raise ValueError
            
            total_score = score + next_exp_score
            e0_full[tid][cat_name] = total_score
            
            if total_score >= max_expected_score:
                max_expected_score = total_score
                max_category = cat_name
            logger.debug("%3d, %s, category %2s, %10s -> %2d + %8.4f = %8.4f, cur_max=%8.4f", i, t, cat_name, 
                         next_state, score, next_exp_score, total_score, max_expected_score)
        e0[i] = max_expected_score
        """
        top = get_top_options(e0_full[tid],4)
        best_cat = top[0]
        best_score = e0_full[tid][best_cat]
        for opt in top:
            if abs(e0_full[tid][opt]- best_score) <= 5.0:
                print opt, 
        print 
        """
        e0_action[i] = max_category
        
    logger.debug("====== leaving exit")
    #print "###"
    return (e0,e0_action,e0_full)

"""
E(s,r',1) = SUM (Prob(r'->r) x E(s,r,0))  over 252 outcomes of r for each fixed r'

Prob(r'->r) is pre-calculated in combinatorics for each edge
E(s,r,0) is the result from the previous step
"""
def expectation_keep(e0):
    e0_prime = [0]*N_OUTCOMES_KEEP
    # iterate all possible outcomes of keeper
    for i,keep in enumerate(distinct_keeper):
        sum_contri = 0
        # iterate all possible edge for each keeper
        for j,roll in enumerate(edge_prob[keep]):
            prob = edge_prob[keep][roll]
            contri = prob * e0[dice_to_id[roll]]
            sum_contri += contri
            logger.debug('%3d,%3d,%16s -> %16s: %5.2f * %5.2f =%8.4f, total: %8.4f', 
                         i,j,keep, roll, prob,e0[dice_to_id[roll]], contri, sum_contri)
        e0_prime[kept_to_id[keep]] = sum_contri
    logger.debug("====== leaving kept")
    
    return e0_prime

""" above we finished the group 6 and group 5, we next we progress 
the same way with group 4 and group 3
The only difference is for group 4, 
E(s,r,1) = max (E(s,r',1) ) over all r' that is reachable from r

"""
def expectation_roll(e0_prime,roll_left=2):
    e1 = [0]*N_OUTCOMES_ROLL
    e1_action=[0]*N_OUTCOMES_ROLL
    e1_full={}
    for i,t in enumerate(all_5_dice_outcomes):
        tid = dice_to_id[t]
        e1_full[tid] = {}
        keeps = reverse_edge[t]
        max_exp_seen = 0
        max_keep = ()
        for keep in keeps:
            kid = kept_to_id[keep]
            exp = e0_prime[kid]
            e1_full[tid][kid] = exp
            #print '%d,%d,%f'% (tid,kid,exp)
            if exp >= max_exp_seen:
                max_exp_seen = exp
                max_keep = keep
            logger.debug("%3d,%16s -> %16s, %8.4f, max %8.4f", i, t, keep, exp, max_exp_seen)
        e1[i] = max_exp_seen
        e1_action[i] = max_keep
        
        """
        top = get_top_options(e1_full[tid],2)
        best_cat = top[0]
        best_score = e1_full[tid][best_cat]
        
        for opt in top:
            if abs(e1_full[tid][opt]- best_score) <= 5.0:
                print opt,
        print
        logger.debug("%3d,%16s,%8.4f,**", i, t, max_exp_seen)
        """
        
    print '###'        
    logger.debug('========= leaving roll')
    return (e1,e1_action,e1_full)
    
"""
E(s) = SUM ( Prob(null->r) * E(s,r,2)) over all 252 roll possibilities
"""
def expectation_entry(e2):
    sum_exp = 0
    for i,t in enumerate(all_5_dice_outcomes):
        prob = single_throw[t]
        exp = prob * e2[dice_to_id[t]]
        logger.debug("%3d, null -> %16s: %5.1f * %5.1f = %8.4f, sum=%8.4f", 
                     i, t, prob, e2[dice_to_id[t]],  exp, sum_exp)
        sum_exp += exp
    logger.debug('expected score: %f', sum_exp)
    return sum_exp
    
def process_main(state, yahtzee=0):
    logger.debug('%s 6:after final roll', '='*25)
    e0,e0_action,e0_full= expectation_exit(state, yahtzee)
    logger.debug('%s 5:after second keep', '='*25)
    e0_prime    = expectation_keep(e0)
    logger.debug('%s 4:after second roll', '='*25)
    e1,e1_action,e1_full= expectation_roll(e0_prime,2)
    logger.debug('%s 3:after first keep', '='*25)   
    e1_prime    = expectation_keep(e1)
    logger.debug('%s 2:after the first roll', '='*25)
    e2,e2_action,e2_full= expectation_roll(e1_prime,1)
    logger.debug('%s 1:at extry point', '='*25)
    expectation = expectation_entry(e2)
    push_expected_score(state, expectation, yahtzee)
    return (e0,e0_action,e0_full,
            e1,e1_action,e1_full,
            e2,e2_action,e2_full)
    
def process_main1(state, yahtzee=0):
    logger.debug('%s 6:after final roll', '='*25)
    e0,e0_action,e0_full= expectation_exit(state, yahtzee)

def load_expectation(timestamp=''):
    #timestamp = "updated"
    E0 = json.load(open('./data/exp%s.json' % timestamp))
    E = {}
    for k in E0:
        E[int(k)] = {}
        for v in E0[k]:
            E[int(k)][int(v)] = E0[k][v]       
    return E

def training_expectation():            
    a = datetime.now()
    total_processed = 0
    for n in range(0, Category.N_CATEGORIES+1):
        cases = get_all_cases_with_N_available_categories(n)
        n_cases = len(cases)
        print '$$$ %d with %d cases, total %d processed' %(n, n_cases, total_processed)
        logger.info("%d with %d cases, total %d processed", n, n_cases, total_processed)
        processed = 0
        for i, (mask, upper_score) in enumerate(cases):
            processed+=1
            if processed % 100 == 0:
                b = datetime.now()
                logger.info('%7d processed, %s', processed, (b-a).total_seconds())
                a = datetime.now()
            if n == 0:
                if upper_score < UPPER_POINTS_THRESHOLD:
                    push_expected_score((mask, upper_score), 0, yahtzee=0)
                    if is_m5ok_possible(mask):
                        push_expected_score((mask, upper_score), 0, yahtzee=1)
                else:
                    push_expected_score((mask, upper_score), UPPER_POINTS_EXTRA, yahtzee=0)
                    if is_m5ok_possible(mask):
                        push_expected_score((mask, upper_score), UPPER_POINTS_EXTRA, yahtzee=1)
            else:
                logger.debug("%2d, %5d/%5d, %15s, upper score = %2d", 
                            n, i, n_cases, bin(mask), upper_score)
                process_main1((mask, upper_score), yahtzee=0)
                if is_m5ok_possible(mask):
                    process_main1((mask, upper_score), yahtzee=1)
                    
        json.dump(E, open('./data/new-exp0-%s.json' % str(datetime.now()),'w+'), indent=2)  
        json.dump(E1, open('./data/new-exp1-%s.json' % str(datetime.now()),'w+'), indent=2)
    
        total_processed += processed      
    #json.dump(E, open('./data/new-exp-%s.json' % str(datetime.now()),'w+'), indent=2)      
"""        
def run_one_turn(r,start_state=(0,0)):
    e0,e0_action,e0_full,\
    e1,e1_action,e1_full,\
    e2,e2_action,e2_full = process_main(start_state)
    if len(r) == 3:
        r0,r1,r2 = r
        roll0 = dice_to_id[r0]
        roll1 = dice_to_id[r1]
        roll2 = dice_to_id[r2]
        next_state = get_next_state(start_state, id_to_dice[roll2], e0_action[roll2])
        earned_points = eval_points[e0_action[roll2]][id_to_dice[roll2]]
        logger.info("%s -> %s: %f", id_to_dice[roll0], e2_action[roll0],e2[roll0])
        logger.info("%s -> %s: %f", id_to_dice[roll1], e1_action[roll1],e1[roll1])
        logger.info("%s -> %s: %f", id_to_dice[roll2], e0_action[roll2],e0[roll2])
    elif len(r) == 2:
        r0,r1 = r
        roll0 = dice_to_id[r0]
        roll1 = dice_to_id[r1]
        next_state = get_next_state(start_state, id_to_dice[roll1], e0_action[roll1])
        earned_points = eval_points[e0_action[roll1]][id_to_dice[roll1]]
        logger.info("%s -> %s: %f", id_to_dice[roll0], e2_action[roll0],e2[roll0])
        logger.info("%s -> %s: %f", id_to_dice[roll1], e0_action[roll1],e1[roll1])
    else:
        roll0 = dice_to_id[r]
        next_state = get_next_state(start_state, id_to_dice[roll0], e0_action[roll0])
        earned_points = eval_points[e0_action[roll0]][id_to_dice[roll0]]
        logger.info("%s -> %s: %f", id_to_dice[roll0], e0_action[roll0],e0[roll0])
    logger.info("earn %d points, ended up in state %s", earned_points, next_state)    
    
    return (earned_points,next_state)
"""

def connection(bot_potential):
    import MySQLdb, cPickle  
    # Connect to a DB, e.g., the test DB on your localhost, and get a cursor 
    connection = MySQLdb.connect('dev-dice.ch6lcsgrqitm.us-east-1.rds.amazonaws.com',
                        'dice','6W97921897')
    connection.autocommit(True)
    cursor = connection.cursor( )  
    # Make a new table for experimentation 
    
    cursor.execute("USE dice")
   
    try: 
       
        # Perform the insertions        
        sql = "INSERT INTO DicePotentialScore (StateId, PotentialScore) VALUES (%s, %s)" 
        
        buffers = []
        for i, (k,v) in enumerate(bot_potential.iteritems()):            
            if i and i % 10000 == 0:
                cursor.executemany(sql, buffers)
                connection.commit()
                buffers = []
                print i
                
            buffers.append((str(k), str(v)))
        
        cursor.executemany(sql, buffers)
        connection.commit()       
        #connection.commit()
        
    finally: 
        # Done. Remove the table and close the connection. 
        #cursor.execute("DROP TABLE justatest") 
        connection.close( )
        
if __name__ == "__main__":   
    #training_expectation()
    E0 = load_expectation('0')
    E1 = load_expectation('1')
    E = load_expectation('-updated')
    
    #for i in range(64):
    #   print i, len(E0[i]) == len(E1[i])*2
    
    bot_potential = {}
    
    for upper_score,v in E0.iteritems():
        for mask,potential_score in v.iteritems():
            k,v = (((upper_score<<13) | mask), potential_score)
            bot_potential[k] = v
    
    for upper_score,v in E1.iteritems():
        for mask,potential_score in v.iteritems():
            k,v = (((1<<19) | (upper_score<<13) | mask), potential_score)
            bot_potential[k] = v
    
    for upper_score,v in E.iteritems():
        for mask, potential_score in v.iteritems():
            if abs(potential_score- E0[upper_score][mask]) > 1.0:
                print upper_score, bin(mask), potential_score, E0[upper_score][mask], abs(potential_score- E0[upper_score][mask])
    #connection(bot_potential)
        
    
    