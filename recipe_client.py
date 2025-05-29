from notion_api.notion_client import NotionClient
from notion_api.notion_client import H1Block, H2Block, ToDoBlock, DividerBlock, ParagraphBlock, \
    NumberedItemBlock, BulletItemBlock, BookmarkBlock

from recipe_scrapers import scrape_me
from recipe_scrapers import NoSchemaFoundInWildMode, WebsiteNotImplementedError

from requests import exceptions

from pint import UndefinedUnitError, DimensionalityError
# from ingredient_parser import parsers
# import ingredient_parser.parsers.parse_ingredient
from ingredient_parser.parsers import parse_ingredient
from pint import UnitRegistry

import csv

ureg = UnitRegistry()
Q_ = ureg.Quantity

from ingredient_processing import QUANTIZED_INGREDIENT_VOLUMES, INGREDIENT_DENSITY_CONVERSIONS

# from pluralizer import Pluralizer
# pluralizer = Pluralizer()
# from ingredient_parser import parse_ingredient

from recipe_obj import Recipe


NOTION_SECRETS_FILEPATH = "./notion_secret.csv"

def read_notion_secrets():
    secrets = {}
    try:
        with open(NOTION_SECRETS_FILEPATH, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                secrets[row['name']] = row['code']
    except FileNotFoundError:
        print(f"Error: The file {NOTION_SECRETS_FILEPATH} does not exist.")
    except Exception as e:
        print(f"An error occurred while reading the secrets: {e}")
    return secrets


class Ingredient:
    def __init__(self, ingredient_str):
        # take the recipe's ingredient text and semantically parse it for ingredient data
        parsed_ing = parse_ingredient(ingredient_str)

        # retrieve the name/text, quantity, and unit of the ingredient
        self.ingredient_text = parsed_ing.name.text
        self.ingredient_qty = float(parsed_ing.amount[0].quantity)
        self.ingredient_unit = parsed_ing.amount[0].unit

        # turn the ingredient amount/quantity into a UREG object
        self.processed_ingredient = self.process_ingredient()

    def process_ingredient(self):
        # use the unit to convert the ingredient quantity to a UREG volume
        try:
            conv_quantity_unit = self.ingredient_qty * ureg(self.ingredient_unit.lower())
        except UndefinedUnitError as e:
            # if the unit cannot be found / doesn't exist (e.g. "1 large egg")
            #   look up the name of the ingredient in the volumes dictionary
            conv_quantity_unit = self.ingredient_qty * QUANTIZED_INGREDIENT_VOLUMES.get(self.ingredient_text) * ureg('tbsp')

        return conv_quantity_unit

    def get_name(self):
        return self.ingredient_text

    def get_volume(self):
        return self.processed_ingredient

    def __repr__(self):
        return f"Ingredient: {self.ingredient_text} | Amount: {self.processed_ingredient}\n"


class RecipeClient:
    def __init__(self, client: NotionClient, recipe_database, ingredient_db):
        self.client = client
        self.database = recipe_database
        self.ingredient_database = ingredient_db
        self.ings_to_compare_against = self.get_db_ingredients()

    def get_db_ingredients(self, debug=False):
        # Get the list of possible ingredients from the ingredient DB
        ingredients = self.ingredient_database.get_pages()
        ings_to_compare_against = {}
        for ing in ingredients:
            ing_name = ing.get('properties').get('Name').get('title')[0].get('text').get('content').lower()
            ing_page_id = ing.get('id')
            ings_to_compare_against[ing_name] = ing_page_id

        if debug:
            print("DB INGS", ings_to_compare_against)

        return ings_to_compare_against

    def add_recipe(self, recipe_link):
        """
        Adds all the information about a recipe to a database entry
        :param recipe_link: a url to the recipe online from which the data is scraped
        :return:
        """

        recipe_obj = Recipe(recipe_link)
        for ing in recipe_obj.get_ingredients():
            self.is_ingredient_in_db(ing)

        yield 'data: Created recipe object.\n\n'

        yield 'data: TEST IMMEDIATE YIELD\n\n'

        # Check if the recipe URL has already been added to the database
        print("Querying database...")
        recipes = self.database.get_pages()
        urls = [recipe["properties"]["Recipe Link"]["url"] for recipe in recipes]
        if recipe_link in urls:
            print("Recipe already in database.")
            return

        print("Adding recipe...")

        print("\nScraping recipe...")
        # scrape the URL and turn the scraped data into a Recipe object
        recipe_obj = Recipe(recipe_link)

        yield 'data: Scraped recipe data successfully.\n\n'

        yield 'data: Test immediate yield.\n\n'

        # store the recipe's title for the database entry
        recipe_title = recipe_obj.get_title()
        print("Processing recipe:", recipe_title)

        recipe_img = recipe_obj.get_image()

        # dict for database variables (title and url)
        new_entry_data = {
            "Title": {"title": [{"text": {"content": recipe_title}}]},
            "Recipe Link": {"url": recipe_link}
        }

        print("Writing to database...")
        # write the new recipe entry to the database
        new_entry_res = self.database.add_entry(new_entry_data)
        print("Wrote to database with response:", new_entry_res)

        yield 'data: Added new entry to database.\n\n'

        print("Getting database entry ID...")
        new_entry_id = new_entry_res.json()["id"]
        print("ID is:", new_entry_id)

        print("Editing recipe page icon...")
        icon_res = self.database.edit_page_icon(new_entry_id, notion_icon_name='list_bullet', notion_icon_color='gray', debug=True)
        print("Edited icon with response", icon_res)

        print("Writing recipe page cover image...")
        img_res = self.database.edit_page_cover(new_entry_id, recipe_img)
        print("Wrote recipe cover image with response", img_res)

        print("Writing recipe information to entry...")
        edit_res = self.database.edit_entry_page(new_entry_id, self.write_recipe_json(recipe_obj))
        print("Wrote to entry with response:", edit_res)

        yield 'data: Recipe information written to entry.\n\n'

    def is_ingredient_in_db(self, ingredient_str):
        return True

        # # TODO
        # parsed_ing = parse_ingredient(ingredient_str)
        #
        # ingredient_text = parsed_ing.name.text.lower()
        # plural_ingredient_text = pluralizer.pluralize(ingredient_text)
        #
        # ingredient_page_id = None
        #
        # if ingredient_text in self.ings_to_compare_against.keys():
        #     ingredient_page_id = self.ings_to_compare_against.get(ingredient_text)
        #     print("INGREDIENT IN DATABASE", ingredient_text)
        # elif plural_ingredient_text in self.ings_to_compare_against.keys():
        #     ingredient_page_id = self.ings_to_compare_against.get(plural_ingredient_text)
        #     print("PLURAL INGREDIENT IN DATABASE", ingredient_text)
        # else:
        #     print("NOT IN DATABASE, \"", ingredient_text, "\"")
        #     for db_ing, db_ing_page_id in self.ings_to_compare_against.items():
        #         if db_ing in ingredient_text or ingredient_text in db_ing:
        #             print("\tFOUND AS SUBSTRING", ingredient_text, db_ing, db_ing_page_id)
        #             ingredient_page_id = db_ing_page_id
        #
        # if ingredient_page_id is None:
        #     print("COULD NOT LOCATE INGREDIENT. CONSIDER ADDING TO DATABASE.")

    @staticmethod
    def write_recipe_json(recipe_obj):
        """
        Build the chain of Notion JSON blocks representing
            the scraped data in the recipe format
        :return: a list of dicts representing the JSON blocks
            to be written to the Notion page
        """
        # Header content
        recipe_blocks = BookmarkBlock(recipe_obj.get_url())

        recipe_blocks.concat_block(H1Block("Info"))
        recipe_blocks.concat_block(ParagraphBlock(recipe_obj.get_description()))
        recipe_blocks.concat_block(DividerBlock())

        # Recipe meta information
        recipe_blocks.concat_block(BulletItemBlock(f'Yield: {recipe_obj.get_yield()}'))
        recipe_blocks.concat_block(BulletItemBlock(f'Prep Time: {recipe_obj.get_prep_time()}'))
        recipe_blocks.concat_block(BulletItemBlock(f'Cook Time: {recipe_obj.get_cook_time()}'))
        recipe_blocks.concat_block(BulletItemBlock(f'Total Time: {recipe_obj.get_total_time()}'))
        recipe_blocks.concat_block(BulletItemBlock(f'Rating: {recipe_obj.get_rating()}'))
        recipe_blocks.concat_block(BulletItemBlock(f'Author: {recipe_obj.get_author()}'))

        # Ingredient List
        recipe_blocks.concat_block(H1Block("Ingredients"))
        # ingredients can sometimes be organized into smaller
        #   groups; give a subheader to each one if relevant
        if len(recipe_obj.get_ingredient_groups()) > 1:
            for group in recipe_obj.get_ingredient_groups():
                group_title = group.purpose
                group_ingredients = group.ingredients

                if group_title is None:
                    recipe_blocks.concat_block(H2Block("Ingredient Group"))
                else:
                    recipe_blocks.concat_block(H2Block(group_title))

                for ingredient in group_ingredients:
                    recipe_blocks.concat_block(ToDoBlock(ingredient))
        # otherwise just make one big list of ingredients
        else:
            for ingredient in recipe_obj.get_ingredients():
                recipe_blocks.concat_block(ToDoBlock(ingredient))

        # Recipe instructions (steps)
        recipe_blocks.concat_block(H1Block("Directions"))
        for direction in recipe_obj.get_directions():
            recipe_blocks.concat_block(NumberedItemBlock(direction))

        # Nutrition Information
        if recipe_obj.get_nutrients() == {}:
            pass
        else:
            recipe_blocks.concat_block(H1Block("Nutrition"))
            for nutrient, value in recipe_obj.get_nutrients().items():
                recipe_blocks.concat_block(BulletItemBlock(f'{nutrient}: {value}'))

        return recipe_blocks.get_json_content()
