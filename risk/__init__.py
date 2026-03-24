from otree.api import *
import random
import json
import itertools
import csv

c = Currency

doc = """
Your app description
"""


class Constants(BaseConstants):
    name_in_url = 'risk'
    players_per_group = None
    num_rounds = 60


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    qid = models.StringField()
    left_lottery = models.StringField()
    right_lottery = models.StringField()
    response = models.StringField()
    random_number = models.IntegerField()
    random_coin = models.StringField()



# FUNCTIONS

def creating_session(subsession):

    if subsession.round_number == 1:
        print(subsession.session.vars)
        params = subsession.session.config['risk_params']
        sample_sizes = subsession.session.config['risk_sample_sizes']
        subsession.session.vars['risk_last_round'] = sum(sample_sizes)
        # n = subsession.session.vars['risk_last_round']

    # blocks = params[0]

    for p in subsession.get_players():
        if subsession.round_number == 1:
            p.participant.vars['selected_risk_questions'] = []

            for b in params:
                print('b', b)
                print('b index', params.index(b))
                print('sample_sizes', sample_sizes)
                print('a', p.participant.vars['selected_risk_questions'])
                p.participant.vars['selected_risk_questions'].append(random.sample(b, sample_sizes[params.index(b)]))
                print('b', p.participant.vars['selected_risk_questions'])
            # Eventually we want additional options here that would allow for presenting questions in block sequence,
            # and perhaps shuffling block order. For now, we will simply randomize questions across blocks.

            # IMPORTANT: questions are currently still in separate block sublists. We must extract them from the sublists
            # so that they are all in a top level without being grouped by block. Then we can shuffle this top level list.

            p.participant.vars['selected_risk_questions'] = list(itertools.chain.from_iterable(p.participant.vars['selected_risk_questions']))

            random.shuffle(p.participant.vars['selected_risk_questions'])

        if subsession.round_number <= subsession.session.vars['risk_last_round']:
            # question_number = p.participant.vars['risk_sequence'][subsession.round_number - 1]
            # print('r', subsession.round_number)
            # print('length of pvars_r_questions', len(p.participant.vars['selected_risk_questions']))
            question = p.participant.vars['selected_risk_questions'][subsession.round_number - 1]
            # print('pvars_selected_risk_questions', p.participant.vars['selected_risk_questions'])
            # print('q:', question)
            p.qid = question[0]
            p.left_lottery = json.dumps(question[1])
            p.right_lottery = json.dumps(question[2])
            p.random_number = random.randint(1, 100)
            p.random_coin = random.choice(['D', 'N'])


def check_partition(random_int, original_partition):
    """
    Checks which part of the original partition a random integer falls into.

    Args:
      random_int: A random integer between 1 and the total length of the expanded partition (inclusive).
      original_partition: A list representing the partition of the probability space.
                          Each element in the list represents the size of a segment
                          in the expanded partition.

    Returns:
      The index of the original partition the random integer corresponds to.
      Returns None if the input is outside the valid range.
    """
    total_length = sum(original_partition)
    if not 1 <= random_int <= total_length:
        return None

    expanded_partition = []
    for i, size in enumerate(original_partition):
        expanded_partition.extend([i] * size)

    return expanded_partition[random_int - 1]


#
# PAGES
#
class Instructions(Page):
    def is_displayed(player):
        return player.subsession.round_number == 1

    def vars_for_template(player):
        return dict(

        )


class MyPage(Page):
    form_model = 'player'
    form_fields = ['response']

    def vars_for_template(player):
        return dict(
            qid=player.qid,
            left_lottery=json.loads(player.left_lottery),
            right_lottery=json.loads(player.right_lottery),
        )

    def is_displayed(player):
        return player.subsession.round_number <= player.subsession.session.vars['risk_last_round']

    def before_next_page(player: Player, timeout_happened):
        # After participant makes all choices, select a round for payment and determine payoff.
        if player.round_number == player.subsession.session.vars['risk_last_round']:

            lottery = None

            # Randomly select a prior round and save the associated player instance
            p_prior = random.choice(player.in_all_rounds())

            if p_prior.pre_beliefs == 'L':
                lottery = json.loads(p_prior.left_lottery)
            elif p_prior.pre_beliefs == 'R':
                lottery = json.loads(p_prior.right_lottery)
            outcome = check_partition(p_prior.random_number, lottery[0])

            payoff = -999
            # Payoff calculation must handle compound lotteries
            if len(lottery) == 2:
                # A simple lottery
                payoff = lottery[1][outcome]
            else:
                # A compound lottery. Check the DoN indicator vector to see if the outcome has DoN
                if lottery[2][outcome] == 1:
                    if p_prior.random_coin == 'D':
                        payoff = 2 * lottery[1][outcome]
                    else:
                        payoff = 0
                else:
                    payoff = lottery[1][outcome]

            # using the built-in payoff field
            player.participant.risk_payoff_round = p_prior.round_number
            player.participant.risk_payoff = payoff
            # The following line updates the otree built-in payment variable
            player.payoff = payoff

            # print(player.participant.vars)

class Results(Page):
    def is_displayed(player):
        return player.subsession.round_number == player.subsession.session.vars['risk_last_round']

    def vars_for_template(player: Player):
        prior_round = player.participant.vars['risk_payoff_round']
        p_prior = player.in_round(prior_round)

        # Show the coin only if dealing with a compound lottery
        show_coin = False
        if p_prior.response == 'L':
            selected_lottery = json.loads(p_prior.left_lottery)
        else:
            selected_lottery = json.loads(p_prior.right_lottery)
        if len(selected_lottery) == 3:
            # We have a compound lottery, so let's check if the outcome involved a DoN
            outcome = check_partition(p_prior.random_number, selected_lottery[0])
            if selected_lottery[2][outcome] == 1:
                show_coin = True

        return dict(
            num_rounds=p_prior.subsession.session.vars['risk_last_round'],
            qid=p_prior.qid,
            left_lottery=json.loads(p_prior.left_lottery),
            right_lottery=json.loads(p_prior.right_lottery),
            random_number=p_prior.random_number,
            random_coin=p_prior.random_coin,
            show_random_coin=show_coin,
            earnings=p_prior.participant.risk_payoff,
            response=p_prior.response,
        )




page_sequence = [Instructions, MyPage, Results]
