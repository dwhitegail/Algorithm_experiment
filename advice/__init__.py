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
    NUM_ROUNDS = 10
    PARTICIPATION_FEE = 10
    ENDOWMENT = 10
    MAX_EARNINGS_PER_REPORT = 50

    # Define which rounds are pre vs post for each task
    WEIGHT_PRE_ROUND = 1
    WEIGHT_POST_ROUND = 2
    HEIGHT_PRE_ROUND = 2  # ← adjust if height is separate
    HEIGHT_POST_ROUND = 2

    # Urns
    URN_PRE_ROUNDS = [3, 4]  # ← both Q1 and Q2 pre-beliefs
    URN_POST_ROUNDS = [5, 6]  # ← both Q1 and Q2 post-beliefs
    URN_MPL_ROUND = 3  # ← MPL shown at start of urns

    # Song
    SONG_PRE_ROUNDS = [7, 8]
    SONG_POST_ROUNDS = [9, 10]
    SONG_MPL_ROUND = 7

    SONG_TITLES = {
        'song01': "Daisies - Justin Bieber",
        'song02': "Ordinary - Alex Warren",
        'song03': "Love Me Not - Ravyn Lenae" ,
        'song04': "Golden - HUNTR/X:EJAE, Audrey Nuna & REI AMI",
        'song05': "Lose Control - Teddy Swims",
        'song06': "Just In Case - Morgan Wallen",
        'song07': "A Bar Song (Tipsy)- Shaboozey",
        'song08': "What I Want -Morgan Wallen ft. Tate McRae",
        'song09': "Soda Pop - Saja Boys",
        'song10': "Luther - Kendrick Lamar",
        'song11': "Die with a Smile -Lady Gaga and Bruno Mars",
        'song12': "Your Idol - Saja Boys",
        'song13': "Not Like Us - Kendrick Lamar",
        'song14': "Birds of a Feather - Billie Ellish",
        'song15': "APT - ROSE and Bruno Mars",
        'song16': "TV OFF - Kendrick Lamar ft. Lefty Gunplay",

    }


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
    advice_purchased = models.BooleanField(initial=False)
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
    display_round = models.IntegerField(initial=1)
    al_advice_source = models.IntegerField(initial=0)  # 0=Claude, 1=Gemini, 2=ChatGPT


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
            participation_fee=f"{C.PARTICIPATION_FEE:.0f}",
            endowment=f"{C.ENDOWMENT:.0f}",
            max_earnings=C.MAX_EARNINGS_PER_REPORT
        )

class Pre_beliefs(Page):

    form_model = 'player'
    form_fields = ['pre_beliefs']
    template_name = 'advice/Beliefs.html'

    @staticmethod
    def is_displayed(player):
        # Show pre-beliefs on rounds 1, 2 (height/weight)
        # AND rounds 3, 4 (urn pre) AND rounds 7, 8 (song pre)
        return player.round_number in [1, 2, 3, 4, 7, 8]


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
            stimulus_path=f"shared_stimulus/{player.qid}.html",

            alpha=player.alpha,
            beta=player.beta,
            num_tokens=player.num_tokens,
            color=json.loads(player.color),
            bin_labels=json.loads(player.bin_labels),
            display_round=1,  # ← always show "Round 1" for pre-beliefs
        )

class Preview_Advice(Page):

    @staticmethod
    def is_displayed(player):
       return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        # Tell subject which type of advice they will receive
        # but don't show the actual advice yet
        if player.treatment == 'algorithmic':
            advice_type = "Algorithmic Advice"
            advice_description = (
                "The Algorithmic advice for the height, weight and urns tasks have been generated by <strong>"
                "Google Gemini Pro 3.1, Claude Sonnet 4.6 and ChatGPT 5.5.</strong> "
                "You will <strong>randomly</strong> receive advice <strong>from one</strong> of them "


            )
        elif player.treatment == 'human':
            advice_type = "Human Advice"
            advice_description = (
                "This advice is based on the aggregated average estimates "
                "of 40 other subjects like you who completed this task "
                "in a previous study."
            )

        else:
            # treatment == 'none'
            advice_type = "No Advice"
            advice_description = (
                "You have not been selected to receive advice for this experiment. "
                "Please proceed to update your beliefs based on your own judgment."
            )

        return dict(
            advice_type=advice_type,
            advice_description=advice_description,
            treatment=player.treatment,
        )

class Mpl(Page):
    form_model = 'player'
    form_fields = ['mpl_response']

    @staticmethod
    def is_displayed(player):
        mpl_rounds = [1, 2, 4, 8]
        return player.round_number in mpl_rounds and player.treatment != 'none'


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
            rows=rows,
            treatment_label = player.treatment.capitalize(),
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if player.treatment != 'none':
            response = json.loads(player.mpl_response)
            num_rows = len(response)
            selected_row_idx = random.randint(0, num_rows - 1)
        # This line transforms the selected row into the monetary amount shown in the selected row.
            player.selected_value = selected_row_idx * .25 + 1
            player.selected_row = selected_row_idx

        # In MyPage: 0 = L (purchase advice), 1 = R (do not purchase)
            player.advice_purchased = (response[selected_row_idx] == 0)

        else:
            # Set defaults for no advice treatment
            player.mpl_response = json.dumps([-999] * 7)
            player.advice_purchased = False
            player.selected_value = 0.0
            player.selected_row = 0


class Advice(Page):
    form_model = 'player'

    def is_displayed(player):
        # Show advice on same rounds as MPL if purchased
        mpl_rounds = [1, 2, 4, 8]
        # Only show if advice was purchased AND treatment is NOT 'none'
        return (
            player.round_number in mpl_rounds
            and player.treatment != 'none'
            and player.advice_purchased
        )


    @staticmethod
    def vars_for_template(player: Player):
        # Route to correct intervention based on treatment
        suffix = 'AL' if player.treatment == 'algorithmic' else 'H'

        qid = player.qid

        # Song title (save BEFORE changing qid)
        song_title = C.SONG_TITLES.get(qid, "")

        if suffix == 'AL':
            # ── ALGORITHMIC advice routing ─────────────────────────
            if qid.startswith('weight'):
                advice_qid = qid  # weight01_AL.html, weight02_AL.html, etc.

            elif qid.startswith('height'):
                advice_qid = qid  # height01_AL.html, height02_AL.html, etc.

            elif qid.startswith('urn'):
                # urn01/02 → urn01_AL, urn03/04 → urn03_AL, urn05/06 → urn05_AL
                urn_pair_map = {'urn02': 'urn01', 'urn04': 'urn03', 'urn06': 'urn05'}
                advice_qid = urn_pair_map.get(qid, qid)

            elif qid.startswith('song'):
                advice_qid = 'song'  # song_AL.html for all songs

            else:
                advice_qid = qid

        else:
            # ── HUMAN advice routing ───────────────────────────────
            if qid.startswith('weight'):
                advice_qid = 'weight'  # weight_H.html for all weight questions

            elif qid.startswith('height'):
                advice_qid = 'height'  # height_H.html for all height questions

            elif qid.startswith('urn'):
                advice_qid = 'urn'  # urn_H.html for all urns

            elif qid.startswith('song'):
                advice_qid = 'song'  # song_H.html for all songs

            else:
                advice_qid = qid

        advice_path = f"advice/intervention/{advice_qid}_{suffix}.html"

        return dict(
            advice_path=advice_path,
            treatment=player.treatment,
            al_advice_source=player.al_advice_source,  # ← pass index to template
            qid=player.qid,
            song_title=song_title,
        )


class Post_beliefs(Page):
    form_model = 'player'
    form_fields = ['post_beliefs']
    template_name = 'advice/Beliefs.html'

    @staticmethod
    def is_displayed(player):
        # Post-beliefs: height/weight same round as pre
        # Urns post: rounds 5, 6
        # Song post: rounds 9, 10
        return player.round_number in [1, 2, 5, 6, 9, 10]

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
            stimulus_path=f"shared_stimulus/{player.qid}.html",

            alpha=player.alpha,
            beta=player.beta,
            num_tokens=player.num_tokens,
            color=json.loads(player.color),
            bin_labels=json.loads(player.bin_labels),
            display_round=2,  # ← always show "Round 2" for post-beliefs
        )


class ResultsWaitPage(WaitPage):
    pass


class Task_Intro(Page):

    @staticmethod
    def is_displayed(player):
        # Only show before the FIRST pre-beliefs of each task
        return player.round_number in [1, 2, 3, 7]

    @staticmethod
    def vars_for_template(player: Player):

        intros = {
            1: {
                'task_number': 'Task 1',
                'task_name': 'Reporting Beliefs about Weight',
                'icon': '⚖️',
                'intro': (
                    "In this task, you will view <strong>1 photograph</strong> of a "
                    "real person and asked to report your beliefs about their weight in pounds. "
                    "You will allocate <strong>100 tokens</strong> across a range of weight intervals in <strong>10 bins</strong>. " 
                    "Place the tokens in the bin or bins that you think represents the correct answer(s). "
                    "Bin 1 represents a weight of less than 120 lbs., bin 2 represents an interval of 120-129 lbs., bin 3, 130-139 lbs, and so on. "
                    "Bin 10 represents the interval of greater than or equal to 200 lbs."
                    " The more tokens you place in the correct bin, the higher your potential earnings. Think carefully, "
                    "every token counts!"
                ),
                'note': (
                    "Note: Consider the person's visible body type and height cues before allocating your tokens. "
                    "If you are more familiar with calculating weight using kilograms (kg), the conversion guide is"
                    " 1 pound (lb.) = 0.45 kilogram (kg) and 1 kilogram (kg.) = 2.2 pounds (lbs.)"
                ),


                'Expectations': [
                    "You will observe <strong>1 photograph</strong> of an individuals.",
                    "You will be asked to report your beliefs  about the weight in <strong>pounds (lbs.)</strong> by allocating <strong>100 tokens across 10 bins.</strong>",
                    "The weight intervals are from <strong>less than 120 lbs</strong> to <strong>greater than or equal to  200 lbs</strong>.",
                    "Each report pays up to <strong>${}</strong> based on accuracy.".format(C.MAX_EARNINGS_PER_REPORT),
                    "You may <strong>purchase advice</strong> between round 1 and round 2 if selected to receive advice.",

                ],
            },

            2: {
                'task_number': 'Task 2',
                'task_name': 'Reporting Beliefs about Height',
                'icon': '📏',
                'intro': (
                    "In this task, you will view <strong>1 photograph</strong> of a real person and "
                    "report your beliefs about their height in feet and inches. You will express your beliefs by distributing <strong>100 tokens across 10 bins</strong> of successive height "
                    "intervals. "
                    "Bin 1 represents a height of less than 5 feet, bin 2 represents an interval from 5 feet to 5 feet, 2 inches, and so on. "
                    "Bin 10 represents the interval of greater than or equal to 7 feet. "
                    "Take your time and observe the photo carefully before making your allocations."
                ),
                'note': (
                    "Note: Look for contextual cues in the photo — surrounding "
                    "objects, posture, and proportions can all help you gauge height. "
                    "If you are more familiar with calculating height using centimeters (cm), the conversion guide is "
                    "1 foot ≈ 30.48 centimeters (cm) and 1 inch = 2.54 cm. Recall that 12 inches = 1 foot. "

                ),

                'Expectations': [
                    "You will be asked to report your beliefs about the height in <strong>feet and inches</strong> of <strong>1 person</strong>.",
                    "The height intervals are from <strong>Under 5 feet (5'0\")</strong> to <strong>Over 7 feet (7'0\")</strong>.",
                    "Each report pays up to <strong>${}</strong> based on accuracy.".format(C.MAX_EARNINGS_PER_REPORT),
                    "You may <strong>purchase advice</strong> between Round 1 and Round 2 if selected to receive advice.",

                ],
            },
            3: {
                'task_number': 'Task 3',
                'task_name': 'Urns Task — What is the percentage of blue balls in the urn?',
                'icon': '🏺',
                'intro': (
                    "This task has an urn containing exactly <strong>100 balls</strong>. Each ball is either "
                    "<strong>blue</strong> or <strong>orange</strong>. "
                    "You do not know how many of each color are inside the urn. "
                    "Because there are exactly 100 balls, the <strong>percentage</strong> of blue balls "
                    "is exactly equal to the actual <strong>number</strong> of blue balls. "
                    "So if you think there are 30 blue balls then the percentage of blue balls in the urn is 30%."
                    "<br><br>"
                    
                    "You will be given <strong>2 samples of 20 draws each</strong> from this urn. "
                    "A <strong>sample</strong> is just a small peek inside the urn. "
                    "Your role is to use each sample to report your beliefs about the total percentage of "
                    "<strong>blue balls</strong> in the full urn. "
                    "First, you will <strong>observe a 20-draw sample,</strong> report your beliefs, "
                    "and then <strong>observe a second 20-draw sample</strong> from the exact <strong>same urn</strong> before reporting again."

                ),
                'note': (
                    "A <strong>draw</strong> means one ball is randomly selected from the urn, its color "
                    "is recorded, and then it is placed <strong>back</strong> into the urn before the next draw. "
                    "Remember, your 20 draws are just a sample — they give you clues, but the percentage of blue balls "
                    "in the sample is not necessarily the same as in the full urn."
                ),
                'Expectations': [
                    "You will be shown <strong>2 separate samples</strong> of 20 draws each.",
                    "After each sample, allocate your <strong>100 tokens</strong> across <strong>10 bins</strong> to reflect "
                    "your beliefs about the <strong>percentage of blue balls in the full urn</strong>.",
                    "The bins are in 10% increments with bin 1 ranging from <strong>0–10% </strong> up to bin 10 ranging from <strong>91–100% </strong>.",
                    "Place the tokens in the bin or bins you think has the correct answer.",

                ],
            },
            7: {
                'task_number': 'Task 4',
                'task_name': 'Billboard Hot 100 Song Ranking',
                'icon': '🎵',
                'intro': (
                    "In this task, you will be asked to report your beliefs about the <strong>ranking</strong> of <strong>two songs</strong> "
                    "on the <strong>Billboard Hot 100 chart</strong> for a given week.  "
                    "You will be shown each song's chart performance over the four preceding weeks "
                    "before making your decision. "
                    "<br>" "<br>"
                    "As in the other tasks, you will report your beliefs by distributing <strong>100 tokens across</strong> "
                    "possible ranking bins. Bin 1 corresponds to the song being ranked #1 for that week! "
                    "Bin 2 corresponds to the song being ranked #2 for that week and so on. Bin 10 represents that the song placed 10th "
                    "or higher on the chart for that week!"
                ),
                'note': (
                    "Note: The Billboard Hot 100 is the definitive weekly ranking of the most popular songs in the United States, "
                    "based on a combination of record sales, radio airplay, and how frequently people stream songs online.  "
                    "It includes music from all genres (pop, rock, country, rap, etc.). "

                ),

                'Expectations': [
                    "You will report your beliefs about the ranking of <strong>2 songs</strong>.",
                    "You will see each song's Billboard chart performance for <strong>4 weeks prior</strong>.",
                    "You will complete <strong>Round 1 for both songs</strong> before the advice phase.",
                    "After the advice phase, you will complete <strong>Round 2 for both songs</strong>.",
                    "Rank each song using <strong>10 bins</strong>: Bin 1 = #1 on the chart, Bin 10 = ranked 10th or higher.",
                    "Each report pays up to <strong>${}</strong> based on accuracy.".format(C.MAX_EARNINGS_PER_REPORT),
                    "You may <strong>purchase advice once</strong> — after completing round 1 for both songs.",

                ],
            },
        }

        info = intros.get(player.round_number, {
            'task_number': 'Next Task',
            'task_name': '',
            'icon': '📋',
            'intro': 'Please proceed to the next task.',
            'note': '',
            'Expectations': []
        })

        return dict(
            task_number=info['task_number'],
            task_name=info['task_name'],
            icon=info['icon'],
            intro=info['intro'],
            note=info['note'],
            Expectations=info['Expectations'],
            max_earnings=f"{C.MAX_EARNINGS_PER_REPORT:.2f}",
        )




class Mpl_results(Page):

    @staticmethod
    def is_displayed(player):
        mpl_rounds = [1, 2, 4, 8]
        return player.round_number in mpl_rounds and player.treatment != 'none'

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
            selected_row=player.selected_row,
            selected_row_display=player.selected_row + 1,
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
                    'title': 'Urns Task Sequence 1 & 2— Percentage of Blue Balls',
                    'image': 'reveal_urn01&02.png',
                    'description': 'The proportion of blue balls is 55%, range (51%-60%)'

                },
                'song01': {
                    'title': 'Song Ranking Task — Song 1',
                    'image': 'reveal_song01.png',
                    'description': 'The correct Billboard rank was position 8'
                },
                'song02': {
                    'title': 'Song Ranking Task — Song 2',
                    'image': 'reveal_song02.png',
                    'description': 'The correct Billboard rank was position 2'
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
        chosen_qids = [
            player.participant.vars['chosen_weight'],
            player.participant.vars['chosen_height'],
            player.participant.vars['chosen_urn1'],
            player.participant.vars['chosen_urn2'],
            player.participant.vars['chosen_urn1'],  # post
            player.participant.vars['chosen_urn2'],  # post
            player.participant.vars['chosen_song1'],
            player.participant.vars['chosen_song2'],
            player.participant.vars['chosen_song1'],  # post
            player.participant.vars['chosen_song2'],  # post
        ]

        # # ── Question metadata map ──────────────────────────────────────
        # question_meta = {
        #     'height01': {
        #         'title': 'Estimation Task — Height 1',
        #         'question': 'Please observe the photo and estimate the height of this person.',
        #         'true_value': "< 5 feet",
        #
        #     },
        #     'weight01': {
        #         'title': 'Estimation Task — Weight 1',
        #         'question': 'Estimate the weight of this person in the photograph.',
        #         'true_value': '170–179 lbs',
        #     },
        #     'song01': {
        #         'title': 'Estimation Task — Song 1',
        #         'question': 'Please estimate the Billboard Hot 100 rank of this song.',
        #         'true_value': 'Position 8',
        #     },
        #     'song02': {
        #         'title': 'Estimation Task — Song 2',
        #         'question': 'Please estimate the Billboard Hot 100 rank of this song.',
        #         'true_value': 'Position 2',
        #     },
        #     'urn01': {
        #         'title': 'Estimation Task — Urns_Period 1',
        #         'question': 'Please estimate the fraction of blue balls in the urn.',
        #         'true_value': '60% of the balls are blue',
        #     },
        #     'urn02': {
        #         'title': 'Estimation Task — Urns_Period 2',
        #         'question': 'Please estimate the fraction of blue balls in the urn.',
        #         'true_value': '60% of the balls are blue',
        #     },
        # }

        question_meta = {}

        # Weight questions
        weight_true_values = {
            'weight01': '170–179 lbs', 'weight02': '<120 lbs',
            'weight03': '120–129 lbs', 'weight04': '140–149 lbs',
            'weight05': '≥200 lbs', 'weight06': '≥200 lbs',
            'weight07': '170–179 lbs', 'weight08': '130–139 lbs',
            'weight09': '150–159 lbs', 'weight10': '170–179 lbs',
            'weight11': '≥200 lbs', 'weight12': '160–169 lbs',
            'weight13': '160–169 lbs', 'weight14': '160–169 lbs',
            'weight15': '160–169 lbs',
        }
        for qid, tv in weight_true_values.items():
            question_meta[qid] = {
                'title': 'Weight Task',
                'question': 'Estimate the weight of this person in the photograph.',
                'true_value': tv,
            }

        # Height questions
        height_true_values = {
            'height01': "< 5'0\"", 'height02': "5'9\"–5'11\"",
            'height03': "5'3\"–5'5\"", 'height04': "5'3\"–5'5\"",
            'height05': "5'6\"–5'8\"", 'height06': "5'6\"–5'8\"",
            'height07': "5'6\"–5'8\"", 'height08': "5'9\"–5'11\"",
            'height09': "6'0\"–6'2\"", 'height10': "6'0\"–6'2\"",
            'height11': "< 5'0\"", 'height12': "6'0\"–6'2\"",
            'height13': "6'0\"–6'2\"", 'height14': "6'3\"–6'5\"",
            'height15': "5'6\"–5'8\"",
        }
        for qid, tv in height_true_values.items():
            question_meta[qid] = {
                'title': 'Height Task',
                'question': 'Please observe the photo and estimate the height of this person.',
                'true_value': tv,
            }

        # Urn questions
        urn_true_values = {
            'urn01': '51%–60% blue', 'urn02': '51%–60% blue',
            'urn03': '31%–40% blue', 'urn04': '31%–40% blue',
            'urn05': '21%–30% blue', 'urn06': '21%–30% blue',
        }
        for qid, tv in urn_true_values.items():
            question_meta[qid] = {
                'title': 'Urns Task',
                'question': 'Please estimate the percentage of blue balls in the urn.',
                'true_value': tv,
            }

        # Song questions
        song_true_values = {
            'song01': 'Position 8', 'song02': 'Position 2',
            'song03': 'Position 6', 'song04': 'Position 1',
            'song05': 'Position 7', 'song06': 'Position 9',
            'song07': 'Position 10', 'song08': 'Position 3',
            'song09': 'Position 5', 'song10': 'Position 10',
            'song11': 'Position 10', 'song12': 'Position 4',
            'song13': 'Position 8', 'song14': 'Position 7',
            'song15': 'Position 10', 'song16': 'Position 10',
        }
        for qid, tv in song_true_values.items():
            question_meta[qid] = {
                'title': 'Song Ranking Task',
                'question': 'Please estimate the Billboard Hot 100 rank of this song.',
                'true_value': tv,
            }

        def get_bins(belief_str, labels):
            if not belief_str:
                return []
            tokens = json.loads(belief_str)
            return [
                {'label': labels[j], 'tokens': tokens[j]}
                for j in range(len(labels))
                if j < len(tokens) and tokens[j] > 0
            ]

        # ── Build per-task results ─────────────────────────────────────
        task_results = []

        # ── Task 1: Weight (pre=round1, post=round1) ──────────────────
        p_pre = player.in_round(1)
        p_post = player.in_round(1)
        labels = json.loads(p_pre.bin_labels)
        meta = question_meta.get(p_pre.qid, {'title': 'Weight Task', 'question': '', 'true_value': 'N/A'})
        task_results.append({
            'title': 'Weight Task',
            'question': meta['question'],
            'true_value': meta['true_value'],
            'pre_earnings': f"{p_pre.pre_earnings:.2f}",
            'post_earnings': f"{p_post.post_earnings:.2f}",
            'pre_bins': get_bins(p_pre.field_maybe_none('pre_beliefs'), labels),
            'post_bins': get_bins(p_post.field_maybe_none('post_beliefs'), labels),
        })

        # ── Task 2: Height (pre=round2, post=round2) ──────────────────
        p_pre = player.in_round(2)
        p_post = player.in_round(2)
        labels = json.loads(p_pre.bin_labels)
        meta = question_meta.get(p_pre.qid, {'title': 'Height Task', 'question': '', 'true_value': 'N/A'})
        task_results.append({
            'title': 'Height Task',
            'question': meta['question'],
            'true_value': meta['true_value'],
            'pre_earnings': f"{p_pre.pre_earnings:.2f}",
            'post_earnings': f"{p_post.post_earnings:.2f}",
            'pre_bins': get_bins(p_pre.field_maybe_none('pre_beliefs'), labels),
            'post_bins': get_bins(p_post.field_maybe_none('post_beliefs'), labels),
        })

        # ── Task 3: Urn Sample 1 (pre=round3, post=round5) ────────────
        p_pre = player.in_round(3)
        p_post = player.in_round(5)
        labels = json.loads(p_pre.bin_labels)
        meta = question_meta.get(p_pre.qid, {'title': 'Urns Task', 'question': '', 'true_value': 'N/A'})
        task_results.append({
            'title': 'Urns Task — Sample 1',
            'question': meta['question'],
            'true_value': meta['true_value'],
            'pre_earnings': f"{p_pre.pre_earnings:.2f}",
            'post_earnings': f"{p_post.post_earnings:.2f}",
            'pre_bins': get_bins(p_pre.field_maybe_none('pre_beliefs'), labels),
            'post_bins': get_bins(p_post.field_maybe_none('post_beliefs'), labels),
        })

        # ── Task 4: Urn Sample 2 (pre=round4, post=round6) ────────────
        p_pre = player.in_round(4)
        p_post = player.in_round(6)
        labels = json.loads(p_pre.bin_labels)
        meta = question_meta.get(p_pre.qid, {'title': 'Urns Task', 'question': '', 'true_value': 'N/A'})
        task_results.append({
            'title': 'Urns Task — Sample 2',
            'question': meta['question'],
            'true_value': meta['true_value'],
            'pre_earnings': f"{p_pre.pre_earnings:.2f}",
            'post_earnings': f"{p_post.post_earnings:.2f}",
            'pre_bins': get_bins(p_pre.field_maybe_none('pre_beliefs'), labels),
            'post_bins': get_bins(p_post.field_maybe_none('post_beliefs'), labels),
        })

        # ── Task 5: Song 1 (pre=round7, post=round9) ──────────────────
        p_pre = player.in_round(7)
        p_post = player.in_round(9)
        labels = json.loads(p_pre.bin_labels)
        meta = question_meta.get(p_pre.qid, {'title': 'Song Ranking Task', 'question': '', 'true_value': 'N/A'})
        task_results.append({
            'title': 'Song Ranking — Song 1',
            'question': meta['question'],
            'true_value': meta['true_value'],
            'pre_earnings': f"{p_pre.pre_earnings:.2f}",
            'post_earnings': f"{p_post.post_earnings:.2f}",
            'pre_bins': get_bins(p_pre.field_maybe_none('pre_beliefs'), labels),
            'post_bins': get_bins(p_post.field_maybe_none('post_beliefs'), labels),
        })

        # ── Task 6: Song 2 (pre=round8, post=round10) ─────────────────
        p_pre = player.in_round(8)
        p_post = player.in_round(10)
        labels = json.loads(p_pre.bin_labels)
        meta = question_meta.get(p_pre.qid, {'title': 'Song Ranking Task', 'question': '', 'true_value': 'N/A'})
        task_results.append({
            'title': 'Song Ranking — Song 2',
            'question': meta['question'],
            'true_value': meta['true_value'],
            'pre_earnings': f"{p_pre.pre_earnings:.2f}",
            'post_earnings': f"{p_post.post_earnings:.2f}",
            'pre_bins': get_bins(p_pre.field_maybe_none('pre_beliefs'), labels),
            'post_bins': get_bins(p_post.field_maybe_none('post_beliefs'), labels),
        })
        # for i in range(num_rounds):
        #     p = player.in_round(i + 1)
        #     qid = p.qid
        #     meta = question_meta.get(qid, {
        #         'title': f'Task {i + 1}',
        #         'question': '',
        #         'true_value': 'N/A',
        #     })
        #
        #     # Parse pre beliefs tokens
        #     pre_bins = []
        #     post_bins = []
        #     labels = json.loads(p.bin_labels)

            # if p.pre_beliefs:
            #     pre_tokens = json.loads(p.pre_beliefs)
            #     for j, label in enumerate(labels):
            #         tokens = pre_tokens[j] if j < len(pre_tokens) else 0
            #         if tokens > 0:
            #             pre_bins.append({
            #                 'label': label,
            #                 'tokens': tokens
            #             })
            #
            # if p.post_beliefs:
            #     post_tokens = json.loads(p.post_beliefs)
            #     for j, label in enumerate(labels):
            #         tokens = post_tokens[j] if j < len(post_tokens) else 0
            #         if tokens > 0:  # ← only include if tokens > 0
            #             post_bins.append({
            #                 'label': label,
            #                 'tokens': tokens
            #
            #             })

            # # In the task_results loop — replace the post_beliefs section:
            # if p.field_maybe_none('post_beliefs'):
            #     post_tokens = json.loads(p.post_beliefs)
            #     for j, label in enumerate(labels):
            #         tokens = post_tokens[j] if j < len(post_tokens) else 0
            #         if tokens > 0:
            #             post_bins.append({'label': label, 'tokens': tokens})
            #
            # # Same for pre_beliefs:
            # if p.field_maybe_none('pre_beliefs'):
            #     pre_tokens = json.loads(p.pre_beliefs)
            #     for j, label in enumerate(labels):
            #         tokens = pre_tokens[j] if j < len(pre_tokens) else 0
            #         if tokens > 0:
            #             pre_bins.append({'label': label, 'tokens': tokens})

            # task_results.append({
            #     'title': meta['title'],
            #     'question': meta['question'],
            #     'true_value': meta['true_value'],
            #     'pre_earnings': f"{p.pre_earnings:.2f}",
            #     'post_earnings': f"{p.post_earnings:.2f}",
            #     'pre_bins': pre_bins,
            #     'post_bins': post_bins,
            # })

        # ── Performance table ──────────────────────────────────────────
        s = f"""
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th scope="col" class="col-1 text-center">Question</th>
                        <th scope="col" class="text-center">Report</th>
                        <th scope="col" class="col-1 text-center">% Tokens on Correct Bin</th>
                        <th scope="col" class="col-1 text-center">Earnings</th>
                        <th scope="col" class="col-1 text-center">Efficiency</th>
                    </tr>
                </thead>
        """
        sum_pre_earnings = 0
        sum_post_earnings = 0
        sum_efficiency = 0

        # Each tuple: (pre_round, post_round, display_label)
        task_pairs = [
            (1, 1, 'Weight Task'),
            (2, 2, 'Height Task'),
            (3, 5, 'Urns Task — Sample 1'),
            (4, 6, 'Urns Task — Sample 2'),
            (7, 9, 'Song Ranking — Song 1'),
            (8, 10, 'Song Ranking — Song 2'),
        ]

        for pre_r, post_r, label in task_pairs:
            p_pre = player.in_round(pre_r)
            p_post = player.in_round(post_r)

            pre_acc = p_pre.pre_accuracy
            pre_earn = p_pre.pre_earnings
            pre_eff = p_pre.pre_efficiency
            pre_points = round(pre_acc * player.num_tokens, 1)
            sum_pre_earnings += pre_earn
            sum_efficiency += pre_eff

        # for i in range(num_rounds):
        #     p = player.in_round(i+1)
        #
        #     # Get descriptive label for this question
        #     q_label = question_meta.get(p.qid, {}).get('title', p.qid)
        #     #q_label = question_meta.get(p.qid, p.qid)

            # # ── Pre beliefs row ──────────────────────────────────
            # pre_acc = p.pre_accuracy
            # pre_earn = p.pre_earnings
            # pre_eff = p.pre_efficiency
            # pre_points = round(pre_acc * player.num_tokens, 1)  # ← tokens earned
            # sum_pre_earnings += pre_earn
            # sum_efficiency += pre_eff

            s += "<tr>"
            s += f"    <td class='text-center'>{label}</td>"
            s += f"    <td class='text-center'>Report 1 (Before advice)</td>"
            s += f"    <td class='text-center'>{pre_points} pts</td>"
            #s += f"    <td class='text-center'>{round(pre_acc * 100, 2)}%</td>"
            s += f"    <td class='text-center'>${round(pre_earn, 2)}</td>"
            s += f"    <td class='text-center'>{round(pre_eff, 4)}</td>"
            s += "</tr>"

            # # ── Post beliefs row ─────────────────────────────────
            # post_acc = p.post_accuracy
            # post_earn = p.post_earnings
            # post_eff = p.post_efficiency
            # post_points = round(post_acc * player.num_tokens, 1)  # ← tokens earned
            # sum_post_earnings += post_earn
            # sum_efficiency += post_eff

            post_acc = p_post.post_accuracy
            post_earn = p_post.post_earnings
            post_eff = p_post.post_efficiency
            post_points = round(post_acc * player.num_tokens, 1)
            sum_post_earnings += post_earn
            sum_efficiency += post_eff

            s += "<tr class='table-light'>"
            s += f"    <td class='text-center'>{label}</td>"
            s += f"    <td class='text-center'>Report 2 (After advice)</td>"
            s += f"    <td class='text-center'>{post_points} pts</td>"
            #s += f"    <td class='text-center'>{round(post_acc * 100, 2)}%</td>"
            s += f"    <td class='text-center'>${round(post_earn, 2)}</td>"
            s += f"    <td class='text-center'>{round(post_eff, 4)}</td>"
            s += "</tr>"

        total_reports = 12
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

        # ── Random payment selection ───────────────────────────────────────────
        import random as _random

        # All rounds that have actual belief reports
        pre_belief_rounds = [1, 2, 3, 4, 7, 8]
        post_belief_rounds = [1, 2, 5, 6, 9, 10]

        # Build list of all valid (round, report_type) pairs
        all_reports = []
        for r in pre_belief_rounds:
            p_r = player.in_round(r)
            if p_r.field_maybe_none('pre_beliefs'):
                all_reports.append({
                    'round': r,
                    'type': 'pre',
                    'earnings': p_r.pre_earnings,
                    'qid': p_r.qid,
                })

        for r in post_belief_rounds:
            p_r = player.in_round(r)
            if p_r.field_maybe_none('post_beliefs'):
                all_reports.append({
                    'round': r,
                    'type': 'post',
                    'earnings': p_r.post_earnings,
                    'qid': p_r.qid,
                })

        # Use participant code as seed for reproducibility
        rng = _random.Random(player.participant.code)
        selected_report = rng.choice(all_reports)
        selected_earnings = selected_report['earnings']
        selected_label = (
            f"Round {selected_report['round']} — "
            f"{'Report 1 (Before Advice)' if selected_report['type'] == 'pre' else 'Report 2 (After Advice)'} — "
            f"{selected_report['qid']}"
        )

        # ── Payment summary ────────────────────────────────────────────
        participation_fee = C.PARTICIPATION_FEE
        endowment = C.ENDOWMENT

        # Build per-round advice cost breakdown
        advice_breakdown = []

        # Sum advice costs across all rounds
        total_advice_cost = 0
        for i in range(1, num_rounds + 1):
            p = player.in_round(i)
            if p.advice_purchased and p.treatment != 'none':
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

        # ── Grand total calculation ────────────────────────────────────
        endowment_remaining = max(round(endowment - total_advice_cost, 2), 0)
        grand_total = round(
            selected_earnings + participation_fee + endowment_remaining, 2
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
            selected_report_label=selected_label,
            selected_earnings=f"{selected_earnings:.2f}",
        )

# FUNCTIONS

def creating_session(subsession: Subsession):
    questions = subsession.session.config['questions']

    # ── Define question pools ──────────────────────────────────────
    weight_questions = [q for q in questions if q[0].startswith('weight')]
    height_questions = [q for q in questions if q[0].startswith('height')]

    urn_pairs = [
        [q for q in questions if q[0] in ['urn01', 'urn02']],
        [q for q in questions if q[0] in ['urn03', 'urn04']],
        [q for q in questions if q[0] in ['urn05', 'urn06']],
    ]
    urn_pairs = [pair for pair in urn_pairs if len(pair) == 2]

    song_questions = [q for q in questions if q[0].startswith('song')]
    song_pairs = [
        song_questions[i:i + 2]
        for i in range(0, len(song_questions) - 1, 2)
    ]
    song_pairs = [pair for pair in song_pairs if len(pair) == 2]

    for p in subsession.get_players():

        # ── Assign random questions ONCE in round 1 ───────────────
        if subsession.round_number == 1:
            chosen_weight    = random.choice(weight_questions)
            chosen_height    = random.choice(height_questions)
            chosen_urn_pair  = random.choice(urn_pairs)
            chosen_song_pair = random.choice(song_pairs)

            p.participant.vars['chosen_weight'] = chosen_weight[0]
            p.participant.vars['chosen_height'] = chosen_height[0]
            p.participant.vars['chosen_urn1']   = chosen_urn_pair[0][0]
            p.participant.vars['chosen_urn2']   = chosen_urn_pair[1][0]
            p.participant.vars['chosen_song1']  = chosen_song_pair[0][0]
            p.participant.vars['chosen_song2']  = chosen_song_pair[1][0]
        else:
            # In rounds 2-10, read from participant.vars set in round 1
            pass    # participant.vars already set — just read below

        # ── Build round-to-qid map from participant.vars ───────────
        # (safe to read in all rounds since round 1 always runs first)
        round_to_qid = {
            1:  p.participant.vars['chosen_weight'],
            2:  p.participant.vars['chosen_height'],
            3:  p.participant.vars['chosen_urn1'],
            4:  p.participant.vars['chosen_urn2'],
            5:  p.participant.vars['chosen_urn1'],   # ← post urn1
            6:  p.participant.vars['chosen_urn2'],   # ← post urn2
            7:  p.participant.vars['chosen_song1'],
            8:  p.participant.vars['chosen_song2'],
            9:  p.participant.vars['chosen_song1'],  # ← post song1
            10: p.participant.vars['chosen_song2'],  # ← post song2
        }

        chosen_qid = round_to_qid[subsession.round_number]  # ← now always defined

        # ── Find full question data ────────────────────────────────
        question_data = next(q for q in questions if q[0] == chosen_qid)

        p.qid        = str(question_data[0])
        p.bin_labels = json.dumps(question_data[1])
        p.color      = json.dumps(['#6495ED'])
        p.display_round = 1

        layout_input = str(question_data[3]).lower() if len(question_data) > 3 else 'h'
        p.layout = 'h' if layout_input in ['h', 'horizontal'] else 'v'

        p.pre_BLP_draw  = round(random.uniform(0, 100), 2)
        p.post_BLP_draw = round(random.uniform(0, 100), 2)

        # ── Treatment assignment ───────────────────────────────────
        if subsession.round_number == 1:
            p.treatment        = random.choice(['algorithmic', 'human', 'none'])
            p.al_advice_source = random.randint(0, 2)
        else:
            p.treatment        = p.in_round(1).treatment
            p.al_advice_source = p.in_round(1).al_advice_source

        # ── Defaults for none treatment ────────────────────────────
        if p.treatment == 'none':
            p.mpl_response     = json.dumps([-999] * 7)
            p.advice_purchased = False
            p.selected_value   = 0.0
            p.selected_row     = 0

        # ── Defaults for non-MPL rounds ────────────────────────────
        if subsession.round_number not in [1, 2, 4, 8]:
            p.mpl_response   = json.dumps([-999] * 7)
            p.selected_value = 0.0
            p.selected_row   = 0

            if subsession.round_number == 3:
                p.advice_purchased = False
            elif subsession.round_number in [5, 6]:
                p.advice_purchased = p.in_round(4).advice_purchased
            elif subsession.round_number == 7:
                p.advice_purchased = False
            elif subsession.round_number in [9, 10]:
                p.advice_purchased = p.in_round(8).advice_purchased




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

    #player.correct_bin = int(player.session.config['questions'][player.subsession.round_number-1][2]) - 1
    qid = player.qid
    questions = player.session.config['questions']
    question_data = next(q for q in questions if q[0] == qid)
    player.correct_bin = int(question_data[2]) - 1

    # BLP START -----------------------
    # This part of code must handle both BLP and non-BLP cases. For now it is fixed for BLP
    score = round(ScoringRule(player.correct_bin), 2)

    # The following line is for non-BLP
    # player.earnings = score

    # The following lines are for BLP
    if draw <= score:
        earnings = C.MAX_EARNINGS_PER_REPORT
    else:
        earnings = 0
    # BLP END -----------------------

    # response_dict = {f"response_bin{i+1}": response[i] for i in range(min(len(response), 8))}
    # for field, val in response_dict.items():
    #     setattr(player, field, val)

    accuracy = response[player.correct_bin]
    efficiency = earnings / (player.alpha + player.beta)

    return score, earnings, accuracy, efficiency


page_sequence = [Consent, Instructions, Preview_Advice, Task_Intro, Pre_beliefs,  Mpl, Mpl_results, Advice, Post_beliefs, ThankYou, Reveal, Results]
