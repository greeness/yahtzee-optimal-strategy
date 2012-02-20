from scoring import Category
from array import array

log = open('small_T')
idx = -1

optimal = []
def to_id(name):
    return Category.CATEGORY_NAME_TO_ID[name]


kept_option = array('B')
id_to_state = {}

highest_bit = 0
nbits  = 0
action_option = array("B")
n = 0

for line in log:
    if line[0] == '$':
        continue
    if line[0] == '#' and len(line) >= 5:
        state = int(line[4:-1])
        id_to_state[len(id_to_state)] = state
        idx = -1
        roll_left = 0
        n = len(id_to_state)-1
        if n and n %1001 == 0:
            print len(id_to_state)/ (357632.0),len(action_option), len(kept_option)/n
            
        action_option = array("B")
          
    if line[0] == '#' and len(line) < 5:
        idx = -1
        roll_left += 1  
        # apend best action to the end of kept_option for this state
        if roll_left == 1:
            kept_option.extend(action_option)
            #n+=1

        nbits = 0
        highest_bit = 0
        
    if idx >= 0:
        mapper_func = int if roll_left >= 1 else to_id
        res = map(mapper_func, line.strip().split(' '))
        
        mask = 0
        if roll_left == 0:
            segment = 4
            added_move = 0
            for i,move in enumerate(res):
                if i<= 1:
                    mask |= move << (segment*i)
                    added_move += 1
            
            # set to all 1s for n/a options
            if added_move == 1:
                mask |= ((1<<segment)-1) << segment
                      
            action_option.append(mask)

        else:
            for i,move in enumerate(res):
                kept_option.append(move & 0b11111111)
                
                highest_bit >>= 1
                # the 9th bit of each move
                highest_bit |= (move & 0b100000000)>>1
            
            # set to all 1s for n/a options
            for i in range(2-len(res)):
                #
                kept_option.append(0b11111111)
                highest_bit >>= 1
                highest_bit |= 0b10000000 
            
            nbits += 2
                
            if nbits == 8:
                kept_option.append(highest_bit)
                nbits = 0
                highest_bit = 0
            
        
    idx += 1
kept_option.tofile(open('options.dat','w+'))
import json
json.dump(id_to_state, open('id_to_state.json','w+'),indent=2)

print 'done'
    