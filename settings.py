from os import environ

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00,
    participation_fee=10.00,
    doc="",
)

PARTICIPANT_FIELDS = [
    'risk_payoff_round',
    'risk_payoff',
]

SESSION_FIELDS = [
]

SESSION_CONFIGS = [
    dict(
        name = "risk_piechart",
        language = 'english',
        display_name = 'Standard Risk',
        num_demo_participants= 3,
        app_sequence= ['risk'],
        risk_sample_sizes= [2],
        # # params format: [ qid, [[L#1,...,L#n] , [L$1,...,L$n]] , [[R#1,...,R#n] , [R$1,...,R$n]]],
        # # 'params':   [ [ ['testq1', [[3, 7, 10], [11, 22, 33]], [[8, 2, 10], [5, 33, 25]]],
        # #                ['testq2', [[5, 5, 10], [8, 15, 25]],  [[10, 1, 10],   [11, 22, 33]]] ] ]
        risk_params = [
           [
               ['instructions_1', [[40, 0, 60], [5, 10, 15]], [[50, 40, 10], [5, 10, 15]]],
               ['instructions_2', [[0, 50, 50, 0], [0, 6, 11, 21]], [[50, 0, 0, 50], [0, 6, 11, 21], [0, 0, 0, 1]]],
               # ['ls10_lr', [[50, 0, 50], [10, 30, 50]], [[10, 80, 10], [10, 30, 50]]],
               # ['ls13', [[70, 0, 30], [10, 30, 50]], [[50, 40, 10], [10, 30, 50]]],
               # ['ls13i_lr', [[55, 30, 15], [10, 30, 50]], [[65, 10, 25], [10, 30, 50]]],
               # ['ls15', [[50, 40, 10], [10, 30, 50]], [[40, 60, 0], [10, 30, 50]]],
               # ['ls16i_lr', [[88, 4, 8], [10, 30, 50]], [[83, 14, 3], [10, 30, 50]]],
               # ['ls17_lr', [[10, 0, 90], [10, 30, 50]], [[0, 25, 75], [10, 30, 50]]],
               # ['ls17i_rl', [[4, 15, 81], [10, 30, 50]], [[8, 5, 87], [10, 30, 50]]],
               # ['ls18', [[40, 0, 60], [10, 30, 50]], [[10, 75, 15], [10, 30, 50]]],
               # ['ls18i_rl', [[14, 65, 21], [10, 30, 50]], [[38, 5, 57], [10, 30, 50]]],
               # ['ls1i_lr', [[12, 5, 83], [10, 30, 50]], [[3, 20, 77], [10, 30, 50]]],
               # ['ls2_lr', [[30, 0, 70], [10, 30, 50]], [[15, 25, 60], [10, 30, 50]]],
               # ['ls21_lr', [[70, 0, 30], [10, 30, 50]], [[60, 25, 15], [10, 30, 50]]],
               # ['ls22i_lr', [[66, 10, 24], [10, 30, 50]], [[54, 40, 6], [10, 30, 50]]],
               # ['ls26', [[40, 0, 60], [10, 30, 50]], [[20, 60, 20], [10, 30, 50]]],
               # ['ls28i_rl', [[12, 84, 4], [10, 30, 50]], [[18, 66, 16], [10, 30, 50]]],
               # ['ls29', [[60, 0, 40], [10, 30, 50]], [[50, 30, 20], [10, 30, 50]]],
               # ['ls30i_rl', [[45, 45, 10], [10, 30, 50]], [[55, 15, 30], [10, 30, 50]]],
               # ['ls31i_lr', [[48, 36, 16], [10, 30, 50]], [[42, 54, 4], [10, 30, 50]]],
               # ['ls32_rl', [[70, 30, 0], [10, 30, 50]], [[80, 0, 20], [10, 30, 50]]],
               # ['ls34', [[25, 0, 75], [10, 30, 50]], [[10, 60, 30], [10, 30, 50]]],
               # ['ls35', [[25, 0, 75], [10, 30, 50]], [[0, 100, 0], [10, 30, 50]]],
               # ['ls35i_lr', [[20, 20, 60], [10, 30, 50]], [[10, 60, 30], [10, 30, 50]]],
               # ['ls36i_rl', [[2, 92, 6], [10, 30, 50]], [[8, 68, 24], [10, 30, 50]]],
               # ['ls37i_lr', [[48, 28, 24], [10, 30, 50]], [[44, 44, 12], [10, 30, 50]]],
               # ['ls39', [[55, 0, 45], [10, 30, 50]], [[50, 20, 30], [10, 30, 50]]],
               # ['ls3i_lr', [[27, 5, 68], [10, 30, 50]], [[3, 45, 52], [10, 30, 50]]],
               # ['ls6_lr', [[60, 0, 40], [10, 30, 50]], [[0, 100, 0], [10, 30, 50]]],
               # ['ls7_lr', [[60, 0, 40], [10, 30, 50]], [[15, 75, 10], [10, 30, 50]]],
               # ['ls7i_lr', [[54, 10, 36], [10, 30, 50]], [[18, 70, 12], [10, 30, 50]]],
               # ['ls9i_lr', [[8, 4, 88], [10, 30, 50]], [[5, 10, 85], [10, 30, 50]]],
               # ['rae1', [[50, 50, 0], [0, 10, 20]], [[75, 0, 25], [0, 10, 20]]],
               # ['rae10', [[0, 75, 25], [0, 35, 70]], [[50, 0, 50], [0, 35, 70]]],
               # ['rae11', [[0, 100, 0], [0, 20, 70]], [[25, 50, 25], [0, 20, 70]]],
               # ['rae12', [[0, 75, 25], [0, 35, 70]], [[25, 0, 75], [0, 35, 70]]],
               # ['rae13', [[25, 75, 0], [0, 10, 35]], [[75, 0, 25], [0, 10, 35]]],
               # ['rae14', [[0, 75, 25], [0, 20, 35]], [[25, 0, 75], [0, 20, 35]]],
               # ['rae15', [[0, 75, 25], [0, 20, 70]], [[25, 0, 75], [0, 20, 70]]],
               # ['rae2', [[0, 100, 0], [0, 10, 20]], [[75, 0, 25], [0, 10, 20]]],
               # ['rae3', [[0, 100, 0], [0, 10, 35]], [[50, 25, 25], [0, 10, 35]]],
               # ['rae4', [[25, 75, 0], [0, 10, 70]], [[50, 0, 50], [0, 10, 70]]],
               # ['rae5', [[0, 100, 0], [0, 10, 70]], [[50, 0, 50], [0, 10, 70]]],
               # ['rae6', [[0, 100, 0], [0, 20, 35]], [[25, 25, 50], [0, 20, 35]]],
               # ['rae7', [[0, 50, 50], [0, 20, 70]], [[25, 0, 75], [0, 20, 70]]],
               # ['rae8', [[0, 100, 0], [0, 35, 70]], [[25, 0, 75], [0, 35, 70]]],
               # ['rae9', [[25, 50, 25], [0, 20, 70]], [[50, 0, 50], [0, 20, 70]]],
               # ['rdon1', [[50, 50, 0], [0, 10, 20]], [[50, 50, 0], [0, 10, 20], [0, 1, 0]]],
               # ['rdon10', [[0, 75, 25], [0, 35, 70]], [[0, 100, 0], [0, 35, 70], [0, 1, 0]]],
               # ['rdon11', [[0, 100, 0], [0, 20, 70]], [[0, 50, 50], [0, 20, 35], [0, 0, 1]]],
               # ['rdon12', [[0, 75, 25], [0, 35, 70]], [[0, 50, 50], [0, 35, 70], [0, 1, 0]]],
               # ['rdon13', [[25, 75, 0], [0, 10, 35]], [[50, 50, 0], [0, 17.5, 35], [0, 1, 0]]],
               # ['rdon14', [[0, 75, 25], [0, 20, 35]], [[0, 50, 50], [0, 17.5, 35], [0, 1, 0]]],
               # ['rdon15', [[0, 75, 25], [0, 20, 70]], [[0, 50, 50], [0, 35, 70], [0, 1, 0]]],
               # ['rdon2', [[0, 100, 0], [0, 10, 20]], [[50, 50, 0], [0, 10, 20], [0, 1, 0]]],
               # ['rdon3', [[0, 100, 0], [0, 10, 35]], [[0, 50, 50], [0, 5, 17.5], [0, 1, 1]]],
               # ['rdon4', [[25, 75, 0], [0, 10, 70]], [[0, 100, 0], [0, 35, 70], [0, 1, 0]]],
               # ['rdon5', [[0, 100, 0], [0, 10, 70]], [[0, 100, 0], [0, 35, 70], [0, 1, 0]]],
               # ['rdon6', [[0, 100, 0], [0, 20, 35]], [[0, 50, 50], [0, 10, 35], [0, 1, 0]]],
               # ['rdon7', [[0, 50, 50], [0, 20, 70]], [[0, 50, 50], [0, 35, 70], [0, 1, 0]]],
               # ['rdon8', [[0, 100, 0], [0, 35, 70]], [[0, 50, 50], [0, 35, 70], [0, 1, 0]]],
               # ['rdon9', [[0, 50, 50], [0, 20, 35], [0, 0, 1]], [[50, 0, 50], [0, 20, 70]]],
           ]
        ],
    ),

    dict(
        name='raven_3questions',
        display_name="First 3 questions from RAPM Set 2 (for testing results page with more than 1 question)",
        app_sequence=['raven_interface'],
        num_demo_participants=1,
        questions=[
            ['raven_set2_q1', 8, 5],
            ['raven_set2_q2', 8, 1],
            ['raven_set2_q3', 8, 7],
        ]
    ),
    dict(
        name='raven_interface',
        display_name="RAPM Set 2 (36 questions)",
        app_sequence=['raven_interface'],
        num_demo_participants=1,
        questions=[
            ['raven_set2_q1', 8, 5],
            ['raven_set2_q2', 8, 1],
            ['raven_set2_q3', 8, 7],
            ['raven_set2_q4', 8, 4],
            ['raven_set2_q5', 8, 3],
            ['raven_set2_q6', 8, 1],
            ['raven_set2_q7', 8, 6],
            ['raven_set2_q8', 8, 1],
            ['raven_set2_q9', 8, 8],
            ['raven_set2_q10', 8, 4],
            ['raven_set2_q11', 8, 5],
            ['raven_set2_q12', 8, 6],
            ['raven_set2_q13', 8, 2],
            ['raven_set2_q14', 8, 1],
            ['raven_set2_q15', 8, 2],
            ['raven_set2_q16', 8, 4],
            ['raven_set2_q17', 8, 6],
            ['raven_set2_q18', 8, 7],
            ['raven_set2_q19', 8, 3],
            ['raven_set2_q20', 8, 8],
            ['raven_set2_q21', 8, 8],
            ['raven_set2_q22', 8, 7],
            ['raven_set2_q23', 8, 6],
            ['raven_set2_q24', 8, 3],
            ['raven_set2_q25', 8, 7],
            ['raven_set2_q26', 8, 2],
            ['raven_set2_q27', 8, 7],
            ['raven_set2_q28', 8, 5],
            ['raven_set2_q29', 8, 6],
            ['raven_set2_q30', 8, 5],
            ['raven_set2_q31', 8, 4],
            ['raven_set2_q32', 8, 8],
            ['raven_set2_q33', 8, 5],
            ['raven_set2_q34', 8, 1],
            ['raven_set2_q35', 8, 3],
            ['raven_set2_q36', 8, 2],
        ]

    ),

]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']



# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'en'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = False

ROOMS = [
    dict(
        name='lab',
        display_name='lab',
        participant_label_file='_rooms/lab.txt',
    ),
    # dict(
    #     name='econ101',
    #     display_name='Econ 101 class',
    #     participant_label_file='_rooms/econ101.txt',
    # ),
    # dict(name='live_demo', display_name='Room for live demo (no participant labels)'),
]

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """
Here are some oTree games.
"""


SECRET_KEY = '4720801523770'

INSTALLED_APPS = ['otree']




# import os
# import dj_database_url

# if os.environ.get('DATABASE_URL'):
#     DATABASES = {
#         'default': dj_database_url.config(
#             # Heroku recommends this setting for persistent connections
#             conn_max_age=600
#         )
#     }
