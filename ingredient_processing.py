from pluralizer import Pluralizer
import matplotlib.pyplot as plt
import numpy as np

# https://pypi.org/project/ingredient-parser-nlp/
from ingredient_parser.parsers import parse_ingredient
from ingredient_parser.parsers import parse_multiple_ingredients

from pint import UnitRegistry
ureg = UnitRegistry()
Q_ = ureg.Quantity
from pint import UndefinedUnitError, DimensionalityError

# from pull_recipe import Recipe
# from process_recipe_1M import read_in_1M

QUANTIZED_INGREDIENT_VOLUMES = {
    # ingredient (name): volume (tbsp)
    'egg': 3.0
}

INGREDIENT_DENSITY_CONVERSIONS = {
    # USE AQUA-CALC!
    # ingredient (name): {'density': #, 'units', 'x/y'}
    # e.g. 'cream cheese': {'density': 8.2, 'units', 'oz/cup'}
    'cream cheese': {'density': 8.2, 'units': 'oz/cup'}
}

# recipe = Recipe("https://sallysbakingaddiction.com/easy-cinnamon-rolls-from-scratch/")


def is_ingredient_present(ingredients_obj, ingredient_name):
    if ingredient_name is None:
        return True

    ingredient_texts = [ele.get('text').lower() for ele in ingredients_obj]
    if any([ingredient_name in txt for txt in ingredient_texts]):
        return True

    return False


def tally_ingredient(recipe_1M_objs, ingredient_name, condition=lambda x, y: True, other_ingredient=None, debug=False):
    tally = 0
    counter = 0

    for idx, recipe in recipe_1M_objs.items():
        ingredients_obj = recipe.get('ingredients')
        if is_ingredient_present(ingredients_obj, ingredient_name):
            if condition(ingredients_obj, other_ingredient):
                tally += 1
                if debug:
                    print(tally, recipe.get('title'))

        if debug:
            counter += 1
            if counter % 10000:
                print("Iterating recipe #", counter)

    return tally


def get_spices():
    spice_names = []
    with open('./herbs_and_spices.txt', 'r+') as f:
        for line in f:
            spice_names.append(line.strip().lower())

    return spice_names


def get_spices_tallies(recipe_objs):
    spices = get_spices()

    spice_tallies = {spice: 0 for spice in spices}

    for spice in spices:
        print("Tallying:", spice, end=' ')
        spice_tally = tally_ingredient(recipe_objs, spice)
        spice_tallies[spice] = spice_tally
        print(spice_tally)

    return spice_tallies


def get_spice_relations(recipe_objs, debug=False):
    spices = get_spices()

    relation_matrix = {spice_outer: {
        spice: 0 for spice in spices
    } for spice_outer in spices}

    for spice_outer in spices:
        print("Tallying associations with", spice_outer, "and")
        for spice in spices:
            if spice == spice_outer:
                continue
            conditional_outer_tally = tally_ingredient(recipe_objs, spice_outer, condition=is_ingredient_present, other_ingredient=spice)
            relation_matrix[spice_outer][spice] = conditional_outer_tally
            print("\t", spice, conditional_outer_tally)

    if debug:
        print(relation_matrix)

    return relation_matrix


def rank_relation_values(rel_matrix):
    all_vals = []

    for outer_spice, vals in rel_matrix.items():
        for inner_spice, tally in vals.items():
            print(outer_spice, inner_spice, tally)
            all_vals.append([tally, outer_spice, inner_spice])

    return sorted(all_vals, key=lambda x: x[0], reverse=True)


def plot_spice_relations(rel_matrix):
    # https://matplotlib.org/stable/gallery/mplot3d/3d_bars.html
    fig = plt.figure(figsize=(8, 6))
    ax1 = fig.add_subplot(projection='3d')

    spices = list(rel_matrix.keys())

    _x = np.arange(len(spices))
    _y = np.arange(len(spices))

    _xx, _yy = np.meshgrid(_x, _y)
    x, y = _xx.ravel(), _yy.ravel()

    bar_heights = []
    for x_val in range(len(spices)):
        for y_val in range(len(spices)):
            bar_heights.append(rel_matrix.get(spices[x_val]).get(spices[y_val]))

    # https://stackoverflow.com/questions/9433240/python-matplotlib-3d-bar-plot-adjusting-tick-label-position-transparent-b
    ticksx = np.arange(0.5, 33, 1)
    plt.xticks(ticksx, spices)

    ticksy = np.arange(0.5, 33, 1)
    plt.yticks(ticksy, spices)

    width = depth = 1

    ax1.bar3d(x, y, np.zeros_like(bar_heights), width, depth, bar_heights, shade=True)
    plt.show()


class IngredientRelationMatrix:
    def __init__(self, filepath):
        self.keys, self.matrix = self.create_matrix(filepath)
        self.matrix_normalized = self.normalize_matrix()

    def create_matrix(self, filepath):
        with open(filepath, 'r+') as f:
            data = []
            for row in f:
                eles = [ele.strip() for ele in row.split(",")]
                data.append(eles)

            headers = data[0]
            values = data[1:]

            rel_matrix = {spice: None for spice in headers}

            for spice_idx, spice in enumerate(headers):
                dict_to_add = dict()
                for idx, value in enumerate(values[spice_idx]):
                    dict_to_add[headers[idx]] = int(value)

                rel_matrix[spice] = dict_to_add

        return headers, rel_matrix

    def normalize_matrix(self):
        new_matrix = {key: values.copy() for key, values in self.get_matrix().copy().items()}
        for ingredient_key, ingredient_values in new_matrix.items():
            normalize_factor = self.count_ingredient(ingredient_key)
            for inner_ing in ingredient_values:
                new_matrix[ingredient_key][inner_ing] /= normalize_factor

        return new_matrix

    def get_normalized_matrix(self):
        return self.matrix_normalized

    def get_matrix(self):
        return self.matrix

    def get_keys(self):
        return self.keys

    def count_ingredient(self, ingredient):
        return self.get_matrix().get(ingredient).get(ingredient)

    def plot(self, normalized=True):
        # https://matplotlib.org/stable/gallery/mplot3d/3d_bars.html
        fig = plt.figure(figsize=(8, 6))
        ax1 = fig.add_subplot(projection='3d')

        if normalized:
            rel_matrix = self.get_normalized_matrix()
        else:
            rel_matrix = self.get_matrix()

        ingredient_keys = list(rel_matrix.keys())

        _x = np.arange(len(ingredient_keys))
        _y = np.arange(len(ingredient_keys))

        _xx, _yy = np.meshgrid(_x, _y)
        x, y = _xx.ravel(), _yy.ravel()

        bar_heights = []
        for x_val in range(len(ingredient_keys)):
            for y_val in range(len(ingredient_keys)):
                bar_heights.append(rel_matrix.get(ingredient_keys[x_val]).get(ingredient_keys[y_val]))

        # https://stackoverflow.com/questions/9433240/python-matplotlib-3d-bar-plot-adjusting-tick-label-position-transparent-b
        ticksx = np.arange(0.5, len(ingredient_keys), 1)
        plt.xticks(ticksx, ingredient_keys)

        ticksy = np.arange(0.5, len(ingredient_keys), 1)
        plt.yticks(ticksy, ingredient_keys)

        width = depth = 1

        ax1.bar3d(x, y, np.zeros_like(bar_heights), width, depth, bar_heights, shade=True)
        plt.show()


if __name__ == "__main__":
    print("Hello world!")

    recipe_obj = Recipe("https://cafedelites.com/best-fluffy-pancakes/#recipe")
    parse_amounts(recipe_obj)


#     # recipe_1M_recipes = read_in_1M()
#     # plot_spice_relations(relation_matrix)
#     # out = rank_relation_values(relation_matrix)
#     # print(out)
#     spice_relations = IngredientRelationMatrix('./spices_relation_matrix.csv')
#     print(spice_relations.get_matrix())
#     print(spice_relations.count_ingredient('tarragon'))
#     normalized = spice_relations.get_normalized_matrix()
#     print(normalized)
#     spice_relations.plot()
