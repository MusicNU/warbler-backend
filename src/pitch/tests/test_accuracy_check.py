from ..compare_pitch import accuracy_check

def test_accuracy_check():
    user = [440.00, 19.45, 43.65, 43.65]
    expected = [430.30, 19.45, 43.65, 43.65]  
    voiced_flag = [True] * len(user)
    assert(accuracy_check(user=user, expected=expected, right_note_hop_window=4, voiced_flag=voiced_flag, sr=44100, hop_length=512) == [])