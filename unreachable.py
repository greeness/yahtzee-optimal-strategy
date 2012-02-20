""" refer to optimal yahtzee """

""" State information consists of:
  - a binary value for each category denoting whether it is used nor unused
  - an integer value denoting the upper score,could be 0 to 63
  
  There are 2^13 possibilities for the category combination;
  There are 64 possibilities for the upper score
  Totally there are 2^13 * 2^6 = 2^19 = 524,288 states
  
  We can reduce the number of states since some states are unreachable. 
  Let S be a subset of {1,2,3,4,5,6}, 0 <= n <= 63
  Define R(n,S) be true if it is possible to score n points in the upper area
  using categories in S and false otherwise.
  
  Then R(0,S) = true for all S and R(n, empty-set) = false for any n >= 1.
  
  For S is not empty-set and n > 1
            - true, if (x in S, k is a natural number 0<=k<=5, and kx <= n and R(n-kx, S-{x}) is true]
  R(n,S) =  |
            - false, otherwise
            
  In my computation, there are 2792 out of 4096 states are valid, 1304 invalid.
  so number of valid reachable states = 2792* 2^7 = 357,376
  """
from scoring import clear_bit
N_FACES = 6
N_DICES = 5
N_CATEGORIES = N_FACES
S_max = 1<<N_CATEGORIES
n_max = (1+N_FACES)*N_FACES*N_DICES/2 + 1
#n_max = (1+N_FACES)*N_FACES*3/2 + 1
R = [[-1]*S_max for x in xrange(n_max)]

def get_set_out_of_mask(mask):
    ret = set()
    for i in range(N_CATEGORIES):
        if mask & (1<<i):
            ret.add(i+1)
    return ret
 
def calc_R(n, s):
    if R[n][s] != -1:
        return R[n][s]
    if n == 0: 
        R[n][s] = 1;
        return 1;
    # s is empty but get a score great than 0: impossible
    #if s == 0 and n > 0: 
    #    R[n][s] = 0; return 0;
    solved = False
    # k from 0 to 5, number of dices that have a face value of x
    for k in range(N_DICES+1):
        for x in get_set_out_of_mask(s):
            n1 = n-k*x
            if (n1 < 0): continue
            if (n1 > 63): continue
            # remove x from superset s
            s1 = clear_bit(s,x)
            r = calc_R(n1, s1)
            if r == 1:
                solved = True
                N = n if n <= 63 else 63
                R[N][s] = 1
                 
    if not solved:
        R[n][s] = 0
    return R[n][s]

def get_reachable_set():
    reachable_set = set()
    unreachable_set=set()
    for n in range(n_max):
        for s in range(S_max):
            r = calc_R(n,s)
            N = n if n <= 63 else 63
            if r: reachable_set.add((N,s))
            else: unreachable_set.add((N,s))   
    total = len(reachable_set)+len(unreachable_set)
    print 'reachables: %d out of %d' % (len(reachable_set), total)
    print 'unreachables: %d out of %d' % (len(unreachable_set), total)
    return (reachable_set)

reachable_set = get_reachable_set()

from itertools import combinations
def get_all_cases_with_N_available_categories(n):
    n_used = 13-n
    case = set()
    for s in reachable_set:
        upper_score, upper_used_mask  = s
        upper_used = get_set_out_of_mask(upper_used_mask)
        lower_used = n_used - len(upper_used)
        
        if lower_used < 0 or lower_used > 7:
            continue
        mask_base = 0b0000000111111 & upper_used_mask
        for com in combinations(range(6,13), lower_used):
            mask = mask_base
            for c in com:
                mask |= 1<<c
            case.add((mask, upper_score))
    return case

if __name__ == '__main__':
    print n_max
    total = 0
    for n in range(13+1):
        cases = get_all_cases_with_N_available_categories(n)
        n_case = len(cases)
        total += n_case
        print n, n_case
    print total