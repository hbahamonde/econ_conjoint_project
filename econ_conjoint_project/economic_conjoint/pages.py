from otree.api import Page
from .models import (
    Constants, Subsession, Group, Player,
    assign_positions, candidate_payload, CANDIDATE_DATA,
    get_metric_value, get_metric_label
)


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
        'info_cost_spent',
    ]

    def vars_for_template(self):
        assign_positions(self.player)

        left = candidate_payload(self.player.left_candidate_id)
        right = candidate_payload(self.player.right_candidate_id)

        left_metric = get_metric_value(self.player.left_candidate_id)
        right_metric = get_metric_value(self.player.right_candidate_id)

        if left_metric > right_metric:
            winner_side = 'left'
            winner_id = self.player.left_candidate_id
            winner_metric = left_metric
        else:
            winner_side = 'right'
            winner_id = self.player.right_candidate_id
            winner_metric = right_metric

        return dict(
            round_number=self.round_number,
            total_rounds=Constants.num_rounds,
            left_candidate=left,
            right_candidate=right,
            timed_task=self.player.timed_task,
            base_points=Constants.base_points,
            time_penalty=Constants.time_penalty_per_second,
            info_click_cost=Constants.info_click_cost,
            metric_label=get_metric_label(),
            winner_side=winner_side,
            winner_id=winner_id,
            winner_metric=winner_metric,
        )

    def error_message(self, values):
        if not values.get('decision_candidate_id'):
            return 'Please choose one candidate before continuing.'

    def before_next_page(self):
        left_metric = get_metric_value(self.player.left_candidate_id)
        right_metric = get_metric_value(self.player.right_candidate_id)

        if left_metric > right_metric:
            winning_id = self.player.left_candidate_id
        else:
            winning_id = self.player.right_candidate_id

        self.player.correct = (self.player.decision_candidate_id == winning_id)

        gross_points = 0
        if self.player.correct:
            if self.player.timed_task:
                penalty = int(self.player.time_spent_seconds * Constants.time_penalty_per_second)
                gross_points = max(0, Constants.base_points - penalty)
            else:
                gross_points = Constants.base_points

        net_points = max(0, gross_points - self.player.info_cost_spent)
        self.player.points_earned = net_points

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
            metric_label=get_metric_label(),
        )


page_sequence = [Intro, Task, Summary]