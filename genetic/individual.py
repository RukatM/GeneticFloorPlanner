from .chromosome import Chromosome

class Individual:
    """
    Represents a single building layout
    """
    def __init__(self, chromosomes=None, fitness=None):
        self.chromosomes = chromosomes if chromosomes is not None else []
        self.fitness = fitness
    
    def __repr__(self):
        return (f"Individual(num_rooms={len(self.chromosomes)}, "
                f"fitness={self.fitness})")

