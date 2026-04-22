from otree.api import Page
from .models import Constants, Subsession, Group, Player
from .models import assign_positions, candidate_payload, CANDIDATE_DATA

class Intro(Page):
    def is_displayed(self):
        return self.round_number == 1


class Task(Page):
    form_model = 'player'
    form_fields = [
        'left_info_opened',
        'right_info_opened',
        'decision_candidate_id',
        'decision_side',
        'time_spent_seconds',
    ]

    def vars_for_template(self):
        assign_positions(self.player)

        left = candidate_payload(self.player.left_candidate_id)
        right = candidate_payload(self.player.right_candidate_id)

        return dict(
            round_number=self.round_number,
            total_rounds=Constants.num_rounds,
            left_candidate=left,
            right_candidate=right,
            timed_task=self.player.timed_task,
            base_points=Constants.base_points,
            time_penalty=Constants.time_penalty_per_second,
        )

    def error_message(self, values):
        if not values.get('decision_candidate_id'):
            return 'Please choose one candidate before continuing.'

    def before_next_page(self):
        left_votes = CANDIDATE_DATA[self.player.left_candidate_id]['votes']
        right_votes = CANDIDATE_DATA[self.player.right_candidate_id]['votes']

        if left_votes > right_votes:
            winning_id = self.player.left_candidate_id
        else:
            winning_id = self.player.right_candidate_id

        self.player.correct = (self.player.decision_candidate_id == winning_id)

        if self.player.correct:
            if self.player.timed_task:
                penalty = int(self.player.time_spent_seconds * Constants.time_penalty_per_second)
                self.player.points_earned = max(0, Constants.base_points - penalty)
            else:
                self.player.points_earned = Constants.base_points
        else:
            self.player.points_earned = 0

        total_points = self.player.participant.vars.get('economic_conjoint_points', 0)
        self.player.participant.vars['economic_conjoint_points'] = total_points + self.player.points_earned


class Summary(Page):
    def is_displayed(self):
        return self.round_number == Constants.num_rounds

    def vars_for_template(self):
        rounds = self.player.in_all_rounds()
        return dict(
            rounds=rounds,
            total_points=self.player.participant.vars.get('economic_conjoint_points', 0),
            timed_round=self.player.participant.vars.get('timed_round'),
        )


page_sequence = [Intro, Task, Summary]