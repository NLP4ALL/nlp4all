from flask import Blueprint
from flask_login import login_required

from nlp4all.controllers import AnalysesController


AnalysesRouter = Blueprint("analyses_controller", __name__)


AnalysesRouter.route("/robot_summary", methods=["GET", "POST"])(
    login_required(AnalysesController.robot_summary)
)
AnalysesRouter.route("/robot", methods=["GET", "POST"])(login_required(AnalysesController.robot))
AnalysesRouter.route("/high_score", methods=["GET", "POST"])(
    login_required(AnalysesController.high_score)
)
AnalysesRouter.route("/shared_analysis_view", methods=["GET", "POST"])(
    login_required(AnalysesController.shared_analysis_view)
)
AnalysesRouter.route("/analysis", methods=["GET", "POST"])(
    login_required(AnalysesController.analysis)
)
AnalysesRouter.route("/matrix/<matrix_id>", methods=["GET", "POST"])(
    login_required(AnalysesController.matrix)
)
AnalysesRouter.route("/matrix_tweets/<matrix_id>", methods=["GET", "POST"])(
    login_required(AnalysesController.matrix_tweets)
)
AnalysesRouter.route("/my_matrices", methods=["GET", "POST"])(
    login_required(AnalysesController.my_matrices)
)
AnalysesRouter.route("/included_tweets/<matrix_id>", methods=["GET", "POST"])(
    login_required(AnalysesController.included_tweets)
)
AnalysesRouter.route("/excluded_tweets/<matrix_id>", methods=["GET", "POST"])(
    login_required(AnalysesController.excluded_tweets)
)
AnalysesRouter.route("/matrix_overview", methods=["GET", "POST"])(
    login_required(AnalysesController.matrix_overview)
)
AnalysesRouter.route("/get_aggregated_data", methods=["GET", "POST"])(
    login_required(AnalysesController.aggregate_matrix)
)
AnalysesRouter.route("/get_matrix_categories", methods=["GET", "POST"])(
    login_required(AnalysesController.get_matrix_categories)
)
AnalysesRouter.route("/get_compare_matrix_data", methods=["GET", "POST"])(
    login_required(AnalysesController.get_compare_matrix_data)
)
AnalysesRouter.route("/compare_matrices", methods=["GET", "POST"])(
    login_required(AnalysesController.compare_matrices)
)
AnalysesRouter.route("/tweet_annotation", methods=["GET", "POST"])(
    login_required(AnalysesController.tweet_annotation)
)
AnalysesRouter.route("/annotation_summary/<analysis_id>", methods=["GET", "POST"])(
    login_required(AnalysesController.annotation_summary)
)
AnalysesRouter.route("/annotations", methods=["GET", "POST"])(
    login_required(AnalysesController.annotations)
)
AnalysesRouter.route("/tweet_annotations", methods=["GET", "POST"])(
    login_required(AnalysesController.tweet_annotations)
)
AnalysesRouter.route("/save_annotation", methods=["GET", "POST"])(
    login_required(AnalysesController.save_annotation)
)
AnalysesRouter.route("/save_draggable_tweet", methods=["GET", "POST"])(
    login_required(AnalysesController.draggable)
)
AnalysesRouter.route("/tweet/<int:id>", methods=["GET"])(login_required(AnalysesController.tweet))
AnalysesRouter.route("/get_bar_chart_data", methods=["GET", "POST"])(
    login_required(AnalysesController.get_bar_chart_data)
)
AnalysesRouter.route("/get_first_tweet", methods=["GET", "POST"])(
    login_required(AnalysesController.get_first_tweet)
)
AnalysesRouter.route("/highlight_tweet/<analysis>", methods=["GET", "POST"])(
    login_required(AnalysesController.highlight_tweet)
)
AnalysesRouter.route("/jq_highlight_tweet", methods=["GET", "POST"])(
    login_required(AnalysesController.jq_highlight_tweet)
)
AnalysesRouter.route("/show_highlights", methods=["GET", "POST"])(
    login_required(AnalysesController.show_highlights)
)
AnalysesRouter.route("/get_annotations", methods=["GET", "POST"])(
    login_required(AnalysesController.get_annotations)
)
AnalysesRouter.route("/delete_last_annotation", methods=["GET", "POST"])(
    login_required(AnalysesController.delete_last_annotation)
)
AnalysesRouter.route("/delete_annotation", methods=["GET", "POST"])(
    login_required(AnalysesController.delete_annotation)
)
AnalysesRouter.route("/precision_recall", methods=["GET", "POST"])(
    login_required(AnalysesController.precision_recall)
)
