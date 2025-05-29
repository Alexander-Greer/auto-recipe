import json
import sys
from pluralizer import Pluralizer
import re
import math

import random

from pull_recipe import NOTION_TOKEN, DATABASE_ID, INGREDIENT_DB_ID
from recipe_client import RecipeClient, Recipe
from notion_client import NotionClient


def get_only_numbers(inp_text):
    return re.findall(r'\d+', inp_text)


def progress_bar(amount_complete, total, num_divisions=10):
    percent_complete = amount_complete / total
    filled_boxes = math.floor(percent_complete * num_divisions)

    out_str = "◼" * (filled_boxes+1)
    out_str += "◻" * (num_divisions-(filled_boxes+1))
    out_str += f" {math.ceil(100*percent_complete)}%"

    return out_str


pluralizer = Pluralizer()


def matching_title(target, title):
    target_words = [word.strip() for word in target.split(' ')]

    lower_title = title.lower()

    token_pairs = []

    for word in target_words:
        if pluralizer.isPlural(word):
            word_pair = [pluralizer.singular(word), word]
            token_pairs.append(word_pair)
        else:
            word_pair = [word, pluralizer.plural(word)]
            token_pairs.append(word_pair)

    for pair in token_pairs:
        sing, plur = [ele.lower() for ele in pair]
        if (sing in lower_title) or (plur in lower_title):
            continue
        else:
            return False

    return True


def scrape_recipe1M(query):
    print('Opening Recipe1M file...')
    f = open('./recipe1M_layers/layer1.json')

    print('Loading Recipe1M JSON...')
    data = json.load(f)

    for recipe in data:
        print("RECIPE IS", recipe)
        break

    # counter = 0
    #
    # found = []
    #
    # print('Iterating through recipes...')
    # for recipe in data:
    #     if counter % 1000 == 0:
    #         print('Checking recipe', counter, '...')
    #     if matching_title(query, recipe['title']):
    #         found.append(recipe)
    #
    #     counter += 1
    #
    # return found


class Recipe1MDatabase:
    def __init__(self, filepath):
        self.indexed_recipes = self.read_in_1M(filepath)
        self.num_recipes = len(self.indexed_recipes)

    def read_in_1M(self, filepath):
        print('Opening Recipe1M file...')
        f = open(filepath)

        print('Loading Recipe1M JSON...')
        data = json.load(f)

        keyed_recipes = {}

        print('Iterating through recipes: ', end='')
        for idx, recipe in enumerate(data):
            if idx % 50000 == 0:
                print('▊', end='')
            keyed_recipes[idx] = recipe

        print()
        print(f'Loaded {len(data)} Recipes')
        return keyed_recipes

    def get_recipes(self):
        return self.indexed_recipes.values()

    def run_cli(self):
        while True:
            inp = input("Enter command:"
                        "\n\tr - Random recipe(s)"
                        "\n\tf - Find recipes from keyword(s)"
                        "\n\tq - Quit program"
                        "\n\t> ")
            if inp == 'q':
                exit()
            elif inp == 'r':
                output_recipes = []
                num_recipes_txt = input('Enter Number of Recipes\n\t> ')
                try:
                    num_recipes = int(num_recipes_txt)

                    for idx in range(num_recipes):
                        random_recipe = random.choice(list(self.indexed_recipes.values()))
                        random_recipe_obj = Recipe(random_recipe, inp_type='1M')
                        output_recipes.append([random_recipe_obj.get_title(), random_recipe_obj.get_url()])
                        print(idx + 1, '-', output_recipes[idx])

                except Exception as e:
                    print("Could not interpret input", e)

                while True:
                    post_generated_inp = input("How to proceed:"
                                               "\n\tx - Exit to main loop"
                                               "\n\te - Edit generated selection"
                                               "\n\tr - Regenerate entire list"
                                               "\n\tw - Write to notion database"
                                               "\n\tq - Quit program"
                                               "\n\t> ")

                    if post_generated_inp == 'q':
                        exit()
                    elif post_generated_inp == 'c':
                        output_recipes = []
                        break
                    elif post_generated_inp == 'e':
                        edit_select = input(
                            f"Enter recipe number(s) to re-generate ({[i + 1 for i in range(len(output_recipes))]})"
                            f"\n\t> ")

                        parsed_numbers = [ele.strip() for ele in edit_select.split(',')]
                        parsed_idxs = [int(num) - 1 for num in parsed_numbers]
                        print(parsed_idxs)

                        regenerated_output_recipes = []

                        for idx, recipe in enumerate(output_recipes):
                            if idx in parsed_idxs:
                                new_recipe = random.choice(list(self.indexed_recipes.values()))
                                new_recipe_obj = Recipe(new_recipe, inp_type='1M')
                                print("NEW RECIPE", new_recipe_obj)
                                regenerated_output_recipes.append(
                                    [new_recipe_obj.get_title(), new_recipe_obj.get_url()])
                            else:
                                regenerated_output_recipes.append(recipe)

                        for idx in range(len(regenerated_output_recipes)):
                            print(idx + 1, '-', regenerated_output_recipes[idx])

                        output_recipes = regenerated_output_recipes

                    elif post_generated_inp == 'w':
                        print("Writing", len(output_recipes), "recipes to Notion database...")

                        token = NOTION_TOKEN
                        client = NotionClient(token)

                        recipe_db = DATABASE_ID
                        database_obj = client.connect_database(recipe_db)

                        ingredient_db_id = INGREDIENT_DB_ID
                        ingredient_db_obj = client.connect_database(ingredient_db_id)

                        recipe_client = RecipeClient(client, database_obj, ingredient_db_obj)

                        for recipe in output_recipes:
                            name, url = recipe
                            print(f"Adding recipe: '{name}'")
                            recipe_client.add_recipe(url)
            elif inp == 'f':
                filter_method = input("Enter keyword filtering method:"
                                      "\n\tt - keyword in title"
                                      "\n\ti - keyword in ingredients"
                                      "\n\ta - any"
                                      "\n\t> ")

                if filter_method == 't':
                    title_keyword = input("Enter title keyword:"
                                          "\n\t> ")
                    found_recipes = self.search_recipe_titles(title_keyword)
                    print(f"Found {len(found_recipes)} recipes whose title includes keyword '{title_keyword}'")

                elif filter_method == 'i':
                    ingredient_keyword = input("Enter ingredient:"
                                               "\n\t> ")

                    found_recipes = self.search_recipes_by_ingredient(ingredient_keyword)
                    print(f"Found {len(found_recipes)} recipes using ingredient '{ingredient_keyword}'")

                else:
                    print("Could not parse input")
                    continue

                next_inp = input("\n\tl - list recipes"
                                 "\n\tx - exit to main loop"
                                 "\n\tr - pick recipe at random"
                                 "\n\t> ")

                if next_inp == 'l':
                    for idx, recipe in enumerate(found_recipes):
                        recipe_obj = Recipe(recipe, inp_type='1M')
                        print(idx, '-', recipe_obj.get_title(), recipe_obj.get_url())

                elif next_inp == 'r':
                    rand_recipe = random.choice(found_recipes)
                    rand_recipe_obj = Recipe(rand_recipe, inp_type='1M')
                    print(rand_recipe_obj.get_title(), rand_recipe_obj.get_url())

    def search_recipe_titles(self, title_keyword):
        print('Filtering recipes...')
        counter = 0

        found_recipes = []
        for recipe in self.get_recipes():
            if matching_title(title_keyword, recipe['title']):
                found_recipes.append(recipe)

            if counter % 50000 == 0:
                print(progress_bar(counter, self.num_recipes, num_divisions=20))

            counter += 1

        return found_recipes

    def search_recipes_by_ingredient(self, ingredient_keyword):
        print('Filtering recipes...')
        counter = 0

        found_recipes = []
        for recipe in self.get_recipes():
            ingredients = Recipe(recipe, inp_type='1M').get_ingredients()
            if any([matching_title(ingredient_keyword, ingredient) for ingredient in ingredients]):
                found_recipes.append(recipe)

            if counter % 50000 == 0:
                print(progress_bar(counter, self.num_recipes, num_divisions=20))

            counter += 1

        return found_recipes


if __name__ == '__main__':
    recipes = Recipe1MDatabase('./recipe1M_layers/layer1.json')
    recipes.run_cli()
