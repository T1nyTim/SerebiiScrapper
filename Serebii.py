import requests
import re
from bs4 import BeautifulSoup

class Pokemon:
    def __init__(self, pokemon_data):
        self.name = pokemon_data[1]
        self.classification = pokemon_data[4]
        self.height = pokemon_data[5]
        self.weight = pokemon_data[6]
        self.gender = pokemon_data[3]
        self.egg_distance = pokemon_data[9]
        self.buddy_distance = pokemon_data[10]
        self.second_charge_attack = pokemon_data[11]
        self.req_to_evolve = pokemon_data[13]

    # Finds only the gender ratio's through the list of tags
    def clean_gender(self):
        find_starts = [match.start() for match in re.finditer('<td>', str(self.gender))]

        # -1 means <td> wasn't found, and pokemon is Genderless
        # Genderless is a single tag, so doesn't need to be cleaned
        if not len(find_starts) == 0:
            find_ends = [match.start() for match in re.finditer('</td>', str(self.gender))]
            male_chance = str(self.gender)[find_starts[0]+49:find_ends[1]]
            female_chance = str(self.gender)[find_starts[2]+51:find_ends[3]]
            self.gender = 'Male ' + male_chance + '|Female ' + female_chance

    def get_req(self):
        evolve_info = self.req_to_evolve.find_all('img')
        self.req_to_evolve = ''

        if not len(evolve_info) == 1:
            for num, info in enumerate(evolve_info):
                image_name_start = info['src'].rfind('/') + 1
                req = info['src'][image_name_start:-4]

                # TODO: Get evolutions names, from the page
                if req.isdigit():
                    url = f'https://www.serebii.net/pokemongo/pokemon/{int(req):03d}.shtml'
                    evolution_data = get_webpage_data(url)
                    poke_name = evolution_data.find_all(class_='fooinfo')[1]

                    if num == (len(evolve_info) - 1):
                        self.req_to_evolve += str(poke_name.contents[0])
                    else:
                        self.req_to_evolve += str(poke_name.contents[0]) + ' ---'
                else:
                    self.req_to_evolve += req + '--> '

# returns html for a given url
def get_webpage_data(url):
    page_response = requests.get(url)
    page_data = BeautifulSoup(page_response.text, 'html.parser')
    return page_data

# loops from 1-4
for i in range(80,81):
    # ensures i is 3 digits long, with up to 2 leading zeroes
    url = f'https://www.serebii.net/pokemongo/pokemon/{i:03d}.shtml'
    webpage = get_webpage_data(url)
    # Find start of data to be searched
    poke_tables = webpage.find_all(class_='dextab')
    # Find end of data to be searched
    poke_moves = webpage.find(id='moves')
    poke_moves.decompose()
    contents = []

    for table in poke_tables:
        # Find class with the data itself
        poke_info = table.find_all(class_='fooinfo')

        for poke in poke_info:
            # Handles fooinfo that are spread over 2 lines
            if not len(poke) == 1:
                if '<br/>' in str(poke.contents[1]):
                    double_line_contents = poke.contents[0] + '|' + poke.contents[2].strip()
                    contents.append(double_line_contents)
                else:
                    contents.append(poke.contents[0])
            else:
                contents.append(poke.contents[0])

    pokemon = Pokemon(contents)
    pokemon.clean_gender()
    pokemon.get_req()

    for poke in pokemon.__dict__:
        print('{}: {}'.format(poke,pokemon.__dict__[poke]))
