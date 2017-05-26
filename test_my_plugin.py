from conftest import is_it_answer_to_life_universe_and_everything

def test_42_is_answer_to_life_universe_and_everything():
    assert is_it_answer_to_life_universe_and_everything(42) == True

def test_44is_not_answer_to_life_universe_and_everything():
    assert is_it_answer_to_life_universe_and_everything("love") == False
