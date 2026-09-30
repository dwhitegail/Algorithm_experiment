from otree.api import *
from urllib.parse import quote

doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'survey'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    pass

# PAGES

class SurveyIntro(Page):
    pass


class Qualtrics(Page):

    @staticmethod
    def vars_for_template(player):
        participant_code = player.participant.code
        session_code = player.session.code
        qualtrics_base_url = player.session.config['qualtrics_url']
        full_url_to_qualtrics = (
            f"{qualtrics_base_url}"
            f"?session_code={session_code}"
            f"&participant_code={participant_code}"
        )

        return {
            'full_url_to_qualtrics': full_url_to_qualtrics
        }


class SurveyOutro(Page):
    pass


page_sequence = [SurveyIntro, Qualtrics,]
