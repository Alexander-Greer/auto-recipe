from notion_client import NotionClient
from recipe_client import RecipeClient, Recipe

# ########################
# Notion API Request Stuff
# ########################

# Internal integration "secret" from Integrations page
NOTION_TOKEN = "secret_4YDFvqvgQF894Hgu8IrfxeLLZj7FylLkZXHOf3KJdwr"

# https://stackoverflow.com/questions/67728038/where-to-find-database-id-for-my-database-in-notion
# If your URL looks like `https://www.notion.so/<long_hash_1>?v=<long_hash_2>`,
# then <long_hash_1> is the database ID and <long_hash_2> is the view ID.
# https://www.notion.so/c58462890203448f9dcf50bea7c11580?v=60df777268d54d29a189ad96b2bbcbd1&pvs=4
DATABASE_ID = "c58462890203448f9dcf50bea7c11580"

# https://www.notion.so/cd2598ec2530433ab675f079e9e3cb3d?v=a3e863c46ee540d1bdf4af746092910f&pvs=4
INGREDIENT_DB_ID = "cd2598ec2530433ab675f079e9e3cb3d"


# #########################
# Recipe Command Line Tools
# #########################

def run_cli():
    token = NOTION_TOKEN
    client = NotionClient(token)

    recipe_db = DATABASE_ID
    database_obj = client.connect_database(recipe_db)

    ingredient_db_id = INGREDIENT_DB_ID
    ingredient_db_obj = client.connect_database(ingredient_db_id)

    recipe_client = RecipeClient(client, database_obj, ingredient_db_obj)

    links_to_add = []

    command = input("Enter Command"
                    "\n\t[a - add recipe from link]"
                    "\n\t[b - add batch of recipes from links]"
                    "\n\t[p - process list of recipe links from file]"
                    "\n\t[s - scrape recipe from link]"
                    "\n\t[i - process recipe ingredients from link]"
                    "\n\t[q - quit program]"
                    "\n> ")

    if command == "a":
        # add the recipe linked at the url to the database
        recipe_link = input("Input recipe link > ")
        recipe_client.add_recipe(recipe_link)

    elif command == "p":
        # adds all the recipes linked in the `links_to_add` list to the database
        if not links_to_add:
            print("No links to process!")
        for recipe_link in links_to_add:
            recipe_client.add_recipe(recipe_link)
            # add_recipe(recipe_link)

    elif command == "s":
        # scrape the linked recipe and output its details
        recipe_link = input("Input recipe link > ")
        recipe = Recipe(recipe_link)
        print(recipe)

    elif command == 'i':
        # scrape the linked recipe and output its details
        recipe_link = input("Input recipe link > ")
        recipe = Recipe(recipe_link)
        print(recipe.ingredient_breakdown(debug=True))

    elif command == 'b':
        # collect recipe urls and scrape one at a time
        links = []
        while True:
            link = input("Input recipe link, d for done > ")
            if link == 'd':
                break
            else:
                links.append(link)

        for link in links:
            recipe_client.add_recipe(link)

    elif command == "q":
        # exit the CLI
        exit()

    cont = input("Continue? [y/n] > ")

    if cont == "y":
        pass
    else:
        exit()


if __name__ == "__main__":
    while True:
        run_cli()
