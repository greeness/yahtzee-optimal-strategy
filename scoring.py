
""" category -relatd utilities"""
class Category:
    CATEGORY_ID_TO_NAME = [
        '1', '2', '3', '4',
        '5', '6', '3K','4K',
        'FH','SS','LS',
        'C', 'Y']
    CATEGORY_NAME_TO_ID = {}
    for i,name in enumerate(CATEGORY_ID_TO_NAME):
        CATEGORY_NAME_TO_ID[name] = i
        
    N_FACES = 6
    N_DICES = 5
    N_CATEGORIES = 13
    S_max = 1<<N_CATEGORIES
    
    @staticmethod
    def is_upper_category(category):
        return category in ['1','2','3','4','5','6']

    @staticmethod
    def get_all_possible_point(category):
        possible_points = set()
        if Category.is_upper_category(category):
            for dice in range(0, Category.N_DICES+1):
                possible_points.add(dice* (Category.CATEGORY_NAME_TO_ID[category]+1))
        
        if category in ['3K','4K','C']:
            for total in range(Category.N_DICES,Category.N_DICES*Category.N_FACES+1):
                possible_points.add(total)
        if category == 'FH':
            possible_points.add(25)
        if category == 'SS':
            possible_points.add(30)
        if category == 'LS':
            possible_points.add(40)
        if category == 'Y':
            possible_points.add(50)
        if category not in ['3K','4K','C']:
            possible_points.add(0)
        return possible_points
    
def set_bit(state, x):
    return state | (1<<(x))

def clear_bit(s, x):
    return s & ~(1<<(x-1))
    
def get_category_name_out_of_mask(mask):
    ret = set()
    for i in range(Category.N_CATEGORIES):
        if (mask & (1<<i)) == 0:
            ret.add(Category.CATEGORY_ID_TO_NAME[i])
    return ret  

class Roll: 
    def __init__(self, roll):
        self._roll = list(roll)
        assert(len(roll) == Category.N_DICES)
        self.rebuild_hist()

    def any_xle(self, n):
        for v in self._hist.values():
            if v == n:
                return True
        return False
    
    def any_double(self):
        return self.any_xle(2)
    
    def any_triple(self):
        return self.any_xle(3)
    
    def any_quadruple(self):
        return self.any_xle(4)
    
    def has_yahtzee(self):
        return self.any_xle(5)
    
    def has_full_house(self):
        if self.any_double() and self.any_triple():
            return True
        return False
    
    def has_x(self, x):
        return x in self._hist
    
    def has_3_of_a_kind(self):
        return self.has_yahtzee() or self.any_quadruple() or self.any_triple()
    
    def has_4_of_a_kind(self):
        return self.has_yahtzee() or self.any_quadruple()
    
    def has_5_of_a_kind(self):
        return self.has_yahtzee()  
    
    def has_small_straight(self):
        return (1 in self._hist and 2 in self._hist and 3 in self._hist and 4 in self._hist) or \
               (2 in self._hist and 3 in self._hist and 4 in self._hist and 5 in self._hist) or \
               (3 in self._hist and 4 in self._hist and 5 in self._hist and 6 in self._hist)
    
    def has_large_straight(self):
        return len(self._hist) == 5 and (1 not in self._hist or 6 not in self._hist)
    
    def get_point_xs(self, x):
        if x not in self._hist:
            return 0
        return self._hist[x] * x
        
    def rebuild_hist(self):
        sorted(self._roll)
        self._hist = {}
        for dice in self._roll:
            self._hist.setdefault(dice, 0)
            self._hist[dice] += 1
            
    def get_point_sum(self):
        return sum([v for v in self._roll])
            
    def eval_point(self, category):
        if Category.is_upper_category(category):
            return self.get_point_xs(int(category))
        if category == '3K':
            if self.has_3_of_a_kind(): return self.get_point_sum()
            return 0
        if category == '4K':
            if self.has_4_of_a_kind(): return self.get_point_sum()
            return 0
        if category == 'FH':
            if self.has_full_house(): return 25
            return 0
        if category == 'SS':
            if self.has_small_straight(): return 30
            return 0
        if category == 'LS':
            if self.has_large_straight(): return 40
            return 0
        if category == 'Y':
            if self.has_5_of_a_kind(): return 50
            return 0
        if category == 'C':
            return self.get_point_sum()
        
        print 'no such category'
        return 0
    
from itertools import combinations_with_replacement
def eval_point_for_all():
    dice = range(1,7)
    for t in combinations_with_replacement(dice,5):
        r = Roll(t)
        #print t, r.eval_point('3K')  
                
if __name__ == '__main__':
    for c in ['1','2','3','4','5','6']:
        print c
        print Category.get_all_possible_point(c)
        
    for c in ['3K','4K','Y','FH','SS','LS','Y','C']:
        print c
        print Category.get_all_possible_point(c)
        
    eval_point_for_all()