"""Analyses routes"""

from flask import Blueprint
from flask_login import login_required

from ..controllers import AnalysesController


AnalysesRouter = Blueprint("analyses_controller", __name__)


@AnalysesRouter.before_request
@login_required
def before_request():
    """ Protect all of the analyses endpoints."""


AnalysesRouter.route("/robot_summary", methods=["GET", "POST"])(
    AnalysesController.robot_summary
)
AnalysesRouter.route("/robot", methods=["GET", "POST"])(AnalysesController.robot)
AnalysesRouter.route("/high_score", methods=["GET", "POST"])(
    AnalysesController.high_score
)
AnalysesRouter.route("/shared_analysis_view", methods=["GET", "POST"])(
    AnalysesController.shared_analysis_view
)
AnalysesRouter.route("/analysis", methods=["GET", "POST"])(
    AnalysesController.analysis
)
AnalysesRouter.route("/matrix/<matrix_id>", methods=["GET", "POST"])(
    AnalysesController.matrix
)
AnalysesRouter.route("/matrix_tweets/<matrix_id>", methods=["GET", "POST"])(
    AnalysesController.matrix_tweets
)
AnalysesRouter.route("/my_matrices", methods=["GET", "POST"])(
    AnalysesController.my_matrices
)
AnalysesRouter.route("/included_tweets/<matrix_id>", methods=["GET", "POST"])(
    AnalysesController.included_tweets
)
AnalysesRouter.route("/excluded_tweets/<matrix_id>", methods=["GET", "POST"])(
    AnalysesController.excluded_tweets
)
AnalysesRouter.route("/matrix_overview", methods=["GET", "POST"])(
    AnalysesController.matrix_overview
)
AnalysesRouter.route("/get_aggregated_data", methods=["GET", "POST"])(
    AnalysesController.aggregate_matrix
)
AnalysesRouter.route("/get_matrix_categories", methods=["GET", "POST"])(
    AnalysesController.get_matrix_categories
)
AnalysesRouter.route("/get_compare_matrix_data", methods=["GET", "POST"])(
    AnalysesController.get_compare_matrix_data
)
AnalysesRouter.route("/compare_matrices", methods=["GET", "POST"])(
    AnalysesController.compare_matrices
)
AnalysesRouter.route("/tweet_annotation", methods=["GET", "POST"])(
    AnalysesController.data_annotation
)
AnalysesRouter.route("/annotation_summary/<analysis_id>", methods=["GET", "POST"])(
    AnalysesController.annotation_summary
)
AnalysesRouter.route("/annotations", methods=["GET", "POST"])(
    AnalysesController.annotations
)
AnalysesRouter.route("/tweet_annotations", methods=["GET", "POST"])(
    AnalysesController.data_annotations
)
AnalysesRouter.route("/save_annotation", methods=["GET", "POST"])(
    AnalysesController.save_annotation
)
AnalysesRouter.route("/save_draggable_tweet", methods=["GET", "POST"])(
    AnalysesController.draggable
)
AnalysesRouter.route("/tweet/<int:id>", methods=["GET"])(AnalysesController.tweet)
AnalysesRouter.route("/get_bar_chart_data", methods=["GET", "POST"])(
    AnalysesController.get_bar_chart_data
)
AnalysesRouter.route("/get_first_tweet", methods=["GET", "POST"])(
    AnalysesController.get_first_tweet
)
AnalysesRouter.route("/highlight_tweet/<analysis>", methods=["GET", "POST"])(
    AnalysesController.highlight_tweet
)
AnalysesRouter.route("/jq_highlight_tweet", methods=["GET", "POST"])(
    AnalysesController.jq_highlight_tweet
)
AnalysesRouter.route("/show_highlights", methods=["GET", "POST"])(
    AnalysesController.show_highlights
)
AnalysesRouter.route("/get_annotations", methods=["GET", "POST"])(
    AnalysesController.get_annotations
)
AnalysesRouter.route("/delete_last_annotation", methods=["GET", "POST"])(
    AnalysesController.delete_last_annotation
)
AnalysesRouter.route("/delete_annotation", methods=["GET", "POST"])(
    AnalysesController.delete_annotation
)
AnalysesRouter.route("/precision_recall", methods=["GET", "POST"])(
    AnalysesController.precision_recall
)
