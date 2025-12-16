from otree.api import *
import json
import csv


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'raven_interface'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 36


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    qid = models.StringField()
    question = models.StringField()
    alpha = models.FloatField()
    num_tokens = models.IntegerField()
    beta = models.FloatField()
    color = models.StringField()
    bin_labels = models.StringField()
    response = models.StringField()
    response_bin1 = models.FloatField(initial=-1)
    response_bin2 = models.FloatField(initial=-1)
    response_bin3 = models.FloatField(initial=-1)
    response_bin4 = models.FloatField(initial=-1)
    response_bin5 = models.FloatField(initial=-1)
    response_bin6 = models.FloatField(initial=-1)
    response_bin7 = models.FloatField(initial=-1)
    response_bin8 = models.FloatField(initial=-1)
    correct_bin = models.IntegerField(initial=-1)
    earnings = models.FloatField(initial=0)
    accuracy = models.FloatField()
    efficiency = models.FloatField()


# PAGES

class Intro(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1



class MyPage(Page):

    @staticmethod
    def is_displayed(player):
        return player.round_number <= player.session.vars['max_round']

    form_model = 'player'
    form_fields = ['response']
    @staticmethod
    def before_next_page(player, timeout_happened):
        score_response(player)
        # print(player.response)
        # print(json.loads(player.response))

    @staticmethod
    def vars_for_template(player: Player):
        qid = player.qid

        image_paths = []

        # Add the base image file
        image_paths.append(f'images/raven/{qid}.png')

        # Add the 8 subfiles with suffixes _1 through _8
        for i in range(1, 9):
            relative_path = f'images/raven/{qid}_{i}.png'
            image_paths.append(relative_path)

        return dict(
            image_paths=image_paths,
        )


class ResultsWaitPage(WaitPage):
    pass


class Results(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == player.session.vars['max_round']

    @staticmethod
    def vars_for_template(player: Player):
        s = f"""
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th scope="col" class="col-1 text-center">Question</th>
                        <th scope="col" class="col-1 text-center">% tokens correctly allocated</th>
                        <th scope="col" class="col-1 text-center">Earnings</th>
                        <th scope="col" class="col-1 text-center">Earnings efficiency</th>
                    </tr>
                </thead>
        """
        sum_accuracy = 0
        sum_earnings = 0
        sum_efficiency = 0
        for i in range(player.session.vars['max_round']):
            p = player.in_round(i+1)
            sum_accuracy += p.accuracy
            sum_earnings += p.earnings
            sum_efficiency += p.efficiency
            s += "<tr>"
            s += "    <td class='text-center'>" + str(p.round_number) + "</td>"
            s += "    <td class='text-center'>" + str(round(p.accuracy*100, 2)) + "</td>"
            s += "    <td class='text-center'>$" + str(round(p.earnings, 2)) + "</td>"
            s += "    <td class='text-center'>" + str(round(p.efficiency, 4)) + "</td>"
            s += "</tr>"
        average_accuracy = sum_accuracy / player.session.vars['max_round']
        average_earnings = sum_earnings / player.session.vars['max_round']
        average_efficiency = sum_efficiency / player.session.vars['max_round']
        s += "    <tr>"
        s += "        <td class='text-center'> AVERAGE</td>"
        s += "        <td class='text-center'>" + str(round(average_accuracy*100, 2)) + "</td>"
        s += "        <td class='text-center'>$" + str(round(average_earnings, 2)) + "</td>"
        s += "        <td class='text-center'>" + str(round(average_efficiency, 4)) + "</td>"
        s += "</table>"

        return dict(
            my_table=s,
        )
# FUNCTIONS

def creating_session(subsession: Subsession):
    if subsession.round_number == 1:
        subsession.session.vars['max_round'] = len(subsession.session.config['questions'])
    if subsession.round_number <= subsession.session.vars['max_round']:
        for p in subsession.get_players():
            p.qid = subsession.session.config['questions'][subsession.round_number-1][0]
            p.question = "Some text goes about here."
            p.alpha = 1
            p.beta = 1
            p.num_tokens = 80
            p.bin_labels = json.dumps(['1', '2', '3', '4', '5', '6', '7', '8', ])
            p.color = json.dumps(['#6495ED'])


def score_response(player: Player):
    response = json.loads(player.response)
    for i in range(len(response)):
        response[i] = response[i] / player.num_tokens
    print(response)
    def ScoringRule(cb):
        SS = 0.0
        # Dim Result As Single
        for i in range(8):
            SS += response[i] * response[i]
            print(i, ' SS: ', SS)
        score = player.alpha + player.beta * ((2 * response[cb]) - SS)
        return score

    player.correct_bin = player.session.config['questions'][player.subsession.round_number-1][2] - 1
    player.earnings = ScoringRule(player.correct_bin)

    player.response_bin1 = response[0]
    player.response_bin2 = response[1]
    player.response_bin3 = response[2]
    player.response_bin4 = response[3]
    player.response_bin5 = response[4]
    player.response_bin6 = response[5]
    player.response_bin7 = response[6]
    player.response_bin8 = response[7]

    player.accuracy = response[player.correct_bin]
    player.efficiency = player.earnings / (player.alpha + player.beta)


page_sequence = [Intro, MyPage, Results]
