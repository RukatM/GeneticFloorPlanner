class Chromosome:
    """
    Represents a single room in building layout
    """
    def __init__(self, room_type, x, y,width,height):
        self.room_type = room_type
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def get_area(self):
        return self.width * self.height
    
    def to_list(self):
        return [self.room_type,self.x,self.y,self.width,self.height]
    
    def __repr__(self):
        return (f"Chromosome(type='{self.room_type}', x={self.x}, y={self.y}, "
                f"w={self.width}, h={self.height})")
