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
    NUM_ROUNDS = 4
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
    num_tokens = models.IntegerField(initial=100)
    color = models.StringField()
    bin_labels = models.StringField()
    pre_beliefs = models.StringField()
    post_beliefs = models.StringField()
    correct_bin = models.IntegerField(initial=-1)
    earnings = models.FloatField(initial=0)
    accuracy = models.FloatField()
    efficiency = models.FloatField()
    layout = models.StringField(initial='v')
    treatment = models.StringField()

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
class Consent(Page):

    @staticmethod
    def is_displayed(player):
        # Show only once at the beginning
        return player.round_number == 1

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

        # ── Add pre_beliefs earnings to player.payoff ──────────────
        player.payoff += earnings  # ← oTree accumulates this automatically

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

    @staticmethod
    def is_displayed(player):
        # Only show MPL if it is NOT song01
        return player.qid


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
        # Only show if advice was purchased AND not song01
        return player.advice_purchased


    @staticmethod
    def vars_for_template(player: Player):
        # Route to correct intervention based on treatment
        suffix = 'AL' if player.treatment == 'algorithmic' else 'H'
        advice_path = f"advice/intervention/{player.qid}_{suffix}.html"

        return dict(
            advice_path=advice_path,
            treatment=player.treatment,
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

        # ── Add post_beliefs earnings to player.payoff ─────────────
        player.payoff += earnings  # ← oTree accumulates this automatically

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

    @staticmethod
    def is_displayed(player):
        return player.qid

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
class ThankYou(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS

class Reveal(Page):

    @staticmethod
    def is_displayed(player):
        # Only show on the last round
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        num_rounds = C.NUM_ROUNDS

        # Build list of reveal items matching each round's question
        reveal_items = []
        for i in range(1, num_rounds + 1):
            p = player.in_round(i)
            qid = p.qid

            # Map each qid to a title, image and description
            reveal_map = {
                'weight01': {
                    'title': 'Weight Task — Person 1',
                    'image': 'reveal_weight01.png',
                    'description': 'The correct weight was 170–179 lbs'

                },
                'height01': {
                    'title': 'Height Task — Person 1',
                    'image': 'reveal_height01.png',
                    'description': 'The correct height was  Less than 5 feet'
                },
                'urn01': {
                    'title': 'Urns Task — Proportion of Blue Balls',
                    'image': 'reveal_urn01.png',
                    'description': 'The proportion of blue balls is 60%, range (51%-60%)'
                },
                'song01': {
                    'title': 'Song Ranking Task — Song 1',
                    'image': 'reveal_song01.png',
                    'description': 'The correct Billboard rank was position 8'
                },

            }

            if qid in reveal_map:
                reveal_items.append(reveal_map[qid])

        return dict(
            reveal_items=reveal_items,
        )

class Results(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        num_rounds = C.NUM_ROUNDS

        # ── Question metadata map ──────────────────────────────────────
        question_meta = {
            'height01': {
                'title': 'Estimation Task — Height 1',
                'question': 'Please observe the photo and estimate the height of this person.',
                'true_value': "< 5 feet",

            },
            'weight01': {
                'title': 'Estimation Task — Weight 1',
                'question': 'Estimate the weight of this person in the photograph.',
                'true_value': '170–179 lbs',
            },
            'song01': {
                'title': 'Estimation Task — Song 1',
                'question': 'Please estimate the Billboard Hot 100 rank of this song.',
                'true_value': 'Position 8',
            },
            'song02': {
                'title': 'Estimation Task — Song 2',
                'question': 'Please estimate the Billboard Hot 100 rank of this song.',
                'true_value': 'Position 2',
            },
            'urn01': {
                'title': 'Estimation Task — Urns',
                'question': 'Please estimate the fraction of blue balls in the urn.',
                'true_value': '60% of the balls are blue',
            },
        }

        # ── Build per-task results ─────────────────────────────────────
        task_results = []
        for i in range(num_rounds):
            p = player.in_round(i + 1)
            qid = p.qid
            meta = question_meta.get(qid, {
                'title': f'Task {i + 1}',
                'question': '',
                'true_value': 'N/A',
            })

            # Parse pre beliefs tokens
            pre_bins = []
            post_bins = []
            labels = json.loads(p.bin_labels)

            if p.pre_beliefs:
                pre_tokens = json.loads(p.pre_beliefs)
                for j, label in enumerate(labels):
                    tokens = pre_tokens[j] if j < len(pre_tokens) else 0
                    if tokens > 0:
                        pre_bins.append({
                            'label': label,
                            'tokens': tokens
                        })

            if p.post_beliefs:
                post_tokens = json.loads(p.post_beliefs)
                for j, label in enumerate(labels):
                    tokens = post_tokens[j] if j < len(post_tokens) else 0
                    if tokens > 0:  # ← only include if tokens > 0
                        post_bins.append({
                            'label': label,
                            'tokens': tokens

                        })

            task_results.append({
                'title': meta['title'],
                'question': meta['question'],
                'true_value': meta['true_value'],
                'pre_earnings': f"{p.pre_earnings:.2f}",
                'post_earnings': f"{p.post_earnings:.2f}",
                'pre_bins': pre_bins,
                'post_bins': post_bins,
            })

        # ── Performance table ──────────────────────────────────────────
        s = f"""
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th scope="col" class="col-1 text-center">Question</th>
                        <th scope="col" class="text-center">Report</th>
                        <th scope="col" class="col-1 text-center">% Points Earned</th>
                        <th scope="col" class="col-1 text-center">Earnings</th>
                        <th scope="col" class="col-1 text-center">Efficiency</th>
                    </tr>
                </thead>
        """
        sum_pre_earnings = 0
        sum_post_earnings = 0
        sum_efficiency = 0
        for i in range(num_rounds):
            p = player.in_round(i+1)

            # Get descriptive label for this question
            q_label = question_meta.get(p.qid, {}).get('title', p.qid)
            #q_label = question_meta.get(p.qid, p.qid)

            # ── Pre beliefs row ──────────────────────────────────
            pre_acc = p.pre_accuracy
            pre_earn = p.pre_earnings
            pre_eff = p.pre_efficiency
            pre_points = round(pre_acc * player.num_tokens, 1)  # ← tokens earned
            sum_pre_earnings += pre_earn
            sum_efficiency += pre_eff

            s += "<tr>"
            s += f"    <td class='text-center'>{q_label}</td>"
            s += f"    <td class='text-center'>Report 1 (Before advice)</td>"
            s += f"    <td class='text-center'>{pre_points} pts</td>"
            #s += f"    <td class='text-center'>{round(pre_acc * 100, 2)}%</td>"
            s += f"    <td class='text-center'>${round(pre_earn, 2)}</td>"
            s += f"    <td class='text-center'>{round(pre_eff, 4)}</td>"
            s += "</tr>"

            # ── Post beliefs row ─────────────────────────────────
            post_acc = p.post_accuracy
            post_earn = p.post_earnings
            post_eff = p.post_efficiency
            post_points = round(post_acc * player.num_tokens, 1)  # ← tokens earned
            sum_post_earnings += post_earn
            sum_efficiency += post_eff

            s += "<tr class='table-light'>"
            s += f"    <td class='text-center'>{q_label}</td>"
            s += f"    <td class='text-center'>Report 2 (After advice)</td>"
            s += f"    <td class='text-center'>{post_points} pts</td>"
            #s += f"    <td class='text-center'>{round(post_acc * 100, 2)}%</td>"
            s += f"    <td class='text-center'>${round(post_earn, 2)}</td>"
            s += f"    <td class='text-center'>{round(post_eff, 4)}</td>"
            s += "</tr>"

        total_reports = num_rounds * 2
        sum_earnings = sum_pre_earnings + sum_post_earnings
        avg_efficiency = sum_efficiency / total_reports if total_reports > 0 else 0
        avg_earnings = sum_earnings / total_reports if total_reports > 0 else 0
        avg_accuracy = (sum_efficiency * (player.alpha + player.beta)) / total_reports if total_reports > 0 else 0

        s += "<tr class='table-secondary'>"
        s += "    <td class='text-center' colspan='2'><strong>TOTAL</strong></td>"
        s += f"   <td class='text-center'>—</td>"
        s += f"   <td class='text-center'><strong>${round(sum_earnings, 2)}</strong></td>"
        s += f"   <td class='text-center'>{round(avg_efficiency, 4)}</td>"
        s += "</tr>"
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

        # Use oTree's built-in payoff accumulation
        participant_payoff = float(player.participant.payoff)
        grand_total = round(
            participant_payoff + participation_fee + endowment_remaining, 2
        )

        return dict(
            my_table=s,
            participation_fee=f"{participation_fee:.2f}",
            task_results=task_results,
            endowment=f"{endowment:.2f}",
            total_advice_cost=f"{total_advice_cost:.2f}",
            advice_purchased_any=total_advice_cost > 0,
            advice_breakdown=advice_breakdown,  # ← new
            endowment_remaining=f"{endowment_remaining:.2f}",
            total_task_earnings=f"{total_task_earnings:.2f}",
            grand_total=f"{grand_total:.2f}",
            total_pre_earnings=f"{sum_pre_earnings:.2f}",
            total_post_earnings=f"{sum_post_earnings:.2f}",
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

            # ── Randomly assign treatment ──────────────────────────
            # Only assign once in round 1, carry forward to other rounds
            if subsession.round_number == 1:
                p.treatment = random.choice(['algorithmic', 'human'])
            else:
                # Keep same treatment across all rounds
                p.treatment = p.in_round(1).treatment



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


page_sequence = [Consent, Instructions, Pre_beliefs, Mpl, Mpl_results, Advice, Post_beliefs, ThankYou, Reveal, Results]
