"""One adapter per baseline: raw output text, app, side -> the run object the scorer reads."""
from access_review.adapters import advisors, pgrls, rlsautotest, semgrep

ADAPTERS = {"semgrep": semgrep.adapt, "advisors": advisors.adapt, "rlsautotest": rlsautotest.adapt,
            "pgrls": pgrls.adapt}
