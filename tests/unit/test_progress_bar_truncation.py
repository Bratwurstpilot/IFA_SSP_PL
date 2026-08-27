# Finding #16: der Fortschrittsbalken-Schrittwert wird per int()-Division berechnet, was bei
# grossen total-Werten (z.B. total=4001) zu einem Schritt von 0 fuehrt -- der Balken stockt dann
# sichtbar, bricht aber nicht ab (rein kosmetisch, geringe Prioritaet laut Audit).
def test_progress_step_ratio_truncates_to_zero_for_large_totals():
    total = 4001
    offset = 100
    progressbar_step_ratio = int(40 / (total / offset)) / 100
    assert progressbar_step_ratio == 0.0


def test_progress_step_ratio_is_nonzero_for_small_totals():
    total = 200
    offset = 100
    progressbar_step_ratio = int(40 / (total / offset)) / 100
    assert progressbar_step_ratio > 0.0
