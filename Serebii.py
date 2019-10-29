import logging
import pathlib
import re
from typing import Dict, Optional, Any

import requests
from bs4 import BeautifulSoup

TOP_DIR = pathlib.Path(__file__).resolve().parent
LOG_DIR = TOP_DIR.joinpath('logs')

LOGGER = logging.getLogger(__name__)


class Pokemon:
    def __init__(self, pokemon_data):
        self.name = pokemon_data[1]
        self.classification = pokemon_data[4]
        self.height = pokemon_data[5]
        self.weight = pokemon_data[6]
        self.male_ratio = None
        self.female_ratio = None
        self.gender = pokemon_data[3]
        self.egg_distance = pokemon_data[9]
        self.buddy_distance = pokemon_data[10]
        self.second_charge_attack = pokemon_data[11]
        self.req_to_evolve = pokemon_data[13]

    # Finds only the gender ratio's through the list of tags
    def clean_gender(self):
        find_starts = [match.start() for match in re.finditer('<td>', str(self.gender))]

        # 0 means the pokemon is Genderless
        if not len(find_starts) == 0:
            find_ends = [match.start() for match in re.finditer('</td>', str(self.gender))]
            male_chance = str(self.gender)[find_starts[0] + 49:find_ends[1]][:-1]
            female_chance = str(self.gender)[find_starts[2] + 51:find_ends[3]][:-1]
            self.male_ratio = float(male_chance) / 100.0
            if self.male_ratio == 0.0:
                self.male_ratio = None
            self.female_ratio = float(female_chance) / 100.0
            if self.female_ratio == 0.0:
                self.female_ratio = None

    # Transforms the various evolution structures into a list
    # Example evolution structure 1 [ 1 -> 2 -> 3 ]
    # Example evolution structure 2 [ 1 -> 2 OR 1 -> 3]
    def get_req(self, webpage):
        evolve_rows = self.req_to_evolve('tr')
        poke_dict = {}
        self.req_to_evolve = []

        for row in evolve_rows:
            evolution_branch = ''
            new_row = row.tr
            row_data = row('td')

            # Due to how branched evolutions are implimented, additional branches
            # need to be excluded from initial loops.
            if new_row is None:
                data_size = len(row_data)
            else:
                new_row_data = row.td
                data_size = len(row_data) - len(new_row_data) - 1

            for num, data in enumerate(row_data):
                if num == data_size:
                    break

                poke_span = 0

                # rowspan documents how many branches a pokemon should be
                # included in. So where it doesn't exist, set poke_span to 1.
                if data.has_attr('rowspan'):
                    poke_span = int(data.get('rowspan'))
                else:
                    poke_span = 1

                if not data.contents:
                    file_name = 'unknown'
                else:
                    poke_img = data.img
                    file_start = poke_img['src'].rfind('/') + 1
                    file_name = poke_img['src'][file_start:-4]

                if file_name.isdigit():
                    # Convert Pokemon number to name
                    poke_dex_name = webpage.find(value='/pokemongo/pokemon/' + file_name + '.shtml')
                    poke_name = poke_dex_name.contents[0][4:]
                    poke_dict[poke_name] = poke_span
                elif file_name in poke_dict:
                    poke_dict[file_name] += 1
                else:
                    poke_dict[file_name] = poke_span
            # Form single evolution branch
            for value in poke_dict:
                if not poke_dict[value] == 0:
                    evolution_branch += value + ' '
                    poke_dict[value] -= 1
            self.req_to_evolve.append(evolution_branch)


# returns html for a given url
def get_webpage_data(url):
    page_response = requests.get(url)
    page_data = BeautifulSoup(page_response.text, 'html.parser')
    return page_data


def scrape_pokemon(pokemon: Dict[str, Optional[Any]]):
    url = f"https://www.serebii.net/pokemongo/pokemon/{pokemon['pokedex']:03d}.shtml"
    webpage = get_webpage_data(url)
    poke_tables = webpage.find_all(class_='dextab')
    poke_moves = webpage.find(id='moves')
    poke_moves.decompose()
    contents = []

    for table in poke_tables:
        poke_info = table.find_all(class_='fooinfo')

        for poke in poke_info:
            if len(poke) == 1:
                contents.append(poke.contents[0])
            # Accounting for Pokemon with missing fields
            elif len(poke) == 0:
                contents.append(None)
            # Accounting for fields with multi values
            else:
                if '<br/>' in str(poke.contents[1]):
                    double_line_contents = poke.contents[0] + '|' + str(poke.contents[2]).strip()
                    contents.append(double_line_contents)
                else:
                    contents.append(poke.contents[0])

    scraped = Pokemon(contents)
    scraped.clean_gender()
    
    if len(scraped.req_to_evolve) != 1:
        scraped.get_req(webpage)

    pokemon['classification'] = scraped.classification
    pokemon['male_ratio'] = scraped.male_ratio
    pokemon['female_ratio'] = scraped.female_ratio
    if scraped.egg_distance[:-2].isdigit():
        pokemon['egg_distance'] = int(scraped.egg_distance[:-2])
    else:
        pokemon['egg_distance'] = None

    return pokemon


def main():
    for x in range(666, 667):
        pokemon = {
            'pokedex': x,
            'name': None,
            'form': None,
            'classification': None,
            'male_ratio': None,
            'female_ratio': None,
            'egg_distance': None
        }
        scraped = scrape_pokemon(pokemon=pokemon)

        for poke in scraped.keys():
            LOGGER.info('{}: {}'.format(poke.replace('_', ' ').title(), scraped[poke]))
        LOGGER.info('-------------------------')


def init_logger() -> None:
    LOG_DIR.mkdir(exist_ok=True)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(levelname)s] %(asctime)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            console,
            logging.FileHandler(LOG_DIR.joinpath('serebii.log'))
        ]
    )


if __name__ == '__main__':
    init_logger()
    main()
