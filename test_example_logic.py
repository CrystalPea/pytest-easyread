from filetotest import is_it_answer_to_life_universe_and_everything

def test_42_is_answer_to_life_universe_and_everything():
    assert is_it_answer_to_life_universe_and_everything(42) == True

def test_44_is_not_answer_to_life_universe_and_everything():
    assert is_it_answer_to_life_universe_and_everything("love") == False

def test_failing_function():
    assert 0

def test_passing_function():
    assert 1 == 1
