__author__ = "Lars van Gemerden"  
__date__   = "$13-3-2015 12:10:22$"


class Caching(object):
    '''
    Instances of this class can be used as a decorator to provide caching of
    the return value of the function, given the arguments of the function call. 
    It can be used for any function or method, but note the limitations below.
    
    A typical use case would be a calculation intensive method, that will always 
    return the same result, given the same arguments.  
    
    Arguments:
        - max_size (optional): indicates the maximum cache size for each 
            decorated function. If the cache becomes larger it will be emptied
            and the return value will be recalculated,
        - for __call__:
            - func: the function to be decorated,
        - for clear():
            - no arguments clears all the caches in the instance,
            - finder: clears the cache of one specific decorated method or
                function,
            - *args: clears the calulated result for finder(*args).
            
    Limitations:
        - In this version no keyword arguments for the decorated function are 
            allowed, although this could easily be added,
        - As with any caching mechanism, if the return value of a decorated 
            function changes for a set of argument values, the value in the 
            cache becomes invalid and clear(..) must be called to empty the cache.
        - Arguments of the decorated function must be hashable, e.g. list 
            arguments are not allowed.
        
    Usage: see bottom of file
    
    Note: the decorated function (finder) is used as key for the caches instead 
        of the original function, in order to be able to clear the cache by 
        function (the original function is not in the namespace of the file or
        class it was defined in).
        
    Discussion:
        - This method could be slightly faster by defining a separate finder
            method when max_size = 0 (unlimited). Since the nature of caching
            says that func is somewhat slow and the cache should be hit more 
            often then the actual calculation, this was omitted for simplicity
            sake.
        - This could be expanded by keeping track of the number of calls for
            different aruments for each decorated function
    '''
    
    def __init__(self, max_size=0): 
        self.caches = {} #only used to be able to clear caches
        self.max_size = max_size
        
    def __call__(self, func):
        max_size = self.max_size
        def finder(*args):
            try:
                return cache[args]
            except KeyError:
                if 0 < max_size <= len(cache): 
                    cache.clear()
                result = cache[args] = func(*args) #actual calculation
                return result            
        cache = self.caches[finder] = {} #use finder as key (not func; see Note)
        return finder
    
    def clear(self, finder=None, *args):
        if finder:
            cache = self.caches[finder]
            if len(args):
                if args in cache:
                    del cache[args]
            else:
                cache.clear()
        else:
            for cache in self.caches.itervalues():
                cache.clear()
                
                
def simple_caching(func):
    '''
    very basic version of the above: caches cannot be cleared at all; same limitations
    apply.
    '''
    cache = {} #stored in closure of finder()
    def finder(*args):
        try:
            return cache[args]
        except KeyError:
            result = cache[args] = func(*args) #actual calculation
            return result            
    return finder
    

if __name__ == "__main__":
    
    #BASIC USAGE
    caching = Caching()
    
    @caching
    def get(x, *args):
        return x, [a for a in args]
    
    get(1) #added to cache
    assert caching.caches[get][(1,)] == (1, [])
    get(2, 3) #added to cache
    assert caching.caches[get][(2,3)] == (2, [3])
    caching.clear()
    assert (2,3) not in caching.caches[get]
    get(2, 3) #added to cache
    assert (2,3) in caching.caches[get]
    
    #CLEARING
    caching = Caching(max_size=2) 
    
    @caching
    def get(x):
        return x

    get(11), get(12), get(12) #fill cache
    assert len(caching.caches[get]) == 2
    get(13) #third argument value: cache is cleared
    assert len(caching.caches[get]) == 1
    caching.clear(get) #clear cache for the decorated function get()
    assert len(caching.caches[get]) == 0
    get(15), get(16) #fill cache
    caching.clear(get, 15) 
    assert len(caching.caches[get]) == 1
    
    #LIMITS
    caching = Caching()
    changing = 0
    
    @caching
    def get():
        return changing
    
    get() #cache set
    assert get() == 0 #from cache
    changing = 1
    if get() != 1: #still from cache
        print "cache out of date" 
        
    @caching
    def get2(x):
        return x
    try:
        get2([1,2])
    except TypeError:
        print "unhashable argument type"
        
    #SIMPLE CACHING
    @simple_caching
    def get(x):
        return x
    
    get(1) #to cache
    get(2) #to cache
    get(1) #from cache
    
    
    
    
    