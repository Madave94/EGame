from game.individuals.dot import Dot

from random import choice, uniform
from copy import copy

import numpy as np

class Breeder:
    '''
    References used:
    Luke, S. (2013). Essentials of metaheuristics. Lulu.com.
    '''
    def __init__(self, parent):
        self.parent = parent

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
        initializer that allows only individuals with a certain diversity.
        according to (Luke, 2013) Page 32
        """
        population = []
        population.append(Dot(self.parent, color=color))
        while (len(population) < num_individuals):
            individual = Dot(self.parent, color=color)
            if self.check_diversity_population(population, individual):
                population.append(individual)
        
        print("David's population with ",len(population), "individuals and with color", population[0].color[1])
        return population
    
    def check_diversity_population(self, existing_population, new_member):
        for old_member in existing_population:
            if not self.is_diverse(old_member, new_member): 
                print("Is not diverse enough, choose next...")
                return False
        print("Is diverse enough.")
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

    def breed_example_with_ga(self, population):
        """
        application of a basic genetic algorithm for breeding
        """
        population_cpy = copy(population)
        self.evaluate_profession(population)
        dead = []
        alive = []
        for individual in population_cpy:
            if individual.dead:
                dead.append(individual)
            else:
                alive.append(individual)

        for _ in range(len(dead)):
            # get the position where the child should be inserted on the field
            where = choice(alive)._position
            color = alive[0].color

            selected = self.select_with_tournament(population_cpy)
            parent1 = selected[0]
            parent2 = selected[1]
            child1, child2 = self.crossover_swap(copy(parent1), copy(parent2))
            child1 = self.tweak(child1)
            child2 = self.tweak(child2)
            score_child1 = self.assess_individual_fitness(child1)
            score_child2 = self.assess_individual_fitness(child2)
            if self.dominantes(score_child1, score_child2):
                new_individual = Dot(self.parent, color=color, position=where, dna=child1.get_dna())
            else:
                new_individual = Dot(self.parent, color=color, position=where, dna=child2.get_dna())
            population_cpy.append(new_individual)
        for dead_individual in dead:
            population_cpy.remove(dead_individual)
        return population_cpy


    def tweak(self, individual):
        """
        first tweak towards the profession,
        then tweak once completly random or swap genes
        """
        dna = individual.get_dna()
        main_trait = self.evaluate_most_valued_trait(individual)
        increase = uniform(0,0.1)
        perc = dna[0]
        des = dna[1]
        abil = dna[2]
        
        if (main_trait is "survival"):
            perc = self.mutate_dna(
                dna=perc, increase_value=increase, increase=0)
            des = self.mutate_dna(
                dna=des, increase_value=increase, increase=0)
            abil = self.mutate_dna(
                dna=abil, increase_value=increase, increase=0)
        if (main_trait is "attack"):
            perc = self.mutate_dna(
                dna=perc, increase_value=increase, increase=3)
            des = self.mutate_dna(
                dna=des, increase_value=increase, increase=3)
            abil = self.mutate_dna(
                dna=abil, increase_value=increase, increase=2)
        if (main_trait is "defense"):
            perc = self.mutate_dna(
                dna=perc, increase_value=increase, increase=choice((1,5)))
            des = self.mutate_dna(
                dna=des, increase_value=increase, increase=choice((1,5)))
            abil = self.mutate_dna(
                dna=abil, increase_value=increase, increase=choice((2,4)))        
        
        dna = [perc, des, abil]
        if (increase > 0.02):
            next_tweak_slot = choice(range(0,17))
            dna = self.mutate_dna_normal(dna, next_tweak_slot)
        else: 
            dna = self.mutate_dna_shuffle(dna)

        individual.dna_to_traits(self.normalize_dna(dna))
        return individual
    
    def mutate_dna_shuffle(self, dna):
        '''
        swap two traits in perception and traits
        only swap food, opponents or predators traits
        '''
        swap_gene_A = choice((0,3,5))
        swap_gene_B = choice((0,3,5))
        tmp = dna[0][swap_gene_A]
        dna[0][swap_gene_A] = dna[0][swap_gene_B]
        dna[0][swap_gene_B] = tmp
        tmp = dna[1][swap_gene_A]
        dna[1][swap_gene_A] = dna[1][swap_gene_B]
        dna[1][swap_gene_B] = tmp
        return dna        

    def mutate_dna_normal(self, dna, gene):
        '''
        normal mutation, complete random
        '''
        increase = uniform(0, 0.1)
        if gene < 6:
            dna[0][gene] += increase
        elif gene < 12:
            dna[1][gene-6] += increase
        else:
            dna[2][gene-12] += increase
        return dna
    
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

    def crossover_swap(self, solution_a, solution_b):
        '''
        Since the crossover_shift is to explorative the previous
        crossover might be more desireable.
        '''
        dna_a = solution_a.get_dna()
        dna_b = solution_b.get_dna()
        for i in range(len(dna_a)):
            if uniform(0, 1) < 0.5:
                tmp = dna_a[i]
                dna_a[i] = dna_b[i]
                dna_b[i] = tmp
        solution_a.dna_to_traits(dna_a)
        solution_b.dna_to_traits(dna_b)
        return solution_a, solution_b     

    def crossover_shift(self, solution_a, solution_b):
        """
        crossover of two individuals
        changing the traits of a specific category
        hunger (food, seek_food, speed)
        status (poison, health_potion, dodge_poison, seek_potion, poison_resistance)
        aggresion (opponent, predator, seek_opponents, 
                    dodge_predetaors, armor, strength)
        others (corpse, seek_corpses, toxicity)
        Why do crossover like this?
        -> Strategic choice
        Changing abilities independently from each other will give a
        mix of abilities unrelated towards each other, the mutation should do this.
        It turns out then when doing the crossover always the algorithm becomes
        very explorative, thats something we don't want.
        """
        dna_a = solution_a.get_dna()
        dna_b = solution_b.get_dna()
        
        crossover_choice = choice(range(1,100))
        # don't always do crossover
        
        # do hunger crossover
        if ( crossover_choice == 1 ):
            tmp = dna_a[0][0]
            dna_a[0][0] = dna_b[0][0]
            dna_b[0][0] = tmp
            tmp = dna_a[1][0]
            dna_a[1][0] = dna_b[1][0]
            dna_b[1][0] = tmp
            tmp = dna_a[2][1]
            dna_a[2][1] = dna_b[2][1]
            dna_b[2][1] = tmp
        # do status crossover
        if ( crossover_choice == 2 ):
            tmp = dna_a[0][1]
            dna_a[0][1] = dna_b[0][1]
            dna_b[0][1] = tmp
            tmp = dna_a[0][2]
            dna_a[0][2] = dna_b[0][2]
            dna_b[0][2] = tmp
            tmp = dna_a[1][1]
            dna_a[1][1] = dna_b[1][1]
            dna_b[1][1] = tmp
            tmp = dna_a[1][2]
            dna_a[1][2] = dna_b[1][2]
            dna_b[1][2] = tmp
            tmp = dna_a[2][3]
            dna_a[2][3] = dna_b[2][3]
            dna_b[2][3] = tmp
        # do aggresion crossover
        if ( crossover_choice == 3 ):
            tmp = dna_a[0][3]
            dna_a[0][3] = dna_b[0][3]
            dna_b[0][3] = tmp
            tmp = dna_a[0][5]
            dna_a[0][5] = dna_b[0][5]
            dna_b[0][5] = tmp
            tmp = dna_a[1][3]
            dna_a[1][3] = dna_b[1][3]
            dna_b[1][3] = tmp
            tmp = dna_a[1][5]
            dna_a[1][5] = dna_b[1][5]
            dna_b[1][5] = tmp
            tmp = dna_a[2][0]
            dna_a[2][0] = dna_b[2][0]
            dna_b[2][0] = tmp
            tmp = dna_a[2][2]
            dna_a[2][2] = dna_b[2][2]
            dna_b[2][2] = tmp
        # do other crossover
        if ( crossover_choice == 4 ):
            tmp = dna_a[0][4]
            dna_a[0][4] = dna_b[0][4]
            dna_b[0][4] = tmp
            tmp = dna_a[1][4]
            dna_a[1][4] = dna_b[1][4]
            dna_b[1][4] = tmp
            tmp = dna_a[2][4]
            dna_a[2][4] = dna_b[2][4]
            dna_b[2][4] = tmp
  
        solution_a.dna_to_traits(self.normalize_dna(dna_a))
        solution_b.dna_to_traits(self.normalize_dna(dna_b))
        return solution_a, solution_b

    def normalize_dna(self, dna):
        dna[0] = dna[0] / sum(dna[0])
        dna[1] = dna[1] / sum(dna[1])
        dna[2] = dna[2] / sum(dna[2])
        return dna

    def select_with_tournament(self, population):
        """
        selects four parents with replacement and the same main trait
        and uses the two strongest to breed
        """
        parents = []
        choice_A = choice(population)
        main_trait = self.evaluate_most_valued_trait(choice_A)
        choice_B = self.choose_parent_candidate(population, main_trait)
        choice_C = self.choose_parent_candidate(population, main_trait)
        choice_D = self.choose_parent_candidate(population, main_trait)
        
        winner_one = self.binary_tournament(choice_A, choice_B, main_trait)
        winner_two = self.binary_tournament(choice_C, choice_D, main_trait)
        
        parents.append(winner_one)
        parents.append(winner_two)
        
        return parents
    
    def choose_parent_candidate(self, population, main_trait):
        '''
        chooses other parent with the same main trait
        '''
        choice_next = None       
        other_trait = 100
        while (other_trait != main_trait):
            choice_next = choice(population)
            other_trait = self.evaluate_most_valued_trait(choice_next)
        return choice_next
          
    def binary_tournament(self, individual, otherIndividual, main_trait):
        '''
        Domination Binary Tournament Selection
        '''
        if (self.assess_individual_fitness(individual)[main_trait] >
                      self.assess_individual_fitness(otherIndividual)[main_trait]):
            return individual
        elif (self.assess_individual_fitness(otherIndividual)[main_trait] >
                        self.assess_individual_fitness(individual)[main_trait]):
            return otherIndividual
        else:
            return individual

    def dominantes(self, individual, otherIndividual):
        '''
        evaluate pareto dominance of two individuals towards each other.
        '''
        dominating = False
        for key, val in individual.items():
            if (val > otherIndividual[key]):
                dominating = True
            elif (val < otherIndividual[key]):
                return False
        return dominating

    def assess_individual_fitness(self, individual):
        """
        making a multi-objective optimization out of that
        fitness that depends on 3 aspects more or less valued
        survival, attacking, defense
        """
        statistic = individual.statistic
        score = {}
        score["survival"] = statistic.time_survived/100 + statistic.food_eaten - statistic.food_seen
        score["attack"] = statistic.enemies_attacked + statistic.consumed_corpses - statistic.opponents_seen
        score["defense"] = statistic.time_survived/100 + statistic.attacked_by_opponents + statistic.attacked_by_predators
        # perception_dna_array = [0][x]
        #   food =               [0][0]
        #   poison =             [0][1]
        #   health_potion =      [0][2]
        #   opponent =           [0][3]
        #   corpse =             [0][4]
        #   predator =           [0][5]
        # desires_dna_array =    [1][x]
        #   seek_food =          [1][0]
        #   dodge_poison =       [1][1]
        #   seek_potion =        [1][2]
        #   seek_opponents =     [1][3]
        #   seek_corpse =        [1][4]
        #   dodge_predators =    [1][5]
        # abilities_dna_array =  [2][x]
        #   armor_ability =      [2][0]
        #   speed =              [2][1]
        #   strength =           [2][2]
        #   poison_resistance =  [2][3]
        #   toxicity =           [2][4]

        return score
    
    def evaluate_most_valued_trait(self, individual):
        '''
        Which trait is valued the most?
        survival
        attack
        defense
        '''
        dna = individual.get_dna()
        survival = (float) (dna[0][0] + dna[1][0])
        attack = (float) (dna[0][3] + dna[1][3])
        defense = (float) (dna[0][2] + dna[0][5] + dna[1][2] + dna[1][5]) / 2
        if survival > (attack and defense ): return "survival"
        if attack > defense: return "attack"
        return "defense"

    def evaluate_profession(self, population):
        survival = 0
        attack = 0
        defense = 0
        for individual in population:
            trait = self.evaluate_most_valued_trait(individual)
            if (trait is "survival"): survival += 1
            if (trait is "attack"): attack += 1
            if (trait is "defense"): defense += 1
        print("survival: ", str(survival), "\nattack: ", str(attack), "\ndefense: ", str(defense) )
        