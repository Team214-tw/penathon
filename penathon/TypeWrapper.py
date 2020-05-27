class TypeWrapper:
    def __init__(self, t, class_name=None):
        self.type = t
        self.class_name = class_name

    def is_list(self):
        return self.class_name == 'list'
    
    def reveal(self):
        return self.type
