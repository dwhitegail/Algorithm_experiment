import json
import random
from otree.api import *

doc = """
Human Advice Collection Experiment
Collects belief distributions from subjects to use as human advice
in the main algorithmic aversion experiment.
No performance-based payment — flat $40 participation fee.
"""


class C(BaseConstants):
    NAME_IN_URL = 'human_advice'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 18              #5 weight + 5 height + 2 urns + 5 songs
    PARTICIPATION_FEE = 10
    ENDOWMENT = 0.00            # no endowment needed — no advice to buy
    MAX_EARNINGS_PER_REPORT = 50

    # Which rounds belong to each task
    WEIGHT_ROUNDS = [1, 2, 3, 4, 5]
    HEIGHT_ROUNDS = [6, 7, 8, 9, 10]
    URN_ROUNDS = [11, 12]
    SONG_ROUNDS_SHORT = [13, 14, 15, 16, 17] # sessions 1 and 2
    SONG_ROUNDS_LONG = [13, 14, 15, 16, 17, 18] #session 3

    # First round of each task — show Task_Intro
    TASK_INTRO_ROUNDS = [1, 6, 11, 13]


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    qid          = models.StringField()
    alpha        = models.FloatField(initial=50.0)
    beta         = models.FloatField(initial=50.0)
    num_tokens   = models.IntegerField(initial=100)
    color        = models.StringField()
    bin_labels   = models.StringField()
    layout       = models.StringField(initial='h')
    beliefs      = models.StringField()    # single belief report per question
    score        = models.FloatField(initial=0)
    earnings     = models.FloatField(initial=0)
    accuracy     = models.FloatField(initial=0)
    efficiency = models.FloatField(initial=0)

    BLP_draw = models.FloatField(initial=-1)
    correct_bin = models.IntegerField(initial=-1)


# ── PAGES ──────────────────────────────────────────────────────────────────

class Consent(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1


class Instructions(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        # Calculate song count dynamically from session config
        questions = player.session.config['questions']
        num_songs = len(questions) - len(C.WEIGHT_ROUNDS) - len(C.HEIGHT_ROUNDS) - len(C.URN_ROUNDS)

        return dict(
            num_tokens=player.num_tokens,
            participation_fee=f"{C.PARTICIPATION_FEE:.0f}",
            max_earnings=f"{C.MAX_EARNINGS_PER_REPORT:.0f}",
            num_weight=len(C.WEIGHT_ROUNDS),
            num_height=len(C.HEIGHT_ROUNDS),
            num_urns=len(C.URN_ROUNDS),
            num_songs=num_songs,  # ← dynamic, not C.SONG_ROUNDS
            total_questions=len(questions),  # ← dynamic, not C.NUM_ROUNDS
            #num_songs=len(C.SONG_ROUNDS),
            #total_questions=C.NUM_ROUNDS,

        )


class Task_Intro(Page):
    @staticmethod
    def is_displayed(player):
        # Show before first round of each task
        # weight=1, height=2, urns=3, songs=5
        return player.round_number in C.TASK_INTRO_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        questions = player.session.config['questions']
        num_songs = len(questions) - 12  # total minus weight(5)+height(5)+urns(2)

        intros = {
            1: {
                'task_number': 'Task 1 of 4',
                'task_name':   'Weight Reporting Beliefs about Weight',
                'icon':        '⚖️',
                'num_questions': len(C.WEIGHT_ROUNDS),
                'intro': (
                    "In this task, you will view photographs of "
                    f"<strong>{len(C.WEIGHT_ROUNDS)} different people</strong> "
                    "and report your beliefs about their weight in pounds (lbs.). For each photograph, "
                    "place the tokens in the bin or bins that you think represents the correct answer(s). "
                    "Bin 1 represents a weight of less than 120 lbs., bin 2 represents an interval of 120-129 lbs., bin 3, 130-139 lbs, and so on. "
                    "Bin 10 represents the interval of greater than or equal to 200 lbs."
                ),
                'note': (
                    "Consider the person's visible body type, posture, height cues, "
                    "and clothing before allocating your tokens. If you are more familiar with calculating weight using "
                    "kilograms (kg), the conversion guide is 1 pound (lb.) ≈ 0.45 kilogram (kg) and 1 kilogram (kg.) ≈ 2.2 pounds (lbs.)."
                ),
                'Expectations': [
                    f"You will observe <strong>{len(C.WEIGHT_ROUNDS)} photographs</strong> of individuals, one at a time.",
                    "For each photograph you will be asked to report your beliefs  about the weight in <strong>pounds (lbs.)</strong> by allocating <strong>100 tokens across 10 bins.</strong>",
                    "The weight intervals are from <strong>less than 120 lbs</strong> to <strong>greater than or equal to  200 lbs</strong>.",

                ],
            },
            6: {
                'task_number': 'Task 2 of 4',
                'task_name':   'Reporting Beliefs about Height',
                'icon':        '📏',
                'num_questions': len(C.HEIGHT_ROUNDS),
                'intro': (
                    "In this task you will view photographs of "
                    f"<strong>{len(C.HEIGHT_ROUNDS)} different people</strong> and report your beliefs about their height in feet and inches. "
                    "As before, distribute your tokens across the height intervals to reflect your beliefs. "
                    "Bin 1 represents a height of less than 5 feet, bin 2 represents an interval from 5 feet to 5 feet, 2 inches, and so on. "
                    "Bin 10 represents the interval of greater than or equal to 7 feet."
                ),
                'note': (
                    "Look for contextual cues in the photo, surrounding "
                    "objects, posture, and proportions can all help you gauge height." 
                    "For example, the height interval <strong>5'0\" - 5'2\"</strong> represents 5 feet 0 inches to 5 feet 2 inches. "
                    "If you are more familiar with calculating height using centimeters (cm), the conversion guide is "
                    "1 foot ≈ 30.48 centimeters (cm) and 1 inch ≈ 2.54 cm. Recall that 12 inches = 1 foot."
                ),
                'Expectations': [
                    f"You will see <strong>{len(C.HEIGHT_ROUNDS)} photographs</strong>, one at a time.",
                    "For each photo, report your beliefs about their heights in <strong>feet and inches</strong> across 10 bins.",
                    "The height intervals are from <strong>Under 5 feet (5'0\")</strong> to <strong>Over 7 feet (7'0\")</strong>.",

                ],
            },
            11: {
                'task_number': 'Task 3 of 4',
                'task_name':   'Urns Task',
                'icon':        '🏺',
                'num_questions': len(C.URN_ROUNDS),
                'intro': (
                    "An urn contains exactly <strong>100 balls</strong>. Each ball is either "
                    "<strong>blue</strong> or <strong>orange</strong>. "
                    "You do not know how many of each color are inside the urn. "
                    "Because there are exactly 100 balls, the <strong>percentage</strong> of blue balls "
                    "is exactly equal to the actual <strong>number</strong> of blue balls. "
                    "So if you think there are 30 blue balls then the percentage of blue balls in the urn is 30%."
                    "<br><br>"
                    
                    "You will be given <strong>2 samples of 20 draws each</strong>. "
                    "A <strong>sample</strong> is just a small peek inside the urn. "
                    "Your role is to use each sample to report your beliefs about the total percentage of "
                    "<strong>blue balls</strong> in the full urn. "
                    "First, you will <strong>observe a 20-draw sample,</strong> report your beliefs, "
                    "and then <strong>observe a second 20-draw sample</strong> from the exact <strong>same urn</strong> before reporting your beliefs again."

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
            13: {
                'task_number': 'Task 4 of 4',
                'task_name':   'Billboard Hot 100 Song Ranking',
                'icon':        '🎵',
                'num_questions': num_songs,
                'intro': (
                    f"In this task, you will be asked to report your beliefs about the ranking of "f"<strong>{num_songs} songs on the Billboard Hot 100 "
                    "chart </strong>for the weeks of <strong>March 29, 2025 and August 30, 2025.</strong> For each song, you will be "
                    "shown its chart performance over the <strong>four preceding weeks.</strong> "
                    "As in the other tasks, you will report your beliefs by distributing tokens across "
                    "possible ranking bins. Bin 1 corresponds to the song being ranked #1 for that week! "
                    "Bin 2 corresponds to the song being ranked  #2 for that week and so on. Bin 10 represents that the song placed 10th "
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
            'task_name':   '',
            'icon':        '📋',
            'num_questions': 0,
            'intro':       'Please proceed.',
            'note':        '',
            'Expectations': [],
        })

        return dict(
            task_number=info['task_number'],
            task_name=info['task_name'],
            icon=info['icon'],
            num_questions=info['num_questions'],
            intro=info['intro'],
            note=info['note'],
            Expectations=info['Expectations'],
        )


class Beliefs(Page):
    form_model  = 'player'
    form_fields = ['beliefs']
    template_name = 'human_advice/Beliefs.html'

    @staticmethod
    def is_displayed(player):
        questions = player.session.config['questions']
        # Only show if there is a question for this round
        return player.round_number <= len(questions)  # ← handles 17 vs 18 rounds

    @staticmethod
    def before_next_page(player, timeout_happened):
        response = json.loads(player.beliefs)
        score, earnings, accuracy, efficiency = score_response(
            player, response, player.BLP_draw)
        player.score    = score
        player.earnings = earnings
        player.accuracy = accuracy
        player.efficiency = efficiency
        player.payoff += earnings

    @staticmethod
    def vars_for_template(player: Player):

        r = player.round_number
        questions = player.session.config['questions']

        # Calculate song rounds dynamically
        song_rounds = list(range(13, len(questions) + 1))

        if r in C.WEIGHT_ROUNDS:
            task_label = "Weight Estimation"
            q_num = C.WEIGHT_ROUNDS.index(r) + 1
            q_total = len(C.WEIGHT_ROUNDS)
        elif r in C.HEIGHT_ROUNDS:
            task_label = "Height Estimation"
            q_num = C.HEIGHT_ROUNDS.index(r) + 1
            q_total = len(C.HEIGHT_ROUNDS)
        elif r in C.URN_ROUNDS:
            task_label = "Urns Task"
            q_num = C.URN_ROUNDS.index(r) + 1
            q_total = len(C.URN_ROUNDS)
        else:
            task_label = "Song Ranking"
            q_num = song_rounds.index(r) + 1
            q_total = len(song_rounds)


        return dict(
            qid=player.qid,
            stimulus_path=f"shared_stimulus/{player.qid}.html",
            alpha=player.alpha,
            beta=player.beta,
            num_tokens=player.num_tokens,
            color=json.loads(player.color),
            bin_labels=json.loads(player.bin_labels),
            task_label=task_label,
            q_num=q_num,
            q_total=q_total,
            display_round=1,
        )


class ThankYou(Page):
    @staticmethod
    def is_displayed(player):
        questions = player.session.config['questions']
        return player.round_number == len(questions)  # ← handles 17 vs 18 rounds

        #return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            participation_fee=f"{C.PARTICIPATION_FEE:.2f}",
        )


class Payoff(Page):
    @staticmethod
    def is_displayed(player):
        questions = player.session.config['questions']
        return player.round_number == len(questions)

    @staticmethod
    def vars_for_template(player: Player):
        questions = player.session.config['questions']
        num_rounds = len(questions)

        question_meta = {
            'weight01': {'title': 'Weight Task',  'true_value': '170–179 lbs'},
            'weight02': {'title': 'Weight Task',  'true_value': "<120 pounds"},
            'weight03': {'title': 'Weight Task',  'true_value': '120–129 lbs'},
            'weight04': {'title': 'Weight Task',  'true_value': '140–149 lbs'},
            'weight05': {'title': 'Weight Task',  'true_value': "≥200 pounds"},
            'weight06': {'title': 'Weight Task',  'true_value': "≥200 pounds"},
            'weight07': {'title': 'Weight Task',  'true_value': '170–179 lbs'},
            'weight08': {'title': 'Weight Task',  'true_value': '130–139 lbs'},
            'weight09': {'title': 'Weight Task',  'true_value': '150–159 lbs'},
            'weight10': {'title': 'Weight Task',  'true_value': '170–179 lbs'},
            'weight11': {'title': 'Weight Task',  'true_value': "≥200 pounds"},
            'weight12': {'title': 'Weight Task',  'true_value': '160–169 lbs'},
            'weight13': {'title': 'Weight Task',  'true_value': '160–169 lbs'},
            'weight14': {'title': 'Weight Task',  'true_value': '160–169 lbs'},
            'weight15': {'title': 'Weight Task',  'true_value': '160–169 lbs'},
            'height01': {'title': 'Height Task',  'true_value': "< 5 feet"},
            'height02': {'title': 'Height Task', 'true_value': "5 feet 11 inches"},
            'height03': {'title': 'Height Task', 'true_value': "5 feet 4 inches"},
            'height04': {'title': 'Height Task', 'true_value': "5 feet 5 inches"},
            'height05': {'title': 'Height Task', 'true_value': "5 feet 6 inches"},
            'height06': {'title': 'Height Task', 'true_value': "5 feet 6 inches"},
            'height07': {'title': 'Height Task', 'true_value': "5 feet 8 inches"},
            'height08': {'title': 'Height Task', 'true_value': "5 feet 10 inches"},
            'height09': {'title': 'Height Task',  'true_value': "6 feet 0 inches"},
            'height10': {'title': 'Height Task', 'true_value': "6 feet 0 inches"},
            'height11': {'title': 'Height Task', 'true_value': "< 5 feet"},
            'height12': {'title': 'Height Task', 'true_value': "6 feet 1 inch"},
            'height13': {'title': 'Height Task', 'true_value': "6 feet 1 inch"},
            'height14': {'title': 'Height Task', 'true_value': "6 feet 3 inches"},
            'height15': {'title': 'Height Task', 'true_value': "5 feet 7 inches"},
            'urn01': {'title': 'Urns — Period 1', 'true_value': '55% blue balls'},
            'urn02': {'title': 'Urns — Period 2', 'true_value': '55% blue balls'},
            'urn03': {'title': 'Urns — Period 1', 'true_value': '36% blue balls'},
            'urn04': {'title': 'Urns — Period 2', 'true_value': '36% blue balls'},
            'urn05': {'title': 'Urns — Period 1', 'true_value': '23% blue balls'},
            'urn06': {'title': 'Urns — Period 2', 'true_value': '23% blue balls'},
            'urn07': {'title': 'Urns — Period 1', 'true_value': '42% blue balls'},
            'urn08': {'title': 'Urns — Period 2', 'true_value': '42% blue balls'},
            'song01': {'title': 'Song Ranking Task: Daisies by Justin Bieber', 'true_value': 'Position 8'},
            'song02': {'title': 'Song Ranking Task: Ordinary by Alex Warren',  'true_value': 'Position 2'},
            'song03': {'title': 'Song Ranking Task: Not Like Us by Kendrick Lamar', 'true_value': 'Position 8'},
            'song04': {'title': 'Song Ranking Task: Golden by HUNTR/X: EJAE, Audrey Nuna & REI AMI', 'true_value': 'Position 1'},
            'song05': {'title': 'Song Ranking Task: Lose Control by Teddy Swims', 'true_value': 'Position 7'},
            'song06': {'title': 'Song Ranking Task: Just in Case by Morgan Wallen', 'true_value': 'Position 9'},
            'song07': {'title': 'Song Ranking Task: A Bar Song (Tipsy) by Shaboozey', 'true_value': 'Position 10'},
            'song08': {'title': 'Song Ranking Task: What I Want by Morgan Wallen ft. Tate McRae', 'true_value': 'Position 3'},
            'song09': {'title': 'Song Ranking Task: Soda Pop by Saja Boys', 'true_value': 'Position 5'},
            'song10': {'title': 'Song Ranking Task: Luther by Kendrick Lamar', 'true_value': 'Position 10'},
            'song11': {'title': 'Song Ranking Task: Die with a smile by Lady Gaga & Bruno Mars', 'true_value': 'Position 10'},
            'song12': {'title': 'Song Ranking Task: Your Idol by Saja Boys', 'true_value': 'Position 4'},
            'song13': {'title': 'Song Ranking Task: Love Me Not by Ravyn Lenae', 'true_value': 'Position 6'},
            'song14': {'title': 'Song Ranking Task: Birds of a Feather by Billie Ellish ', 'true_value': 'Position 7'},
            'song15': {'title': 'Song Ranking Task: APT by ROSE and Bruno Mars', 'true_value': 'Position 10'},
            'song16': {'title': 'Song Ranking Task: TV OFF by Kendrick Lamar', 'true_value': 'Position 10'},

        }

        task_results = []
        for i in range(1, num_rounds + 1):
            p = player.in_round(i)
            meta = question_meta.get(p.qid, {'title': p.qid, 'true_value': 'N/A'})
            labels = json.loads(p.bin_labels)

            bins = []
            if p.beliefs:
                tokens = json.loads(p.beliefs)
                for j, label in enumerate(labels):
                    t = tokens[j] if j < len(tokens) else 0
                    if t > 0:
                        bins.append({'label': label, 'tokens': t})

            task_results.append({
                'round': i,
                'title':      meta['title'],
                'true_value': meta['true_value'],
                'earnings':   f"{p.earnings:.2f}",
                'bins':       bins,
                'qid': p.qid,
            })


        # ── Randomly select ONE round for payment ──────────────────
        # Use participant label as seed so it's consistent if page reloads
        import random as _random
        rng = _random.Random(player.participant.code)
        selected_round = rng.randint(1, num_rounds)
        selected_player = player.in_round(selected_round)
        selected_earnings = selected_player.earnings
        selected_title = question_meta.get(
            selected_player.qid, {'title': selected_player.qid}
        )['title']

        participation_fee = C.PARTICIPATION_FEE
        grand_total = round(selected_earnings + participation_fee, 2)

        return dict(
            task_results=task_results,
            selected_round=selected_round,
            selected_title=selected_title,
            selected_earnings=f"{selected_earnings:.2f}",
            participation_fee=f"{participation_fee:.2f}",
            grand_total=f"{grand_total:.2f}",
        )


# ── FUNCTIONS ──────────────────────────────────────────────────────────────

def creating_session(subsession: Subsession):
    questions = subsession.session.config['questions']

    if subsession.round_number <= len(questions):
        for p in subsession.get_players():
            question_data = questions[subsession.round_number - 1]
            p.qid        = str(question_data[0])
            p.bin_labels = json.dumps(question_data[1])
            p.color      = json.dumps(['#6495ED'])

            layout_input = str(question_data[3]).lower() if len(question_data) > 3 else 'h'
            p.layout = 'h' if layout_input in ['h', 'horizontal'] else 'v'

            p.BLP_draw = round(random.uniform(0, 100), 2)


def score_response(player: Player, response, draw):
    num_bins = len(response)
    for i in range(num_bins):
        response[i] = response[i] / player.num_tokens

    def ScoringRule(cb):
        SS = sum(r * r for r in response)
        return player.alpha + player.beta * ((2 * response[cb]) - SS)

    player.correct_bin = int(
        player.session.config['questions'][player.subsession.round_number - 1][2]
    ) - 1

    score    = round(ScoringRule(player.correct_bin), 2)
    earnings = C.MAX_EARNINGS_PER_REPORT if draw <= score else 0
    accuracy  = response[player.correct_bin]
    efficiency = earnings / (player.alpha + player.beta)

    return score, earnings, accuracy, efficiency


# ── PAGE SEQUENCE ──────────────────────────────────────────────────────────
page_sequence = [
    Consent,
    Instructions,
    Task_Intro,
    Beliefs,
    ThankYou,
    Payoff
]