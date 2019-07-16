from game.individuals.dot import Dot

from random import choice, uniform
from copy import copy

import numpy as np

class Breeder:
    def __init__(self, parent):
        self.parent = parent
        self.profession = {"Attacker":0,"Defender":0}

    def breed(self, population):
        """
        this function gets called by the EGame on one population
        it gets a population consisting of individuals
        each individual has certain statistics and traits
        """
        # return self.breed_copy_dead_example(population)
        return self.breed_example_with_ga(population)

    def initialize_population(self, num_individuals, color):
        """
        this function gets calles by EGame before the first frame
        it gets the number of individuals which have to be generated
        also, it gets the color of the population
        """
        return self.initialize_population_min_diversity(num_individuals, color)
    
    def initialize_population_min_diversity(self, num_individuals, color):
        """
        There will be 5 diverse individuals and 5 attackers.
        
        initializer that allows only individuals with a certain diversity.
        according to (Luke, 2013) Page 32
        """
        population = []
 
        for _ in range(0,5):
            aggresive_individual = Dot(self.parent, color=color)
            dna = aggresive_individual.get_dna()
            dna = self.create_attacker_dna(dna)
            aggresive_individual.dna_to_traits(dna)
            population.append(aggresive_individual)
        
        while (len(population) < num_individuals):
            individual = Dot(self.parent, color=color)
            if self.check_diversity_population(population, individual):
                population.append(individual)
        
        print("Davidson's ready to conqure in", population[0].color[1], "!")
        return population
    
    def check_diversity_population(self, existing_population, new_member):
        for old_member in existing_population:
            if not self.is_diverse(old_member, new_member): 
                #print("Is not diverse enough, choose next...")
                return False
        #print("Is diverse enough.")
        return True

    def is_diverse(self, old_member, new_member, accuracy=2):
        """
        checks if if two individuals are similar in there dna
        if they are not similar the function returns true
        adjust the accuracy to change the rounded number
        2 seems to be a good number for the initialization procedure
        """
        isDiverse = True
        old_member = old_member.get_dna()
        new_member = new_member.get_dna()
        
        for dna in range(0,3):
            for sub_trait in range(0,5):
                if round(old_member[dna][sub_trait], accuracy) == round(new_member[dna][sub_trait], accuracy):
                     return False
        # check the two members that are not so easily iterateable
        if round(old_member[0][5], accuracy) == round(new_member[0][5], accuracy):
            return False
        if round(old_member[1][5], accuracy) == round(new_member[1][5], accuracy):
            return False  
        
        return isDiverse

    def init_attacker(self, where, color):
        '''
        initialize aggressive individual
        '''
        new_individual = Dot(self.parent, color=color, position = where)
        dna = new_individual.get_dna()
        dna = self.create_attacker_dna(dna)
        new_individual.dna_to_traits(dna)
        return new_individual

    def init_defender(self, where, color):
        '''
        initialize maximal defensive individual
        '''
        perc = [0,0.5,0,0,0,0.5]
        des = [0,0.5,0,0,0,0.5]
        abil = [0.2,0.2,0.2,0.2,0.2]
        dna = [perc, des, abil]
        new_individual = Dot(self.parent, color=color, position = where, dna=dna)
        return new_individual
    
    def create_attacker_dna(self, dna):
        '''
        increase the traits important for attackers
        perception opponents
        desire opponents
        strength
        '''
        dna[0][3] = uniform(0.5,1)
        dna[1][3] = uniform(0.5,1)
        dna[2][2] = uniform(0.5,1)
        dna = self.normalize_dna(dna)
        return dna
    
    def normalize_dna(self, dna):
        dna[0] = dna[0] / sum(dna[0])
        dna[1] = dna[1] / sum(dna[1])
        dna[2] = dna[2] / sum(dna[2])
        return dna
    
    def breed_example_with_ga(self, population):
        """
        application of a basic genetic algorithm for breeding
        """
        population_cpy = copy(population)
        dead = []
        alive = []
        for individual in population_cpy:
            if individual.dead:
                dead.append(individual)
            else:
                alive.append(individual)
        
        self.count_professions_in_population(alive)
        
        for _ in range(len(dead)):
            # get the position where the child should be inserted on the field
            where = choice(alive)._position
            color = alive[0].color
            
            if self.profession["Attacker"] < len(alive)/2:
                new_individual = self.init_attacker(where, color)
                population_cpy.append(new_individual)
                self.profession["Attacker"] += 1
                continue

            selected = self.select_example(population_cpy)
            parent1 = selected[0]
            parent2 = selected[1]
            child1, child2 = self.crossover_example(copy(parent1), copy(parent2))
            child1 = self.tweak_example(child1)
            child2 = self.tweak_example(child2)
            score_child1 = self.assess_individual_fitness(child1)
            score_child2 = self.assess_individual_fitness(child2)
            if score_child1 > score_child2:
                new_individual = Dot(self.parent, color=color, position=where, dna=child1.get_dna())
            else:
                new_individual = Dot(self.parent, color=color, position=where, dna=child2.get_dna())
            population_cpy.append(new_individual)
        for dead_individual in dead:
            population_cpy.remove(dead_individual)
        print("Davidson's with ", len(population_cpy), " individuals, ready for the next round!")
        return population_cpy

    def tweak_example(self, individual):
        """
        we want to increase the trait to seek food and increase armor
        """

        dna = individual.get_dna()
        increase = uniform(0, 0.1)

        perc = dna[0]
        des = dna[1]
        abil = dna[2]

        perc = self.mutate_dna(
            dna=perc, increase_value=increase, increase=choice(range(0,6)))
        des = self.mutate_dna(
            dna=des, increase_value=increase, increase=choice(range(0,6)))
        abil = self.mutate_dna(
            dna=abil, increase_value=increase, increase=choice(range(0,5)))

        dna = [perc, des, abil]
        if (increase > 0.08): self.mutate_dna_shuffle(dna)
        individual.dna_to_traits(dna)
        return individual

    def mutate_dna(self, dna, increase_value, increase):
        # select some other dna to be decreased
        choices = [i for i in range(len(dna))]
        choices.remove(increase)
        decreased = False
        while not decreased:
            decrease = choice(choices)
            if dna[decrease] - increase_value >= 0.0:
                dna[decrease] -= increase_value
                decreased = True
            else:
                choices.remove(decrease)
            if len(choices) == 0:
                break
        # if we were able to reduce the value for the other dna -> increase the desired dna
        if decreased:
            # increase the value
            dna[increase] += increase_value if dna[increase] <= 1.0 else 1.0
        # otherwise we cannot do anything
        return dna
    
    def mutate_dna_shuffle(self, dna):
        '''
        swap two traits in perception and traits
        only swap food, opponents or predators traits
        '''
        swap_gene_A = choice(range(0,6))
        swap_gene_B = choice(range(0,6))
        tmp = dna[0][swap_gene_A]
        dna[0][swap_gene_A] = dna[0][swap_gene_B]
        dna[0][swap_gene_B] = tmp
        tmp = dna[1][swap_gene_A]
        dna[1][swap_gene_A] = dna[1][swap_gene_B]
        dna[1][swap_gene_B] = tmp
        return dna  


    def crossover_example(self, solution_a, solution_b):
        """
        crossover of two individuals
        """
        dna_a = solution_a.get_dna()
        dna_b = solution_b.get_dna()
        for i in range(len(dna_a)):
            if uniform(0, 1) < 0.2:
                tmp = dna_a[i]
                dna_a[i] = dna_b[i]
                dna_b[i] = tmp
        solution_a.dna_to_traits(dna_a)
        solution_b.dna_to_traits(dna_b)
        return solution_a, solution_b

    def select_example(self, population):
        """
        example select
        """
        fitness_array = np.empty([len(population)])
        for i in range(len(population)):
            score = self.assess_individual_fitness(population[i])
            fitness_array[i] = score
        
        # span value range
        for i in range(1, len(fitness_array)):
            fitness_array[i] = fitness_array[i] + fitness_array[i - 1]
        
        parents = self.selectParentSUS(population, fitness_array, 2)
        return parents

    def selectParentSUS(self, population, fitness_array, count):
        """
        Stochastic uniform sampling
        """
        individual_indices = []
        # build the offset = random number between 0 and f_l / n
        offset = uniform(0, fitness_array[-1] / count)
        # repeat for all selections (n)
        for _ in range(count):
            index = 0
            # increment the index until we reached the offset
            while fitness_array[index] < offset:
                index += 1
            # increment the offset to the next target
            offset = offset + fitness_array[-1] / count
            individual_indices.append(population[index])
        # return all selected individual indices
        return np.array(individual_indices)

    def count_professions_in_population(self, population):
        '''
        Count how many attackers are in the population
        '''
        self.profession["Attacker"] = 0
        self.profession["Defender"] = 0
        for individual in population:
            if self.check_profession(individual) is "Attacker": self.profession["Attacker"] += 1
            else: self.profession["Defender"] += 1
        for key, val in self.profession.items():
            print(key, ": ", val)
            
    def check_profession(self, individual):
        '''
        If the desire and perception to attack opponents is larger enough 
        (attacker_threshold) then the  we consider an individual as an Attacker
        '''
        attacker_threshold = 0.35
        dna = individual.get_dna()
        if (dna[0][3] and dna[1][3]) > attacker_threshold: return "Attacker"
        return "Defender"

    def assess_individual_fitness(self, individual):
        """
        fitness score depending on several factors:
        - individuals that didn't survive at least one iteration get a 0
        x food rating: how much food did the individual see and how much did it eat?
        - poison rating: how much poison did the individual see and still did it eat?
        - potion rating: did the individual consume many of the potions it saw?
        - predataor rating: can the individual see a predetaor and avoid it?
        """
        statistic = individual.statistic
        iterations_survied = int(statistic.time_survived / 300)
        if (iterations_survied is 0): return 0
        #food_rating = (statistic.food_eaten - statistic.food_seen) / iterations_survied
        poison_rating = (statistic.poison_seen - statistic.poison_eaten) / iterations_survied
        potion_rating = (statistic.consumed_potions - statistic.potions_seen) / iterations_survied
        predator_rating = (statistic.predators_seen - statistic.attacked_by_predators) / iterations_survied
        score = iterations_survied + poison_rating + potion_rating + predator_rating
        return score