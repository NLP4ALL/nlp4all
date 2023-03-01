"""Database and models for NLP4ALL."""

# The files that have a _model suffix for some reason
# seem to error out on github when they do not have an underscore
# this is totally bizarre and I don't like having inconsistent names
# so if it's fixed, any of the files with _model suffix can be renamed
from .bayesian_robot import BayesianRobotModel as BayesianRobotModel
from .bayesian_analysis import BayesianAnalysisModel as BayesianAnalysisModel
from .confusion_matrix import ConfusionMatrixModel as ConfusionMatrixModel
from .data_source import DataSourceModel as DataSourceModel
from .data_model import DataModel as DataModel
from .user_group import UserGroupModel as UserGroupModel
from .project_model import ProjectModel as ProjectModel
from .role_model import RoleModel as RoleModel
from .data_annotation import DataAnnotationModel as DataAnnotationModel
from .data_tag import DataTagModel as DataTagModel
from .data_tag_category import DataTagCategoryModel as DataTagCategoryModel
from .user_model import UserModel as UserModel
from .user_model import load_user as load_user
