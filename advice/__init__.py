from otree.api import *
import json
import csv
import random
import settings


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'advice'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 16
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
            DEBUG=settings.DEBUG,
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
        return player.round_number in [1, 2, 5, 6, 9, 10, 13, 14]


    @staticmethod
    def before_next_page(player, timeout_happened):
        response = json.loads(player.pre_beliefs)
        score, earnings, accuracy, efficiency = score_response(player, response, player.pre_BLP_draw)
        player.pre_score = score
        player.pre_earnings = earnings
        player.pre_accuracy = accuracy
        player.pre_efficiency = efficiency

        # ── Add earnings to player.payoff ONLY if selected ─────────────────
        if player.round_number == player.participant.vars.get('selected_round'):
            player.payoff = earnings
        else:
            player.payoff = 0

        # If this is the last round, add the remaining endowment
        if player.round_number == C.NUM_ROUNDS:
            total_advice_cost = 0
            for r in range(1, C.NUM_ROUNDS + 1):
                p_r = player.in_round(r)
                if p_r.advice_purchased:
                    total_advice_cost += p_r.selected_value
            endowment_remaining = max(C.ENDOWMENT - total_advice_cost, 0)
            player.payoff += endowment_remaining

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
            endowment=f"{C.ENDOWMENT:.0f}",
            DEBUG=settings.DEBUG,
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
                "Algorithmic advice for the height, weight and urn and song tasks was generated by <strong>"
                "Google Gemini Pro 3.0, Claude Sonnet 4.6 and ChatGPT 5.5.</strong> "
                "You will <strong>randomly</strong> receive advice <strong>from one</strong> of these three models "


            )
        else:
            advice_type = "Human Advice"
            advice_description = (
                "This advice is based on the aggregated average "
                "of 30 other subjects like you who completed this task "
                "in a previous study."
            )


            # # treatment == 'none'
            # advice_type = "No Advice"
            # advice_description = (
            #     "You have not been selected to receive advice for this experiment. "
            #     "Please proceed to update your beliefs based on your own judgment."
            # )

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
        mpl_rounds = [2, 6, 10, 14]
        return player.round_number in mpl_rounds #and player.treatment != 'none'


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
        #if player.treatment != 'none':
        response = json.loads(player.mpl_response)
        num_rows = len(response)
        selected_row_idx = random.randint(0, num_rows - 1)

        # This line transforms the selected row into the monetary amount shown in the selected row.
        player.selected_value = selected_row_idx * .25 + 1
        player.selected_row = selected_row_idx

        # In MyPage: 0 = L (purchase advice), 1 = R (do not purchase)
        player.advice_purchased = (response[selected_row_idx] == 0)

        #else:
            # Set defaults for no advice treatment
           # player.mpl_response = json.dumps([-999] * 7)
           # player.advice_purchased = False
           # player.selected_value = 0.0
           # player.selected_row = 0


class Advice(Page):
    form_model = 'player'

    # def is_displayed(player):
    #     # Show advice on same rounds as MPL if purchased
    #     mpl_rounds = [2, 6, 10, 14]
    #     # Only show if advice was purchased AND treatment is NOT 'none'
    #     return (
    #         player.round_number in mpl_rounds
    #         and player.advice_purchased
    #         #and player.treatment != 'none'
    #
    #     )

    @staticmethod
    def is_displayed(player):
        # Show advice on MPL round AND the round immediately after
        # BUT only if advice was purchased on the MPL round of this task
        advice_rounds = {
            2:  2,   # weight task MPL round
            3:  2,   # weight task carry-over → check round 2 for purchase
            6:  6,   # height task MPL round
            7:  6,   # height task carry-over → check round 6
            10: 10,  # urn task MPL round
            11: 10,  # urn task carry-over → check round 10
            14: 14,  # song task MPL round
            15: 14,  # song task carry-over → check round 14
        }
        r = player.round_number
        if r not in advice_rounds:
            return False
        mpl_round = advice_rounds[r]
        purchased = player.in_round(mpl_round).advice_purchased
        return purchased


    @staticmethod
    def vars_for_template(player: Player):
        # Route to correct intervention based on treatment
        suffix = 'AL' if player.treatment == 'algorithmic' else 'H'

        qid = player.qid

        # Song titles lookup
        song_titles = {
            'song01': 'Daisies — Justin Bieber',
            'song02': 'Ordinary — Alex Warren',
            'song03': 'Love Me Not — Ravyn Lenae',
            'song04': 'Golden — HUNTR/X',
            'song05': 'Lose Control — Teddy Swims',
            'song06': 'Just In Case — Morgan Wallen',
            'song07': 'A Bar Song (Tipsy) — Shaboozey',
            'song08': 'What I Want — Morgan Wallen ft. Tate McRae',
            'song09': 'Soda Pop — Saja Boys',
            'song10': 'Luther — Kendrick Lamar & SZA',
            'song11': 'Die With A Smile — Lady Gaga & Bruno Mars',
            'song12': 'Your Idol — Saja Boys',
            'song13': 'Not Like Us — Kendrick Lamar',
            'song14': 'Birds of a Feather — Billie Eilish',
            'song15': 'APT. — ROSÉ and Bruno Mars',
            'song16': 'TV OFF — Kendrick Lamar ft. Lefty Gunplay',
        }

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

        # ── Label so subject knows which question this advice is for ──
        task_labels = {
            2: 'Weight Task — Photo 1',
            3: 'Weight Task — Photo 2',
            6: 'Height Task — Photo 1',
            7: 'Height Task — Photo 2',
            10: 'Urns Task — Sample 1',
            11: 'Urns Task — Sample 2',
            14: 'Song Ranking — Song 1',
            15: 'Song Ranking — Song 2',
        }
        advice_label = task_labels.get(player.round_number, '')

        return dict(
            advice_path=advice_path,
            treatment=player.treatment,
            al_advice_source=player.al_advice_source,  # ← pass index to template
            qid=player.qid,
            song_title=song_title,
            advice_label=advice_label,
        )


class Post_beliefs(Page):
    form_model = 'player'
    form_fields = ['post_beliefs']
    template_name = 'advice/Beliefs.html'

    @staticmethod
    def is_displayed(player):
        # Post-beliefs on the last two rounds of each task
        return player.round_number in [3, 4, 7, 8, 11, 12, 15, 16]

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

        # ── Add earnings to player.payoff ONLY if selected ─────────────────
        if player.round_number == player.participant.vars.get('selected_round'):
            player.payoff = earnings
        else:
            player.payoff = 0

        # If this is the last round, add the remaining endowment
        if player.round_number == C.NUM_ROUNDS:
            total_advice_cost = 0
            for r in range(1, C.NUM_ROUNDS + 1):
                p_r = player.in_round(r)
                if p_r.advice_purchased:
                    total_advice_cost += p_r.selected_value
            endowment_remaining = max(C.ENDOWMENT - total_advice_cost, 0)
            player.payoff += endowment_remaining

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
            endowment=f"{C.ENDOWMENT:.0f}",
            DEBUG=settings.DEBUG,
        )


class ResultsWaitPage(WaitPage):
    pass


class Task_Intro(Page):

    @staticmethod
    def is_displayed(player):
        # Only show before the FIRST pre-beliefs of each task
        return player.round_number in [1, 5, 9, 13]

    @staticmethod
    def vars_for_template(player: Player):

        intros = {
            1: {
                'task_number': 'Task 1 of 4',
                'task_name': 'Reporting Beliefs about Weight',
                'icon': '⚖️',
                'intro': (
                    "In this task, you will view <strong>2 photographs</strong> of "
                    "real people and asked to report your beliefs about their weight in pounds. "
                    "You will allocate <strong>100 tokens</strong> across a range of weight intervals in <strong>10 bins</strong>. " 
                    "Place the tokens in the bin or bins that you think represents the correct answer(s). "
                    "Bin 1 represents a weight of less than 120 lbs., bin 2 represents an interval of 120-129 lbs., bin 3, 130-139 lbs, and so on. "
                    "Bin 10 represents the interval of greater than or equal to 200 lbs."
                    " The more tokens you place in the correct bin, the higher your potential earnings. Think carefully, "
                    "every token counts!"
                ),
                'note': (
                    "Note: Consider each person's visible body type and height cues before allocating your tokens. "
                    "If you are more familiar with calculating weight using kilograms (kg), the conversion guide is"
                    " 1 pound (lb.) = 0.45 kilogram (kg) and 1 kilogram (kg.) = 2.2 pounds (lbs.)"
                ),


                'Expectations': [
                    "You will observe <strong>2 photographs</strong> of 2 different people.",
                    "You will be asked to report your beliefs  about the weight in <strong>pounds (lbs.)</strong> by allocating <strong>100 tokens across 10 bins.</strong>",
                    "The weight intervals are from <strong>less than 120 lbs</strong> to <strong>greater than or equal to  200 lbs</strong>.",
                    "Each report pays up to <strong>${}</strong> based on accuracy.".format(C.MAX_EARNINGS_PER_REPORT),
                    "You may <strong>purchase advice</strong> between round 1 and round 2 if selected to receive advice.",

                ],
            },

            5: {
                'task_number': 'Task 2 of 4',
                'task_name': 'Reporting Beliefs about Height',
                'icon': '📏',
                'intro': (
                    "In this task, you will view <strong>2 photographs</strong> of real people and "
                    "report your beliefs about their height in feet and inches. You will express your beliefs by distributing <strong>100 tokens across 10 bins</strong> of successive height "
                    "intervals. "
                    "Bin 1 represents a height of less than 5 feet, bin 2 represents an interval from 5 feet (5'0\") to 5 feet, 2 inches (5'2\"), and so on. "
                    "Bin 10 represents the interval of greater than or equal to 7 feet. "
                    "Take your time and observe the photo carefully before making your allocations."
                ),
                'note': (
                    "Note: Look for contextual cues in the photos — surroundings "
                    "objects, posture, and proportions can all help you gauge height. "
                    "If you are more familiar with calculating height using centimeters (cm), the conversion guide is "
                    "1 foot ≈ 30.48 centimeters (cm) and 1 inch = 2.54 cm. Recall that 12 inches = 1 foot. "

                ),

                'Expectations': [
                    "You will be asked to report your beliefs about the height in <strong>feet and inches</strong> of <strong>2 people</strong>.",
                    "The height intervals are from <strong>Under 5 feet (5'0\")</strong> to <strong>Greater than or Equal to 7 feet (7'0\")</strong>.",
                    "Each report pays up to <strong>${}</strong> based on accuracy.".format(C.MAX_EARNINGS_PER_REPORT),
                    "You may <strong>purchase advice</strong> between Round 1 and Round 2 if selected to receive advice.",

                ],
            },
            9: {
                'task_number': 'Task 3 of 4',
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
                    "The draws are with replacement"

                ),
                'note': (
                    "A <strong>draw with replacement</strong> means one ball is randomly selected from the urn, its color "
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
            13: {
                'task_number': 'Task 4 of 4',
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
        mpl_rounds = [2, 6, 10, 14]
        return player.round_number in mpl_rounds #and player.treatment != 'none'

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


class SelectedRound(Page):
    template_name = 'advice/SelectedRound.html'

    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        selected_round = player.participant.vars['selected_round']
        selected_player = player.in_round(selected_round)

        is_pre = selected_round in [1, 2, 5, 6, 9, 10, 13, 14]
        beliefs_str = selected_player.pre_beliefs if is_pre else selected_player.post_beliefs
        beliefs = json.loads(beliefs_str) if beliefs_str else []

        return dict(
            display_round=selected_round,
            total_questions=C.NUM_ROUNDS,
            stimulus_path=f"shared_stimulus/{selected_player.qid}.html",
            bin_labels=json.loads(selected_player.bin_labels),
            correct_bin=selected_player.correct_bin,
            beliefs_json=json.dumps(beliefs),
            num_tokens=selected_player.num_tokens,
            alpha=selected_player.alpha,
            beta=selected_player.beta,
            endowment=f"{C.ENDOWMENT:.0f}",
        )

class Payoff(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        selected_round = player.participant.vars['selected_round']
        selected_player = player.in_round(selected_round)

        is_pre = selected_round in [1, 2, 5, 6, 9, 10, 13, 14]
        beliefs_str = selected_player.pre_beliefs if is_pre else selected_player.post_beliefs
        beliefs = json.loads(beliefs_str) if beliefs_str else [0] * 10
        
        tokens_allocated = int(beliefs[selected_player.correct_bin]) if selected_player.correct_bin >= 0 else 0
        score = selected_player.pre_score if is_pre else selected_player.post_score
        draw = selected_player.pre_BLP_draw if is_pre else selected_player.post_BLP_draw
        earnings = int(selected_player.pre_earnings if is_pre else selected_player.post_earnings)

        # Advice costs
        total_advice_cost = 0
        for r in range(1, C.NUM_ROUNDS + 1):
            p = player.in_round(r)
            if p.advice_purchased:
                total_advice_cost += p.selected_value

        endowment_remaining = max(round(C.ENDOWMENT - total_advice_cost, 2), 0)
        total_earnings = earnings + C.PARTICIPATION_FEE + endowment_remaining

        bin_labels = json.loads(selected_player.bin_labels)
        correct_answer = bin_labels[selected_player.correct_bin] if selected_player.correct_bin >= 0 else "N/A"

        return dict(
            selected_round=selected_round,
            correct_answer=correct_answer,
            num_tokens=selected_player.num_tokens,
            tokens_allocated=tokens_allocated,
            score=score,
            draw=draw,
            earnings=earnings,
            task_earnings=earnings,
            participation_fee=C.PARTICIPATION_FEE,
            endowment_remaining=endowment_remaining,
            total_earnings=total_earnings,
            tplural='' if tokens_allocated == 1 else 's',
            splural='' if score == 1.0 else 's',
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

    song_pair_ids = [
        ['song01', 'song02'], ['song03', 'song04'], ['song05', 'song06'],
        ['song07', 'song08'], ['song09', 'song10'], ['song11', 'song12'],
        ['song13', 'song14'], ['song15', 'song16'],
    ]
    song_pairs = []
    for pair_ids in song_pair_ids:
        pair = [q for q in questions if q[0] in pair_ids]
        if len(pair) == 2:
            pair.sort(key=lambda q: q[0])
            song_pairs.append(pair)

    # song_questions = [q for q in questions if q[0].startswith('song')]
    # song_pairs = [
    #     song_questions[i:i + 2]
    #     for i in range(0, len(song_questions) - 1, 2)
    # ]
    # song_pairs = [pair for pair in song_pairs if len(pair) == 2]

    for p in subsession.get_players():

        # ── Assign random questions ONCE in round 1 ───────────────
        if subsession.round_number == 1:
            chosen_weight    = random.sample(weight_questions, 2)
            chosen_height    = random.sample(height_questions, 2)
            chosen_urn_pair  = random.choice(urn_pairs)
            chosen_song_pair = random.choice(song_pairs)

            p.participant.vars['chosen_weight1'] = chosen_weight[0][0]
            p.participant.vars['chosen_weight2'] = chosen_weight[1][0]
            p.participant.vars['chosen_height1'] = chosen_height[0][0]
            p.participant.vars['chosen_height2'] = chosen_height[1][0]
            p.participant.vars['chosen_urn1']   = chosen_urn_pair[0][0]
            p.participant.vars['chosen_urn2']   = chosen_urn_pair[1][0]
            p.participant.vars['chosen_song1']  = chosen_song_pair[0][0]
            p.participant.vars['chosen_song2']  = chosen_song_pair[1][0]

            # ── Select round for payment ──
            import random as _random
            rng = _random.Random(p.participant.code)
            # Pick one round from all 16 rounds (each round has 1 report)
            p.participant.vars['selected_round'] = rng.randint(1, 16)
        # else:
        #     # In rounds 2-10, read from participant.vars set in round 1
        #     pass    # participant.vars already set — just read below
        #
        # # ── Build round-to-qid map from participant.vars ───────────
        # # (safe to read in all rounds since round 1 always runs first)

            # ── Treatment: algorithmic or human only ───────────────
            p.treatment = random.choice(['algorithmic', 'human'])
            p.al_advice_source = random.randint(0, 2)

        else:
            p.treatment = p.in_round(1).treatment
            p.al_advice_source = p.in_round(1).al_advice_source
        round_to_qid = {
            1: p.participant.vars['chosen_weight1'],
            2: p.participant.vars['chosen_weight2'],
            3: p.participant.vars['chosen_weight1'],  # post
            4: p.participant.vars['chosen_weight2'],  # post
            5: p.participant.vars['chosen_height1'],
            6: p.participant.vars['chosen_height2'],
            7: p.participant.vars['chosen_height1'],  # post
            8: p.participant.vars['chosen_height2'],  # post
            9: p.participant.vars['chosen_urn1'],
            10: p.participant.vars['chosen_urn2'],
            11: p.participant.vars['chosen_urn1'],  # post
            12: p.participant.vars['chosen_urn2'],  # post
            13: p.participant.vars['chosen_song1'],
            14: p.participant.vars['chosen_song2'],
            15: p.participant.vars['chosen_song1'],  # post
            16: p.participant.vars['chosen_song2'],  # post
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

        # # ── Treatment assignment ───────────────────────────────────
        # if subsession.round_number == 1:
        #     p.treatment        = random.choice(['algorithmic', 'human'])
        #     p.al_advice_source = random.randint(0, 2)
        # else:
        #     p.treatment        = p.in_round(1).treatment
        #     p.al_advice_source = p.in_round(1).al_advice_source

        # ── Defaults for none treatment ────────────────────────────
        #if p.treatment == 'none':
        #    p.mpl_response     = json.dumps([-999] * 7)
         #   p.advice_purchased = False
         #   p.selected_value   = 0.0
        #    p.selected_row     = 0

        # ── Defaults for non-MPL rounds ────────────────────────────
        if subsession.round_number not in [2, 6, 10, 14]:
            p.mpl_response   = json.dumps([-999] * 7)
            p.selected_value = 0.0
            p.selected_row   = 0

            if subsession.round_number == 1:
                p.advice_purchased = False  # weight pre 1 — MPL not yet
            elif subsession.round_number in [3, 4]:
                p.advice_purchased = p.in_round(2).advice_purchased  # weight post
            elif subsession.round_number == 5:
                p.advice_purchased = False  # height pre 1 — MPL not yet
            elif subsession.round_number in [7, 8]:
                p.advice_purchased = p.in_round(6).advice_purchased  # height post
            elif subsession.round_number == 9:
                p.advice_purchased = False  # urn pre 1 — MPL not yet
            elif subsession.round_number in [11, 12]:
                p.advice_purchased = p.in_round(10).advice_purchased  # urn post
            elif subsession.round_number == 13:
                p.advice_purchased = False  # song pre 1 — MPL not yet
            elif subsession.round_number in [15, 16]:
                p.advice_purchased = p.in_round(14).advice_purchased  # song post


def score_response(player: Player, response, draw):
    # response = json.loads(player.pre_beliefs)
    num_bins = len(response)
    for i in range(num_bins):
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


page_sequence = [Consent, Instructions, Preview_Advice, Task_Intro, Pre_beliefs,  Mpl, Mpl_results, Advice, Post_beliefs, ThankYou, SelectedRound, Payoff]
