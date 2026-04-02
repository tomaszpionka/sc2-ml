import logging
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import RandomizedSearchCV
from scipy.stats import randint
from config import RANDOM_SEED, TUNING_N_ITER, TUNING_CV_FOLDS

logger = logging.getLogger(__name__)


def tune_random_forest(X_train: pd.DataFrame, y_train: pd.Series) -> RandomForestClassifier:
    """Run RandomizedSearchCV to find optimal Random Forest hyperparameters.

    Searches TUNING_N_ITER random combinations over the defined parameter space
    using TUNING_CV_FOLDS-fold cross-validation. Returns the best fitted estimator.
    """
    logger.info("Starting Random Forest hyperparameter tuning...")

    param_dist = {
        "n_estimators": randint(100, 500),         # Number of trees
        "max_depth": [5, 8, 12, 15, None],          # Maximum tree depth
        "min_samples_split": randint(2, 20),         # Minimum samples required to split a node
        "min_samples_leaf": randint(1, 10),          # Minimum samples in leaf (regularisation)
        "max_features": ["sqrt", "log2"],            # Features considered per split
    }

    rf = RandomForestClassifier(random_state=RANDOM_SEED)

    random_search = RandomizedSearchCV(
        estimator=rf,
        param_distributions=param_dist,
        n_iter=TUNING_N_ITER,
        cv=TUNING_CV_FOLDS,
        scoring="accuracy",
        n_jobs=-1,
        random_state=RANDOM_SEED,
        verbose=1,
    )

    random_search.fit(X_train, y_train)

    logger.info(f"Best parameters: {random_search.best_params_}")
    logger.info(f"Best CV accuracy: {random_search.best_score_:.4f}")

    return random_search.best_estimator_
