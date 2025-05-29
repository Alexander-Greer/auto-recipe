from recipe_scrapers import scrape_me
from recipe_scrapers import NoSchemaFoundInWildMode, WebsiteNotImplementedError

from requests import exceptions

# from ingredient_parser.parsers import parse_ingredient
# from pluralizer import Pluralizer
# pluralizer = Pluralizer()

# import numpy as np
# from scipy import spatial
# import gensim.downloader as api

# print("Loading Gensim model...")
# MODEL = api.load("glove-wiki-gigaword-50") #choose from multiple models https://github.com/RaRe-Technologies/gensim-data


class Recipe:
    def __init__(self, inp, inp_type="url"):
        if inp_type == "url":
            self.url = inp
            self.scraped = self.scrape_recipe(self.url)
            self.recipe_1M_obj = None
        elif inp_type == "1M":
            self.recipe_1M_obj = inp
            self.scraped = None

        self.inp_type = inp_type

        if self.scraped is not None:
            try:
                self.host = self.scraped.host()
            except:
                self.host = "N/A"
            try:
                self.title = self.scraped.title()
            except:
                self.title = "Recipe"
            try:
                self.image = self.scraped.image()
            except:
                self.image = ''
            try:
                self.total_time = self.scraped.total_time()
            except:
                self.total_time = "N/A"
            try:
                self.yields = self.scraped.yields()
            except:
                self.yields = "N/A"
            try:
                self.ingredients = self.scraped.ingredients()
            except:
                self.ingredients = []
            try:
                self.ingredient_groups = self.scraped.ingredient_groups()
            except:
                self.ingredient_groups = []
            try:
                self.directions = self.scraped.instructions()
            except:
                self.directions = "N/A"
            try:
                self.nutrients = self.scraped.nutrients()
            except:
                self.nutrients = {}
            try:
                self.ratings = self.scraped.ratings()
            except:
                self.ratings = "N/A"
            try:
                self.author = self.scraped.author()
            except:
                self.author = "N/A"
            try:
                self.prep_time = self.scraped.prep_time()
            except:
                self.prep_time = "N/A"
            try:
                self.cook_time = self.scraped.cook_time()
            except:
                self.cook_time = "N/A"
            try:
                self.description = self.scraped.description()
            except:
                self.description = "N/A"
        elif self.recipe_1M_obj is not None:
            self.url = self.recipe_1M_obj.get('url')
            self.title = self.recipe_1M_obj.get('title')
            self.recipe_1M_ID = self.recipe_1M_obj.get('id')
            self.ingredients = self.parse_1M_ingredients()
            self.directions = self.parse_1M_directions()
            self.host = "N/A"
            self.total_time = "N/A"
            self.yields = "N/A"
            self.ingredient_groups = []
            self.nutrients = {}
            self.ratings = "N/A"
            self.author = "N/A"
            self.prep_time = "N/A"
            self.cook_time = "N/A"
            self.description = "N/A"
            self.image = ''
        else:
            self.host = "N/A"
            self.title = "Recipe"
            self.total_time = "N/A"
            self.yields = "N/A"
            self.ingredients = []
            self.ingredient_groups = []
            self.directions = "N/A"
            self.nutrients = {}
            self.ratings = "N/A"
            self.author = "N/A"
            self.prep_time = "N/A"
            self.cook_time = "N/A"
            self.description = "N/A"
            self.image = ''

    def parse_1M_ingredients(self):
        ingredients_obj = self.recipe_1M_obj.get('ingredients')
        ingredients_out = []

        for ingredient_obj in ingredients_obj:
            ingredient_txt = ingredient_obj.get('text')
            ingredients_out.append(ingredient_txt)

        return ingredients_out

    def parse_1M_directions(self):
        directions_obj = self.recipe_1M_obj.get('instructions')
        directions_out = []

        for direction_obj in directions_obj:
            direction_txt = direction_obj.get('text')
            directions_out.append(direction_txt)

        return directions_out

    # def process_ingredients(self):
    #     return [Ingredient(ing) for ing in self.get_ingredients()]

    # def get_volume(self, debug=False):
    #     vol_sum = 0

    #     for ingredient in self.process_ingredients():
    #         try:
    #             if debug:
    #                 print(ingredient.get_volume())
    #             vol_sum += ingredient.get_volume()
    #         except DimensionalityError as e:
    #             if debug:
    #                 print("Error on converting", ingredient, e)
    #             cc_vals = INGREDIENT_DENSITY_CONVERSIONS.get('cream cheese')
    #             density_converted_unit = ingredient.ingredient_qty * ureg(ingredient.ingredient_unit.lower()) / (
    #                         cc_vals.get('density') * ureg(cc_vals.get('units')))
    #             vol_sum += density_converted_unit

    #     return vol_sum

    # def ingredient_breakdown(self, unit='volume', debug=False):
    #     processed_ingredients = self.process_ingredients()
    #     total_vol = self.get_volume(debug)
    #     if debug:
    #         print("Total volume:", total_vol)
    #     if unit == 'volume':
    #         volumes_vector = dict()
    #         for ingredient in processed_ingredients:
    #             percent_vol = ingredient.get_volume().to(ureg("cup")) / total_vol
    #             volumes_vector[ingredient.get_name()] = percent_vol.magnitude
    #         return volumes_vector

    @staticmethod
    def scrape_recipe(recipe_url, wild_mode=True):
        try:
            scraper = scrape_me(recipe_url, wild_mode=wild_mode)
            return scraper
        except (NoSchemaFoundInWildMode, exceptions.MissingSchema, WebsiteNotImplementedError) as e:
            print(e)
            return None
        except Exception as e:
            print(e)
            return None

    def get_title(self):
        return self.title

    def get_image(self):
        return self.image

    def get_author(self):
        return self.author

    def get_ingredients(self):
        return self.ingredients

    def get_ingredient_groups(self):
        return self.ingredient_groups

    def get_directions(self):
        if self.inp_type != "1M":
            return [ele for ele in self.directions.split('\n')]
        else:
            return self.directions

    def get_prep_time(self):
        return f'{self.prep_time}{" mins" if self.prep_time != "N/A" else ""}'

    def get_cook_time(self):
        return f'{self.cook_time}{" mins" if self.cook_time != "N/A" else ""}'

    def get_total_time(self):
        return f'{self.total_time}{" mins" if self.total_time != "N/A" else ""}'

    def get_rating(self):
        return self.ratings

    def get_yield(self):
        return self.yields

    def get_url(self):
        return self.url

    def get_description(self):
        return self.description

    def get_nutrients(self):
        formatted = {}
        # the scraper returns the names of nutrients with keys like
        #   "carboyhdrateContent": ...
        #   remove the "Content" bit and capitalize what's left
        for nutrient, val in self.nutrients.items():
            nut_name = nutrient.replace("Content", "").capitalize()
            formatted[nut_name] = val
        return formatted

    def __repr__(self):
        joined_ingredient_string = "\n\t\t• ".join([ingredient for ingredient in self.get_ingredients()])
        return f'{self.get_title()}:' \
               f'\n\tDescription: {self.get_description()}' \
               f'\n\tIngredients:\n\t\t• {joined_ingredient_string}'

    @staticmethod
    def get_semantic_similarity(str1, str2, debug=False):
        # https://medium.com/@yachna398/natural-language-processing-for-fuzzy-string-matching-with-python-c66d52fab0e0
        # https://stackoverflow.com/questions/65852710/text-similarity-using-word2vec

        def preprocess(s):
            return [i.lower() for i in s.split()]

        def get_vector(s):
            try:
                return np.sum(np.array([MODEL[i] for i in preprocess(s)]), axis=0)
            except Exception as e:
                if debug:
                    print("ERR", e)
        
        try:
            return 1 - spatial.distance.cosine(get_vector(str1), get_vector(str2))
        except ValueError as e:
            if debug:
                print("Err", e)
            return 0

    def measure_ingredients(self):
        for ingredient in self.get_ingredients():
            print("Measuring", ingredient, "...")

            parsed_ingr = parse_ingredient(ingredient)
            print("P", parsed_ingr)
            if parsed_ingr.amount:
                try:
                    ingredient_vol = parsed_ingr.amount[0].convert_to("cups")
                    print(parsed_ingr.name[0].text, ingredient_vol)
                except TypeError as e:
                    print("non volumetric qty", e)
            else:
                print("no vol")


    def match_ingredients(self, ingredient_db_dict, debug=False):
        output_matching = {}
        for ingredient in self.get_ingredients():
            print("Matching", ingredient, "...")

            parsed_ingr = parse_ingredient(ingredient)
            # print("INGR", parsed_ingr)
            ingr_name = parsed_ingr.name[0].text.lower()  # pull out the name of the ingredient from the returned object from the parsing operation

            # STEP 1:
            # check if the ingredient name listed is already in the database outright (in singular or plural form)
            if pluralizer.isSingular(ingr_name):
                ingredient_names_to_check = [ingr_name, pluralizer.plural(ingr_name)]
            else:
                ingredient_names_to_check = [pluralizer.singular(ingr_name), ingr_name]

            ingredient_names_to_check = [name.replace(" ", "_") for name in ingredient_names_to_check]

            found_match = False
            for name in ingredient_names_to_check:
                if name in ingredient_db_dict.keys():
                    print("FOUND MATCH:", name)
                    output_matching[name] = ingredient_db_dict.get(name)
                    found_match = True
                    break

            # don't continue to the rest of the search steps if we explicitly found the ingredient already
            if found_match:
                continue

            # STEP 2:
            # pick ingredient with highest semantic similarity above a cutoff threshold
            candidates = []

            for db_ingr in ingredient_db_dict.keys():
                natural_language_ing = db_ingr.replace("_", " ").lower()
                similarity = self.get_semantic_similarity(ingr_name, natural_language_ing)
                # print("SIM", ingredient, natural_language_ing, similarity)
                if similarity > 0.85:
                    candidates.append((ingredient_db_dict.get(natural_language_ing), similarity))

            # if not present, notify to add ingredient to list
            if not candidates:
                print("INGREDIENT", ingr_name, "COULD NOT BE FOUND!")
                continue
            
            if len(candidates) == 1:
                print("CAND1", candidates)
                # return candidates[0][0]
                # output_matching[]
                
            if debug:
                print("CAND", candidates)
            closest_match = sorted(candidates, key=lambda x: x[1])[-1]
            # return closest_match[0]
            print("CLSMTCH", closest_match)
        
        return output_matching