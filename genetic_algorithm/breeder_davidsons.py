from game.individuals.dot import Dot

from random import choice, uniform
from copy import copy

import numpy as np

class Breeder:
    '''
    General outcomes:
    I tried different approaches (first quite random, second multi-objective and this one with the professions).
    It turns out that the assumed domain knowledge does no necessarily lead to better outcomes (~bias).
    -> Assuming we know thinks that turn out to be exactly the opposite.
    A completely random breeder might perform decently enough with only a fitness criteria for the survival time.
    However, for the task I assume that my population needs a certain aggressiveness in order to win the game against
    passive population, i guarantee this by dividing the population into two professions.
    
    The general Strategy here is:
    Update the strategy (distribution of professions).
    Breed the two professions only with each other using two different fitness measurement depending on the profession.
    Tweak them only in certain directions depending on their profession.
    
    parameters to set to increase/decrease exploration and exploitation
    default 5, 0.35, 0.025, False, True, False
    Sampling for performance with this settings:
    Performance against aggressive: Won 19:6 
    Performance against passive: Won 7:3
    
    attacker_number: sets the minimum number of attackers, setting this value to 10 will create population
        only consisting of aggressive individuals. increasing the value above 10 doesn't have any effect.
        range 0-10.
    attacker_threshold: this value is used to decide when individuals are considered as attackers, if the
        threshold is low the aggressiveness will decrease, the value should at least stay above 1/6
    crossover_chance: change the crossover chance, I decreased the crossover very much.
    defender_random_init: If this is true, no bias for the initial defender population will be applied, an instead a
        number of maximal diverse individuals will be initialized.
    adoptive_strategy: turn this on to change the number of professions dynamically during runtime.
    '''
    attacker_number = 5 
    attacker_threshold = 0.35
    crossover_chance = 0.025
    defender_random_init = False
    adoptive_strategy = True
    intermediate_output = False
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
        return self.breed_depending_on_profession(population)

    def initialize_population(self, num_individuals, color):
        """
        this function gets calles by EGame before the first frame
        it gets the number of individuals which have to be generated
        also, it gets the color of the population
        """
        return self.initialize_population_min_diversity(num_individuals, color)
    
    def initialize_population_min_diversity(self, num_individuals, color):
        """
        There will be the set number of individuals. Either the individuals are initialized with a bias
        or with a diversity measurement.
        
        initializer that allows only individuals with a certain diversity.
        according to (Luke, 2013) Page 32
        """
        population = []
 
        for _ in range(0,self.attacker_number):
            aggresive_individual = Dot(self.parent, color=color)
            dna = aggresive_individual.get_dna()
            dna = self.create_attacker_dna(dna)
            aggresive_individual.dna_to_traits(dna)
            population.append(aggresive_individual)
        
        if (self.defender_random_init):
            while (len(population) < num_individuals):
                individual = Dot(self.parent, color=color)
                if self.check_diversity_population(population, individual):
                    population.append(individual)
        else:
            for _ in range(0,num_individuals-self.attacker_number):
                defensive_individual = Dot(self.parent, color=color)
                dna = defensive_individual.get_dna()
                dna = self.create_defender_dna(dna)
                defensive_individual.dna_to_traits(dna)
                population.append(aggresive_individual)
        
        print("Davidson's ready to conquer in", population[0].color[1], "!")
        return population
    
    def check_diversity_population(self, existing_population, new_member):
        '''
        Compares the new individual with the other individuals in the population.
        It works somehow like pareto dominance checking but not with dominance, instead with diversity.
        '''
        for old_member in existing_population:
            if not self.is_diverse(old_member, new_member): 
                #print("Is not diverse enough, choose next...")
                return False
        #print("Is diverse enough.")
        return True

    def is_diverse(self, old_member, new_member, accuracy=3):
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
        initialize defender individual
        '''
        new_individual = Dot(self.parent, color=color, position = where)
        dna = new_individual.get_dna()
        dna = self.create_defender_dna(dna)
        new_individual.dna_to_traits(dna)
        return new_individual
    
    def create_attacker_dna(self, dna):
        '''
        increase the traits important (assumption) for attackers
        perception opponents
        desire opponents
        strength
        '''
        dna[0][3] = uniform(0.5,1)
        dna[1][3] = uniform(0.5,1)
        dna[2][2] = uniform(0.5,1)
        dna = self.normalize_dna(dna)
        return dna
    
    def create_defender_dna(self, dna):
        '''
        decrease the traits unimportant (assumption) for defenders
        and increase the one important (assumption) to survive
        '''
        dna[0][3] = 0
        dna[1][3] = 0
        dna[0][5] += 0.2
        dna[1][0] += 0.2
        dna[1][1] += 0.2
        dna[1][5] += 0.2
        dna = self.normalize_dna(dna)
        return dna
    
    def traits_to_tweak(self, profession):
        '''
        depending on the profession different traits will be randomly chosen for the tweak
        '''
        if (profession is "Attacker"):
            perc = (3,3)
            des = (3,3)
            abil = (2,2)
            return perc, des, abil
        else:
            perc = (0,1,2,3,4,5)
            des = (0,1,2,3,4,5)
            abil = (0,1,2,3,4)
            return perc, des, abil
    
    def normalize_dna(self, dna):
        dna[0] = dna[0] / sum(dna[0])
        dna[1] = dna[1] / sum(dna[1])
        dna[2] = dna[2] / sum(dna[2])
        return dna
    
    def breed_depending_on_profession(self, population):
        """
        Depending on the initially set number of profession new individuals will be added
        to our population. The parameters can be found in the beginning of the class.
        
        attackers breed new attackers only with attackers.
        defenders can be breeded by all.
        
        we will take both breeded individuals not only one, so no score is evaluated.
        If only one can be chosen its just the first one, this is random since the
        parents have been chosen randomly before.
        """
        if self.adoptive_strategy:
            self.update_strategy(population)
        population_cpy = copy(population)
        dead = []
        alive = []
        for individual in population_cpy:
            if individual.dead:
                dead.append(individual)
            else:
                alive.append(individual)
        
        all_attacker = self.create_attacker_population(population_cpy)
        all_defender = self.create_defender_population(population_cpy)
        self.count_professions_in_population(alive)
        if (self.intermediate_output):
            print("The survivers of the last round:")
            self.print_professions()
        
        needed_individuals = len(dead)
        index = 0
        while index < needed_individuals:
            # get the position where the child should be inserted on the field
            where = choice(alive)._position
            color = alive[0].color
                        
            # get the desired number of attackers and defenders
            if self.profession["Attacker"] < self.attacker_number:
                selected = self.select_individual(all_attacker)
                profession_flag = True
            else:
                selected = self.select_individual(population_cpy)
                profession_flag = False
            
            parent1 = selected[0]
            parent2 = selected[1]
            child1, child2 = self.crossover_example(copy(parent1), copy(parent2))
            child1 = self.tweak_depending_on_profession(child1)
            child2 = self.tweak_depending_on_profession(child2)
            #score_child1 = self.assess_individual_fitness(child1)
            #score_child2 = self.assess_individual_fitness(child2)
            if needed_individuals - index > 2:
                new_individual = Dot(self.parent, color=color, position=where, dna=child1.get_dna())
                population_cpy.append(new_individual)
                index += 1
                if profession_flag: self.profession["Attacker"] += 1
                else: self.profession["Defender"] +=1
                new_individual = Dot(self.parent, color=color, position=where, dna=child2.get_dna())
            else:
                new_individual = Dot(self.parent, color=color, position=where, dna=child1.get_dna())
            population_cpy.append(new_individual)
            index += 1
            if profession_flag: self.profession["Attacker"] += 1
            else: self.profession["Defender"] +=1
        for dead_individual in dead:
            population_cpy.remove(dead_individual)
        if (self.intermediate_output):
            print("Davidson's with ", len(population_cpy), " individuals, ready for the next round!")
            self.print_professions()
        return population_cpy

    def tweak_depending_on_profession(self, individual):
        """
        we want to tweak the individual depending on the profession
        First the profession is checked.
        Depending on the profession the decision is made which traits are tweaked.
        
        The dna_shuffel is something used instead of the crossover. (while the crossover is
        still activated anyways but with a low value).
        """
        profession = self.check_profession(individual)
        p,d,a = self.traits_to_tweak(profession)
        dna = individual.get_dna()
        increase = uniform(0, 0.1)

        perc = dna[0]
        des = dna[1]
        abil = dna[2]

        perc = self.mutate_dna(
            dna=perc, increase_value=increase, increase=choice(p))
        des = self.mutate_dna(
            dna=des, increase_value=increase, increase=choice(d))
        abil = self.mutate_dna(
            dna=abil, increase_value=increase, increase=choice(a))

        dna = [perc, des, abil]
        if (increase > 0.09): self.mutate_dna_shuffle(dna)
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
        swap two traits in perception and desire,
        this is necessary so that individuals can adjust their behaviour rapidly 
        it is somehow a substitute for the crossover.
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
        The crossover is set to a very low value so it doesn't happen to often.
        I basically tried different parameters and it turns out that a lower crossover
        improves my individuals, I suppose this is related to the two professions.
        """
        dna_a = solution_a.get_dna()
        dna_b = solution_b.get_dna()
        for i in range(len(dna_a)):
            if uniform(0, 1) < self.crossover_chance:
                tmp = dna_a[i]
                dna_a[i] = dna_b[i]
                dna_b[i] = tmp
        solution_a.dna_to_traits(dna_a)
        solution_b.dna_to_traits(dna_b)
        return solution_a, solution_b

    def select_individual(self, population):
        """
        The chosen selection method seems to work fine.
        I tried to use a tournament selection instead, 
        The influence appears to be neglectable.
        More of a "meta-selection" is made in the strategy definition earlier,
        this can be only seen as the last steps in my selection procedure.
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
        In my fitness I guranteed that no individual has a very low fitness,
        so here still every individual has a chance to be chosen. 
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

    def create_attacker_population(self, population):
        all_attacker = []
        for individual in population:
            if "Attacker" is self.check_profession(individual):
                all_attacker.append(individual)
        return all_attacker
    
    def create_defender_population(self, population):
        all_defender = []
        for individual in population:
            if "Defender" is self.check_profession(individual):
                all_defender.append(individual)
        return all_defender

    def count_professions_in_population(self, population):
        '''
        Count how many attackers are in the population
        '''
        self.profession["Attacker"] = 0
        self.profession["Defender"] = 0
        for individual in population:
            if self.check_profession(individual) is "Attacker": self.profession["Attacker"] += 1
            else: self.profession["Defender"] += 1

    def print_professions(self):
        for key, val in self.profession.items():
            print(key, ": ", val)
            
    def check_profession(self, individual):
        '''
        If the desire and perception to attack opponents is larger enough 
        (attacker_threshold) then the  we consider an individual as an Attacker
        '''
        dna = individual.get_dna()
        if (dna[0][3] and dna[1][3]) > self.attacker_threshold: return "Attacker"
        return "Defender"

    def assess_individual_fitness(self, individual):
        """
        fitness score depending on several factors:
        - individuals that didn't survive at least one iteration get a 0
        x food rating: how much food did the individual see and how much did it eat?
        - poison rating: how much poison did the individual see and still did it eat?
        x potion rating: did the individual consume many of the potions it saw?
        - predator rating: can the individual see a predator and avoid it?
        
        x = unused fitness ratings.
        
        The number of survived iterations is divided by the number of frames, to somehow make the values more
        close to each other. So for each breeding session the individual will get +1 on its counter.
        I decided to exclude the dna entirely from the assessment rating and only use the statistics.
        I do this since I dont want to reward my individuals for having only a desireable DNA set based on my
        assumption (since we know they could be wrong). For the ratings (same for the strategy) I always tought,
        what does my individual want to do? The individual should see the predetaor but should not get attacked from them etc.!
        """
        statistic = individual.statistic
        iterations_survied = int(statistic.time_survived / 300)
        if (iterations_survied is 0): return 0.5
        #food_rating = (statistic.food_eaten - statistic.food_seen) / iterations_survied
        poison_rating = (statistic.poison_seen - statistic.poison_eaten) / iterations_survied
        #potion_rating = (statistic.consumed_potions - statistic.potions_seen) / iterations_survied
        predator_rating = (statistic.predators_seen - statistic.attacked_by_predators) / iterations_survied
        if self.check_profession(individual) is "Attacker":
            offense_rating = (statistic.enemies_attacked + statistic.consumed_corpses) / iterations_survied
            score = poison_rating + predator_rating + offense_rating**offense_rating
        else:
            defense_rating = ( statistic.enemies_attacked * (not individual.dead) ) / iterations_survied
            score = iterations_survied + poison_rating + predator_rating + defense_rating**defense_rating

        # Don't allowe negative scores
        if (score < 0.5): score = 0.5
        return score
    
    def update_strategy(self, population):
        '''
        adopting the strategy depending on the current population.
        Some of the statistics measurement are taken to evaluate if the population should adjust to more
        aggressiveness or defensiveness.   
        '''
        if (self.intermediate_output):
            print("Current strategy\nThreshold: ", self.attacker_threshold, "\nAtackers: ", self.attacker_number)
        score = 0
        for individual in population:
            statistic = individual.statistic
            iterations_survied = int(statistic.time_survived / 300)
            aggresion = statistic.enemies_attacked - statistic.attacked_by_predators
            defense = iterations_survied + statistic.opponents_seen - statistic.attacked_by_opponents
            score += aggresion - defense
        if score > 0:
            if self.attacker_number < 8 : self.attacker_number += 1
        else:
            if self.attacker_number > 3 :self.attacker_number -= 1
        if (self.intermediate_output):
            print("New strategy\nThreshold: ", self.attacker_threshold, "\nAtackers: ", self.attacker_number)