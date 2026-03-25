from otree.api import *
import json
import csv


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'advice'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 3


class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass


class Player(BasePlayer):
    qid = models.StringField()
    question = models.StringField()
    alpha = models.FloatField(initial=10.0)
    beta = models.FloatField(initial=10.0)
    num_tokens = models.IntegerField(initial=10)
    color = models.StringField()
    bin_labels = models.StringField()
    pre_beliefs = models.StringField()
    post_beliefs = models.StringField()
    correct_bin = models.IntegerField(initial=-1)
    earnings = models.FloatField(initial=0)
    accuracy = models.FloatField()
    efficiency = models.FloatField()
    layout = models.StringField(initial='v')

    mpl_response = models.StringField()
    selected_row = models.IntegerField()
    advice_purchased = models.BooleanField()
    selected_value = models.IntegerField()


# PAGES

class Pre_beliefs(Page):

    form_model = 'player'
    form_fields = ['pre_beliefs']
    template_name = 'advice/Beliefs.html'


    @staticmethod
    def before_next_page(player, timeout_happened):
        response = json.loads(player.pre_beliefs)
        score_response(player, response)

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            qid=player.qid,
            stimulus_path=f"advice/stimulus/{player.qid}.html",

            alpha=player.alpha,
            beta=player.beta,
            num_tokens=player.num_tokens,
            color=json.loads(player.color),
            bin_labels=json.loads(player.bin_labels),
        )


class Mpl(Page):
    form_model = 'player'
    form_fields = ['mpl_response']

    def vars_for_template(player):
        # Define the number of rows for your MPL.
        num_rows = 10
        rows = []

        for i in range(1, num_rows + 1):
            left_option = f"Buy advice for ${i}"
            right_option = "Do not buy advice"

            rows.append({
                'id': i,
                'L': left_option,
                'R': right_option,
            })

        return dict(
            num_rows=num_rows,
            rows=rows
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        import random
        response = json.loads(player.mpl_response)
        num_rows = len(response)
        selected_row_idx = random.randint(0, num_rows - 1)
        player.selected_row = selected_row_idx + 1  # 1-indexed

        # In MyPage: 0 = L (purchase), 1 = R (forego)
        player.advice_purchased = (response[selected_row_idx] == 0)
        player.selected_value = selected_row_idx + 1


class Advice(Page):
    form_model = 'player'

    def is_displayed(player):
        return player.advice_purchased


    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            # This builds the string: "my_app_name/advice/42.html"
            advice_path=f"advice/intervention/{player.qid}.html"
        )


class Post_beliefs(Page):
    form_model = 'player'
    form_fields = ['post_beliefs']
    template_name = 'advice/Beliefs.html'

    @staticmethod
    def before_next_page(player, timeout_happened):
        response = json.loads(player.post_beliefs)
        score_response(player, response)
        # print(player.response)
        # print(json.loads(player.response))

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            qid=player.qid,
            stimulus_path=f"advice/stimulus/{player.qid}.html",

            alpha=player.alpha,
            beta=player.beta,
            num_tokens=player.num_tokens,
            color=json.loads(player.color),
            bin_labels=json.loads(player.bin_labels),
        )


class ResultsWaitPage(WaitPage):
    pass


class Mpl_results(Page):
    def vars_for_template(player: Player):
        num_rows = 10
        rows = []

        for i in range(1, num_rows + 1):
            left_option = f"Buy advice for ${i}"
            right_option = "Do not buy advice"

            rows.append({
                'id': i,
                'L': left_option,
                'R': right_option,
            })

        response = json.loads(player.mpl_response)
        for i, r_choice in enumerate(response):
            rows[i]['choice'] = r_choice

        return dict(
            num_rows=num_rows,
            rows=rows,
            selected_row=player.selected_row,
            is_purchase=player.advice_purchased,
            selected_value=player.selected_value
        )


class Results(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        num_rounds = C.NUM_ROUNDS
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
        for i in range(num_rounds):
            p = player.in_round(i+1)
            sum_accuracy += p.accuracy
            sum_earnings += p.earnings
            sum_efficiency += p.efficiency
            s += "<tr>"
            s += "    <td class='text-center'>" + str(p.round_number) + "</td>"
            s += "    <td class='text-center'>" + str(round(p.accuracy*100, 2)) + "%</td>"
            s += "    <td class='text-center'>$" + str(round(p.earnings, 2)) + "</td>"
            s += "    <td class='text-center'>" + str(round(p.efficiency, 4)) + "</td>"
            s += "</tr>"
        average_accuracy = sum_accuracy / num_rounds if num_rounds > 0 else 0
        average_earnings = sum_earnings / num_rounds if num_rounds > 0 else 0
        average_efficiency = sum_efficiency / num_rounds if num_rounds > 0 else 0
        s += "    <tr>"
        s += "        <td class='text-center'> AVERAGE</td>"
        s += "        <td class='text-center'>" + str(round(average_accuracy*100, 2)) + "%</td>"
        s += "        <td class='text-center'>$" + str(round(average_earnings, 2)) + "</td>"
        s += "        <td class='text-center'>" + str(round(average_efficiency, 4)) + "</td>"
        s += "    </tr>"
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
            # p.question = "Please allocate your tokens based on your belief."

            labels = question_data[1]

            p.bin_labels = json.dumps(labels)
            p.color = json.dumps(['#6495ED'])

            # Layout logic: Normalize to 'h' or 'v'
            layout_input = str(question_data[3]).lower() if len(question_data) > 3 else 'v'
            if layout_input in ['h', 'horizontal']:
                p.layout = 'h'
            else:
                p.layout = 'v'



def score_response(player: Player, response):
    # response = json.loads(player.pre_beliefs)
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

    player.correct_bin = int(player.session.config['questions'][player.subsession.round_number-1][2]) - 1
    player.earnings = ScoringRule(player.correct_bin)

    # response_dict = {f"response_bin{i+1}": response[i] for i in range(min(len(response), 8))}
    # for field, val in response_dict.items():
    #     setattr(player, field, val)

    player.accuracy = response[player.correct_bin]
    player.efficiency = player.earnings / (player.alpha + player.beta)


page_sequence = [Pre_beliefs, Mpl, Mpl_results, Advice, Post_beliefs]
