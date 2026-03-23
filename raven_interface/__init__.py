from otree.api import *
import json
import csv


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'raven_interface'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 3


class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass


class Player(BasePlayer):
    qid = models.StringField()
    question = models.StringField()
    stimulus_html = models.LongStringField()
    alpha = models.FloatField(initial=1.0)
    num_tokens = models.IntegerField(initial=80)
    beta = models.FloatField(initial=1.0)
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


class MyPage(Page):

    form_model = 'player'
    form_fields = ['response']
    @staticmethod
    def before_next_page(player, timeout_happened):
        score_response(player)
        # print(player.response)
        # print(json.loads(player.response))

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            qid=player.qid,
            stimulus_html=player.stimulus_html,

            alpha=player.alpha,
            beta=player.beta,
            num_tokens=player.num_tokens,
            color=json.loads(player.color),
            bin_labels=json.loads(player.bin_labels),
        )


class ResultsWaitPage(WaitPage):
    pass


class Results(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        max_round = player.session.vars.get('max_round', 0)
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
        for i in range(max_round):
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
        average_accuracy = sum_accuracy / max_round if max_round > 0 else 0
        average_earnings = sum_earnings / max_round if max_round > 0 else 0
        average_efficiency = sum_efficiency / max_round if max_round > 0 else 0
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
    print('hello world')
    questions = subsession.session.config['questions']
    print(questions)

    if subsession.round_number <= len(questions):
        for p in subsession.get_players():
            question_data = questions[subsession.round_number - 1]
            p.qid = str(question_data[0])
            p.stimulus_html = str(question_data[1])
            # p.question = "Please allocate your tokens based on your belief."

            labels = question_data[2]

            p.bin_labels = json.dumps(labels)
            p.color = json.dumps(['#6495ED'])



def score_response(player: Player):
    response = json.loads(player.response)
    num_bins = len(response)
    for i in range(len(response)):
        response[i] = response[i] / player.num_tokens
    print(response)
    def ScoringRule(cb):
        SS = 0.0
        # Dim Result As Single
        for i in range(num_bins):
            SS += response[i] * response[i]
            print(i, ' SS: ', SS)
        score = player.alpha + player.beta * ((2 * response[cb]) - SS)
        return score

    player.correct_bin = int(player.session.config['questions'][player.subsession.round_number-1][3]) - 1
    player.earnings = ScoringRule(player.correct_bin)

    response_dict = {f"response_bin{i+1}": response[i] for i in range(min(len(response), 8))}
    for field, val in response_dict.items():
        setattr(player, field, val)

    player.accuracy = response[player.correct_bin]
    player.efficiency = player.earnings / (player.alpha + player.beta)


page_sequence = [ MyPage, Results]
