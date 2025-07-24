from pytest import raises
from project import prompt_parse_and_run, extract_date, verify_date, verify_location

def test_prompt_parse_and_run_incorrect_usage():
    with raises(SystemExit):
        prompt_parse_and_run("", "2025-05-07", "2025-05-09")
        prompt_parse_and_run("New York", "", "2025-05-09")
        prompt_parse_and_run("New York", 0, "2025-05-09")
        prompt_parse_and_run("New York", 0, 0)
        prompt_parse_and_run("New York", "2025-04-29")
        prompt_parse_and_run("New York", "2025-05-07", "2025-05-10")

def test_extract_date_correct():
    assert extract_date("2025-05-07") == (2025,5,7)
    assert extract_date("2025-5-7") == (2025,5,7)

def test_extract_date_incorrect():
    assert extract_date("2025--07") == None
    assert extract_date("2025-5") == None
    assert extract_date("") == None
    assert extract_date("-05-07") == None

def test_verify_location_correct():
    assert verify_location("New York") == True
    assert verify_location("New Delhi") == True
    assert verify_location("Rome") == True
    assert verify_location("Paris") == True

def test_verify_location_incorrect():
    assert verify_location("") == False
    assert verify_location(" ") == False
    assert verify_location("987") == False
    assert verify_location(";[]'.") == False

def test_verify_date_correct():
    assert verify_date("2025-05-07") == True
    assert verify_date("2025-5-7") == True

def test_verify_date_incorrect():
    assert verify_date("07-05-2025") == False
    assert verify_date("") == False
    assert verify_date(" ") == False
    assert verify_date("987") == False

