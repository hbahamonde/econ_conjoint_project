from otree.api import *
import csv
import random
from pathlib import Path


doc = """
Toy economic conjoint:
- 2 tasks
- 2 candidate photos per task
- left/right randomized
- hidden expandable info
- one timed task and one untimed task
- subjects guess who got more votes
"""


def load_candidate_data():
    data_path = (
        Path(__file__).resolve().parent.parent
        / '_static'
        / 'economic_conjoint'
        / 'data'
        / 'dataset.csv'
    )

    if not data_path.exists():
        raise FileNotFoundError(f'dataset.csv not found at: {data_path}')

    rows = {}
    with open(data_path, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            candidate_id = str(row['ID']).strip()
            rows[candidate_id] = {
                'id': candidate_id,
                'party': row.get('PARTIDO', '').strip(),
                'ideology': row.get('ideologia_cat', '').strip(),
                'age': row.get('age', '').strip() or row.get('EDAD', '').strip(),
                'votes': int(float(row.get('Votos', 0) or 0)),
            }
    return rows


CANDIDATE_DATA = load_candidate_data()


class Constants(BaseConstants):
    name_in_url = 'economic_conjoint'
    players_per_group = None
    num_rounds = 2

    base_points = 100
    time_penalty_per_second = 2

    toy_pairs = [
        ('110108', '113701'),
        ('110702', '119102'),
    ]


class Subsession(BaseSubsession):
    pass


def creating_session(subsession):
    if subsession.round_number != 1:
        return

    for player in subsession.get_players():
        if 'timed_round' not in player.participant.vars:
            player.participant.vars['timed_round'] = random.choice([1, 2])

        if 'pair_order' not in player.participant.vars:
            pair_order = Constants.toy_pairs.copy()
            random.shuffle(pair_order)
            player.participant.vars['pair_order'] = pair_order


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    left_candidate_id = models.StringField()
    right_candidate_id = models.StringField()

    left_info_opened = models.BooleanField(initial=False)
    right_info_opened = models.BooleanField(initial=False)

    timed_task = models.BooleanField(initial=False)

    decision_candidate_id = models.StringField(blank=True)
    decision_side = models.StringField(blank=True)

    time_spent_seconds = models.FloatField(initial=0)

    correct = models.BooleanField(initial=False)
    points_earned = models.IntegerField(initial=0)


def ensure_randomization(player):
    if 'timed_round' not in player.participant.vars:
        player.participant.vars['timed_round'] = random.choice([1, 2])

    if 'pair_order' not in player.participant.vars:
        pair_order = Constants.toy_pairs.copy()
        random.shuffle(pair_order)
        player.participant.vars['pair_order'] = pair_order


def get_pair_for_round(player):
    ensure_randomization(player)
    pair_order = player.participant.vars['pair_order']
    return pair_order[player.round_number - 1]


def assign_positions(player):
    pair = get_pair_for_round(player)
    shuffled = random.sample(list(pair), 2)
    player.left_candidate_id = shuffled[0]
    player.right_candidate_id = shuffled[1]
    player.timed_task = (player.round_number == player.participant.vars['timed_round'])


def candidate_payload(candidate_id):
    row = CANDIDATE_DATA[candidate_id]
    return dict(
        id=row['id'],
        image_path=f'economic_conjoint/images/{row["id"]}.jpg',
        party=row['party'],
        ideology=row['ideology'],
        age=row['age'],
        votes=row['votes'],
    )