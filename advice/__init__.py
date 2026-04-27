from otree.api import *
import json
import csv
import random


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'advice'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 6
    PARTICIPATION_FEE = 10.00
    ENDOWMENT = 10.00


class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass


class Player(BasePlayer):
    qid = models.StringField()
    question = models.StringField()
    alpha = models.FloatField(initial=50.0)
    beta = models.FloatField(initial=50.0)
    num_tokens = models.IntegerField(initial=20)
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
    selected_value = models.FloatField()

    pre_BLP_draw = models.FloatField(initial=-1)
    post_BLP_draw = models.FloatField(initial=-1)
    pre_score = models.FloatField(initial=0)
    post_score = models.FloatField(initial=0)
    pre_earnings = models.FloatField(initial=0)
    post_earnings = models.FloatField(initial=0)
    pre_accuracy = models.FloatField(initial=0)
    post_accuracy = models.FloatField(initial=0)
    pre_efficiency = models.FloatField(initial=0)
    post_efficiency = models.FloatField(initial=0)


# PAGES

class Instructions(Page):

    @staticmethod
    def is_displayed(player):
        # Only show instructions on round 1
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            num_tokens=player.num_tokens,
            participation_fee=f"{C.PARTICIPATION_FEE:.2f}",
            endowment=f"{C.ENDOWMENT:.2f}",
            max_earnings=10.00,   # match your hardwired BLP earnings
        )

class Pre_beliefs(Page):

    form_model = 'player'
    form_fields = ['pre_beliefs']
    template_name = 'advice/Beliefs.html'


    @staticmethod
    def before_next_page(player, timeout_happened):
        response = json.loads(player.pre_beliefs)
        score, earnings, accuracy, efficiency = score_response(player, response, player.pre_BLP_draw)
        player.pre_score = score
        player.pre_earnings = earnings
        player.pre_accuracy = accuracy
        player.pre_efficiency = efficiency

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
        num_rows = 7
        rows = []

        for i in range(0, num_rows):
            # The following line is responsible for the monetary values shown in the MPL.
            n = 1 + i*.25
            left_option = f"Buy advice for ${n:.2f}"
            right_option = f"Do not buy advice for ${n:.2f}"

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
        # This line transforms the selected row into the monetary amount shown in the selected row.
        player.selected_value = selected_row_idx * .25 + 1
        player.selected_row = selected_row_idx

        # In MyPage: 0 = L (purchase advice), 1 = R (do not purchase)
        player.advice_purchased = (response[selected_row_idx] == 0)



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
        score, earnings, accuracy, efficiency = score_response(player, response, player.post_BLP_draw)
        player.post_score = score
        player.post_earnings = earnings
        player.post_accuracy = accuracy
        player.post_efficiency = efficiency
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
        num_rows = 7
        rows = []

        for i in range(0, num_rows):
            # this line displays MPL monetary amounts in 25cent increments.
            n = 1 + i * .25
            left_option = f"Buy advice for ${n:.2f}"
            right_option = f"Do not buy advice for ${n:.2f}"

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
            selected_row=player.selected_row + 1,
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

        # ── Performance table ──────────────────────────────────────────
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
            # Use post_ beliefs for final results
            acc = p.post_accuracy
            earn = p.post_earnings
            eff = p.post_efficiency

            sum_accuracy += acc
            sum_earnings += earn
            sum_efficiency += eff
            s += "<tr>"
            s += "    <td class='text-center'>" + str(p.round_number) + "</td>"
            s += "    <td class='text-center'>" + str(round(acc*100, 2)) + "%</td>"
            s += "    <td class='text-center'>$" + str(round(earn, 2)) + "</td>"
            s += "    <td class='text-center'>" + str(round(eff, 4)) + "</td>"
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

        # ── Payment summary ────────────────────────────────────────────
        participation_fee = C.PARTICIPATION_FEE
        endowment = C.ENDOWMENT

        # Build per-round advice cost breakdown
        advice_breakdown = []

        # Sum advice costs across all rounds
        total_advice_cost = 0
        for i in range(1, num_rounds + 1):
            p = player.in_round(i)
            if p.advice_purchased:
                cost = p.selected_value
                total_advice_cost += cost
                advice_breakdown.append(
                    f"Round {i}: -${cost:.2f}"
                )

                #total_advice_cost += p.selected_value  # already stored as dollar amount

        endowment_remaining = max(round(endowment - total_advice_cost, 2), 0)
        total_task_earnings = round(sum_earnings, 2)
        grand_total = round(total_task_earnings + participation_fee + endowment_remaining, 2)

        return dict(
            my_table=s,
            participation_fee=f"{participation_fee:.2f}",
            endowment=f"{endowment:.2f}",
            total_advice_cost=f"{total_advice_cost:.2f}",
            advice_purchased_any=total_advice_cost > 0,
            advice_breakdown=advice_breakdown,  # ← new
            endowment_remaining=f"{endowment_remaining:.2f}",
            total_task_earnings=f"{total_task_earnings:.2f}",
            grand_total=f"{grand_total:.2f}",
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

            p.pre_BLP_draw = round(random.uniform(0, 100), 2)
            p.post_BLP_draw = round(random.uniform(0, 100), 2)



def score_response(player: Player, response, draw):
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

    # BLP START -----------------------
    # This part of code must handle both BLP and non-BLP cases. For now it is fixed for BLP
    score = round(ScoringRule(player.correct_bin), 2)

    # The following line is for non-BLP
    # player.earnings = score

    # The following lines are for BLP
    if draw <= score:
        earnings = 10    # hardwired for $10 presently
    else:
        earnings = 0
    # BLP END -----------------------

    # response_dict = {f"response_bin{i+1}": response[i] for i in range(min(len(response), 8))}
    # for field, val in response_dict.items():
    #     setattr(player, field, val)

    accuracy = response[player.correct_bin]
    efficiency = earnings / (player.alpha + player.beta)

    return score, earnings, accuracy, efficiency


page_sequence = [Pre_beliefs, Mpl, Mpl_results, Advice, Post_beliefs, Results]
