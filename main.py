import pygame
import random
import math
import sys
import matplotlib.pyplot as plt
from enum import Enum

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
FPS = 60
SIMULATION_DURATION = 10  # seconds
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 128, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

# Animal traits
class Diet(Enum):
    HERBIVORE = 1
    CARNIVORE = 2
    OMNIVORE = 3

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Survival of the Fittest Simulation")
clock = pygame.time.Clock()

# Font setup
font = pygame.font.SysFont('Arial', 14)

class Animal:
    def __init__(self, x, y, dna=None):
        self.x = x
        self.y = y
        self.age = 0
        self.energy = 100
        self.alive = True
        self.reproduction_cooldown = 0
        
        # DNA determines traits
        if dna:
            self.dna = dna
        else:
            self.dna = {
                'speed': random.uniform(0.5, 3.0),
                'size': random.uniform(0.5, 2.0),
                'sense': random.uniform(1.0, 5.0),
                'diet': random.choice(list(Diet)),
                'color': (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
            }
        
        # Movement
        self.direction = random.uniform(0, 2 * math.pi)
        self.change_direction_counter = 0
        
    def move(self, plants, animals):
        # Random direction changes
        if self.change_direction_counter <= 0:
            self.direction += random.uniform(-0.5, 0.5)
            self.change_direction_counter = random.randint(10, 30)
        else:
            self.change_direction_counter -= 1
        
        # Move based on diet
        if self.dna['diet'] == Diet.HERBIVORE:
            self.move_toward_food(plants)
        elif self.dna['diet'] == Diet.CARNIVORE:
            self.move_toward_food([a for a in animals if a != self and a.dna['size'] < self.dna['size'] * 1.2])
        else:  # OMNIVORE
            all_food = plants + [a for a in animals if a != self and a.dna['size'] < self.dna['size'] * 1.2]
            self.move_toward_food(all_food)
        
        # Calculate movement
        dx = math.cos(self.direction) * self.dna['speed']
        dy = math.sin(self.direction) * self.dna['speed']
        
        # Update position with boundary checks
        self.x = max(0, min(WIDTH, self.x + dx))
        self.y = max(0, min(HEIGHT, self.y + dy))
        
        # Energy cost
        self.energy -= 0.05 * self.dna['speed'] * self.dna['size']
    
    def move_toward_food(self, food_items):
        if not food_items:
            return
            
        # Find closest food
        closest = None
        min_dist = float('inf')
        
        for food in food_items:
            dist = math.sqrt((self.x - food.x)**2 + (self.y - food.y)**2)
            if dist < min_dist and dist < self.dna['sense'] * 20:
                min_dist = dist
                closest = food
        
        if closest:
            # Move toward food
            target_dir = math.atan2(closest.y - self.y, closest.x - self.x)
            angle_diff = (target_dir - self.direction + math.pi) % (2 * math.pi) - math.pi
            self.direction += angle_diff * 0.1
    
    def eat(self, plants, animals):
        if self.dna['diet'] == Diet.HERBIVORE:
            for plant in plants[:]:
                dist = math.sqrt((self.x - plant.x)**2 + (self.y - plant.y)**2)
                if dist < 10 + self.dna['size'] * 5:
                    self.energy += 30
                    plants.remove(plant)
                    break
        elif self.dna['diet'] == Diet.CARNIVORE:
            for animal in animals[:]:
                if animal != self and animal.dna['size'] < self.dna['size'] * 1.2:
                    dist = math.sqrt((self.x - animal.x)**2 + (self.y - animal.y)**2)
                    if dist < 10 + self.dna['size'] * 5:
                        self.energy += animal.energy * 0.7
                        animal.alive = False
                        break
        else:  # OMNIVORE
            ate = False
            for plant in plants[:]:
                dist = math.sqrt((self.x - plant.x)**2 + (self.y - plant.y)**2)
                if dist < 10 + self.dna['size'] * 5:
                    self.energy += 20
                    plants.remove(plant)
                    ate = True
                    break
            
            if not ate:
                for animal in animals[:]:
                    if animal != self and animal.dna['size'] < self.dna['size'] * 1.2:
                        dist = math.sqrt((self.x - animal.x)**2 + (self.y - animal.y)**2)
                        if dist < 10 + self.dna['size'] * 5:
                            self.energy += animal.energy * 0.5
                            animal.alive = False
                            ate = True
                            break
    
    def reproduce(self):
        if self.energy > 150 and self.reproduction_cooldown <= 0:
            self.energy /= 2
            self.reproduction_cooldown = 100
            
            # Create offspring with slightly mutated DNA
            mutated_dna = {
                'speed': max(0.1, self.dna['speed'] + random.uniform(-0.2, 0.2)),
                'size': max(0.1, self.dna['size'] + random.uniform(-0.2, 0.2)),
                'sense': max(0.5, self.dna['sense'] + random.uniform(-0.3, 0.3)),
                'diet': self.dna['diet'] if random.random() > 0.05 else random.choice(list(Diet)),
                'color': (
                    max(0, min(255, self.dna['color'][0] + random.randint(-20, 20))),
                    max(0, min(255, self.dna['color'][1] + random.randint(-20, 20))),
                    max(0, min(255, self.dna['color'][2] + random.randint(-20, 20)))
                )
            }
            
            return Animal(
                self.x + random.uniform(-20, 20),
                self.y + random.uniform(-20, 20),
                mutated_dna
            )
        return None
    
    def update(self, plants, animals):
        if not self.alive:
            return None
        
        self.age += 1
        self.energy -= 0.1 * self.dna['size']
        
        if self.reproduction_cooldown > 0:
            self.reproduction_cooldown -= 1
        
        # Die if no energy or too old
        if self.energy <= 0 or self.age > 1000:
            self.alive = False
            return None
        
        self.move(plants, animals)
        self.eat(plants, animals)
        
        return self.reproduce()
    
    def draw(self, screen):
        if not self.alive:
            return
            
        size = 5 + self.dna['size'] * 5
        pygame.draw.circle(screen, self.dna['color'], (int(self.x), int(self.y)), int(size))
        
        # Draw a small indicator for diet
        if self.dna['diet'] == Diet.HERBIVORE:
            pygame.draw.circle(screen, GREEN, (int(self.x), int(self.y)), 3)
        elif self.dna['diet'] == Diet.CARNIVORE:
            pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), 3)
        else:  # OMNIVORE
            pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), 3)

class Plant:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.energy = random.uniform(20, 50)
        self.growth_rate = random.uniform(0.5, 2.0)
        self.size = random.uniform(0.5, 2.0)
        self.color = (random.randint(0, 50), random.randint(100, 200), random.randint(0, 50))
    
    def update(self):
        self.energy += self.growth_rate
        if self.energy > 100:
            self.energy = 50
            return Plant(
                self.x + random.uniform(-30, 30),
                self.y + random.uniform(-30, 30)
            )
        return None
    
    def draw(self, screen):
        size = 3 + self.size * 3
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(size))

def draw_stats(screen, animals, plants, generation, elapsed_time, fps):
    # Background panel (larger on Y axis)
    pygame.draw.rect(screen, (200, 200, 200, 150), (10, 10, 250, 140))
    
    # Display stats
    stats = [
        f"Generation: {generation}",
        f"Time: {elapsed_time:.1f}/{SIMULATION_DURATION}s",
        f"FPS: {fps:.1f}",
        f"Animals: {len(animals)}",
        f"Plants: {len(plants)}",
        "",
        "Average Traits:",
        f"Speed: {sum(a.dna['speed'] for a in animals)/len(animals):.2f}" if animals else "N/A",
        f"Size: {sum(a.dna['size'] for a in animals)/len(animals):.2f}" if animals else "N/A",
        f"Sense: {sum(a.dna['sense'] for a in animals)/len(animals):.2f}" if animals else "N/A"
    ]
    
    for i, stat in enumerate(stats):
        text = font.render(stat, True, BLACK)
        screen.blit(text, (20, 20 + i * 18))

def show_final_population_graph(animal_history, plant_history):
    plt.figure(figsize=(10, 6))
    
    # Plot animal populations by type
    herbivores = [sum(1 for a in animals if a.dna['diet'] == Diet.HERBIVORE) for animals in animal_history]
    carnivores = [sum(1 for a in animals if a.dna['diet'] == Diet.CARNIVORE) for animals in animal_history]
    omnivores = [sum(1 for a in animals if a.dna['diet'] == Diet.OMNIVORE) for animals in animal_history]
    
    time_points = [i/FPS for i in range(len(animal_history))]
    
    plt.plot(time_points, herbivores, 'g-', label='Herbivores')
    plt.plot(time_points, carnivores, 'r-', label='Carnivores')
    plt.plot(time_points, omnivores, 'y-', label='Omnivores')
    plt.plot(time_points, plant_history, 'b-', label='Plants')
    
    plt.xlabel('Time (seconds)')
    plt.ylabel('Population')
    plt.title('Population Over Time')
    plt.legend()
    plt.grid(True)
    plt.show()

def main():
    # Simulation parameters
    animals = [Animal(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(20)]
    plants = [Plant(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(50)]
    
    generation = 1
    running = True
    paused = False
    start_time = pygame.time.get_ticks()
    
    # For tracking population history
    animal_history = []
    plant_history = []
    
    while running:
        current_time = (pygame.time.get_ticks() - start_time) / 1000
        if current_time >= SIMULATION_DURATION:
            running = False
            break
            
        fps = clock.get_fps()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    # Reset simulation
                    animals = [Animal(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(20)]
                    plants = [Plant(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(50)]
                    generation = 1
                    start_time = pygame.time.get_ticks()
                    animal_history = []
                    plant_history = []
        
        if paused:
            # Draw everything but don't update
            screen.fill((230, 255, 230))  # Forest background
            for plant in plants:
                plant.draw(screen)
            for animal in animals:
                animal.draw(screen)
            draw_stats(screen, animals, plants, generation, current_time, fps)
            pygame.display.flip()
            clock.tick(FPS)
            continue
        
        # Record current populations
        animal_history.append(animals.copy())
        plant_history.append(len(plants))
        
        # Update plants
        new_plants = []
        for plant in plants:
            new_plant = plant.update()
            if new_plant:
                new_plants.append(new_plant)
        plants.extend(new_plants)
        
        # Add new plants occasionally
        if random.random() < 0.02:
            plants.append(Plant(random.randint(0, WIDTH), random.randint(0, HEIGHT)))
        
        # Update animals
        new_animals = []
        dead_animals = []
        
        for animal in animals[:]:
            offspring = animal.update(plants, animals)
            if offspring:
                new_animals.append(offspring)
            if not animal.alive:
                dead_animals.append(animal)
        
        # Remove dead animals
        for animal in dead_animals:
            if animal in animals:
                animals.remove(animal)
        
        animals.extend(new_animals)
        
        # If population gets too low, start a new generation
        if len(animals) < 5 and len(animals) > 0:
            generation += 1
            surviving_dna = [a.dna for a in animals]
            animals.clear()
            for _ in range(20):
                parent_dna = random.choice(surviving_dna)
                animals.append(Animal(
                    random.randint(0, WIDTH),
                    random.randint(0, HEIGHT),
                    parent_dna
                ))
        
        # Draw everything
        screen.fill((230, 255, 230))  # Forest background
        
        for plant in plants:
            plant.draw(screen)
        for animal in animals:
            animal.draw(screen)
        
        draw_stats(screen, animals, plants, generation, current_time, fps)
        
        # Display controls
        controls = [
            "Controls:",
            "Space - Pause/Resume",
            "R - Reset Simulation"
        ]
        
        for i, control in enumerate(controls):
            text = font.render(control, True, BLACK)
            screen.blit(text, (WIDTH - 200, 20 + i * 18))
        
        pygame.display.flip()
        clock.tick(FPS)
    
    # Show population graph when simulation ends
    show_final_population_graph(animal_history, plant_history)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()