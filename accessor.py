__author__ = "Lars van Gemerden"
__date__ = "$11-Feb-2015 12:41:24$"


from inspect import isfunction

_marker = object() 

class accessor(object):
    '''
    descriptor to be able to validate type and value of attributes on setting;
        - initial value can be set
        - type and initial value can be functions,
        - validation can depend on object for which the attribute is set
        - see below for usage
    '''
    
    def __init__(self, type_, init=_marker, valid=None): 
        self.__type = type_
        self.__init = init
        self.__valid = valid
        
    def _type(self, obj):
        if isfunction(self.__type):
            return self.__type(obj)
        return self.__type
    
    def _init(self, obj):
        if isfunction(self.__init):
            return self.__init(obj)
        return self.__init
    
    def __get__(self, obj, cls=None):
        if obj is None:
            return self
        try:
            return obj.__dict__[self.name]
        except KeyError:
            raise AttributeError("'%s' object has no attribute '%s'" % (cls.__name__, self.name))
    
    def __set__(self, obj, value):
        obj.__dict__[self.name] = self._validate(obj, value)
        
    def _validate(self, obj, value):
        if value is None or value is _marker:
            return value
        if not isinstance(value, self._type(obj)):
            raise ValueError("incorrect type for '%s' in '%s'" % (self.name, type(obj).__name__))
        if self.__valid and not self.__valid(obj, value):
            raise ValueError("invalid value for '%s' in '%s'" % (self.name, type(obj).__name__))
        return value
                
    def set_init(self, obj):
        if self.__init is not _marker:
            setattr(obj, self.name, self._init(obj))



class accessor_meta(type):
    '''adds names of accessors to a class attribute __names__ for faster iteration and
        adds name to accessor to simplify use of accessors in classes'''
    def __init__(cls, name, bases, cls_dict):
        for name, attr in cls_dict.iteritems():
            if isinstance(attr, accessor):
                attr.name = name
        super(accessor_meta, cls).__init__(name, bases, cls_dict)
        cls.__names__ = set()
        for c in cls.mro():
            for name, attr in c.__dict__.iteritems():
                if isinstance(attr, accessor):
                    cls.__names__.add(name)
        
class Validated(object):
    
    '''subclasses of Validated that can only have accessor managed attributes
        and all accessor managed attributes are type checked and can be validated'''
    
    __metaclass__ = accessor_meta
    
    def __init__(self, **kw):
        for name in self.__class__.__names__:
            if name in kw:
                setattr(self, name, kw.pop(name))
            else:
                getattr(self.__class__, name).set_init(self)
        super(Validated, self).__init__(**kw)
        
    def __setattr__(self, name, value):
        if name not in self.__class__.__names__:
            raise AttributeError("attribute '%s' in '%s' cannot be set; it has no accessor" % (name, self.__class__.__name__))
        super(Validated, self).__setattr__(name, value)
        
    def __str__(self):
        return "{cls}({attrs})".format(cls=self.__class__.__name__, 
                                       attrs=", ".join("{k}: {v}".format(k=k, v=getattr(self, k, None)) for k in self.__class__.__names__))
            
        
if __name__ == "__main__":
    
    class Person(Validated):
        
        name = accessor(str)
        age = accessor(int, init=0, valid=lambda s, v: v>=0)
        spouse = accessor(lambda s: Person, valid=lambda s, v: s.valid_spouse(v))
        
        def valid_spouse(self, obj):
            return self is not obj and self.age>=18 and obj.age>=18
        
    bob = Person(name="bob")
    bob.age = 26
    ann = Person(name="ann", age=21)
    mia = Person(name="mia", age=14)
    bob.spouse = ann
    print bob
    print ann
    print mia
    try:
        bob.name = 3 #wrong type
    except ValueError as e:
        print e.message
    try:
        err = Person(name="err", age=-1) #age must be >=0
    except ValueError as e:
        print e.message
    try:
        bob.hair = "brown" #"hair" is not a controled attribute
    except AttributeError as e:
        print e.message 
    try:
        ann.spouse = mia #mia is underaged
    except ValueError as e:
        print e.message
    
    