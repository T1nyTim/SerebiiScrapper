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
        # 0 means the pokemon is Genderless
        if not len(find_starts) == 0:
            find_ends = [match.start() for match in re.finditer('</td>', str(self.gender))]
            male_chance = str(self.gender)[find_starts[0]+49:find_ends[1]]
            female_chance = str(self.gender)[find_starts[2]+51:find_ends[3]]
            self.gender = 'Male ' + male_chance + '|Female ' + female_chance

    def get_req(self):
        evolve_rows = self.req_to_evolve('tr')
        poke_dict = {}
        self.req_to_evolve = []
        for row in evolve_rows:
            evolution_branch = ''
            print('=')
            new_row = row.tr
            row_data = row('td')
            if new_row == None:
                data_size = len(row_data)
            else:
                new_row_data = row.td
                data_size = len(row_data) - len(new_row_data) - 1
            for num, data in enumerate(row_data):
                if num == data_size:
                    break
                poke_span = 0
                if data.has_attr('rowspan'):
                    poke_span = int(data.get('rowspan'))
                else:
                    poke_span = 1
                poke_img = data.img
                file_start = poke_img['src'].rfind('/') + 1
                file_name = poke_img['src'][file_start:-4]
                if file_name.isdigit():
                    poke_dex_name = webpage.find(value = '/pokemongo/pokemon/' + file_name + '.shtml')
                    poke_name = poke_dex_name.contents[0][4:]
                    poke_dict[poke_name] = poke_span
                elif file_name in poke_dict:
                    poke_dict[file_name] += 1
                else:
                    poke_dict[file_name] = 1
            for value in poke_dict:
                print('-')
                print(value)
                print(poke_dict)
                print(poke_dict[value])
                if not poke_dict[value] == 0:
                    print(value)
                    evolution_branch += value + ' '
                    poke_dict[value] -= 1
            self.req_to_evolve.append(evolution_branch)

# returns html for a given url
def get_webpage_data(url):
    page_response = requests.get(url)
    page_data = BeautifulSoup(page_response.text, 'html.parser')
    return page_data

for i in range(79,80):
    url = f'https://www.serebii.net/pokemongo/pokemon/{i:03d}.shtml'
    webpage = get_webpage_data(url)
    poke_tables = webpage.find_all(class_='dextab')
    poke_moves = webpage.find(id='moves')
    poke_moves.decompose()
    contents = []

    for table in poke_tables:
        poke_info = table.find_all(class_='fooinfo')
        for poke in poke_info:
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

    # Printing for now, will change general structure of what's created, and create a JSON later
    for poke in pokemon.__dict__:
        print('{}: {}'.format(poke,pokemon.__dict__[poke]))
