import librosa, math
REST_PITCH: float = float('nan') # pitch used to represent rest. A rest doesn't have a pitch, so it is set to impossible value nan

def similar(a_freq: float, b_freq: float):
    #if one is resting but not the other, then not similar
    if math.isnan(a_freq) != math.isnan(b_freq):
        return False
    
    #if they're both resting, they're similar
    elif math.isnan(a_freq) and math.isnan(b_freq): 
        return True
    
    # if neither are resting then evaluate pitch
    else:
        a_bef_f: float = librosa.midi_to_hz(round(librosa.hz_to_midi(a_freq) - 1))
        a_next_f: float = librosa.midi_to_hz(round(librosa.hz_to_midi(a_freq) + 1))

        delta_coeff = .5 # what percent you must be close to the note above or below to be considered similar 
        lower_bound: float = a_freq - ((a_freq - a_bef_f) * delta_coeff)
        upper_bound: float = a_freq + ((a_next_f - a_freq) * delta_coeff)

        return lower_bound <= b_freq <= upper_bound

# compares the sample frequencies of user and expected, returns the number of times they significantly differ (for now, at least)
def accuracy_check(user, expected: list[float], right_note_hop_window: int, voiced_flag, sr: int, hop_length: int) -> list[int]:

    # if the user's is 95% or shorter than the original length, the user didn't record until the end
    # if len(user) < .95 * len(expected): 
    #     print("user's is 95% or shorter than the original length, the user didn't record until the end")
    #     return (int(.95 * (len(expected) - len(user))))
    
    ret = [] # for now just how many times the pitches significantly differ
    n: int = min(len(user), len(expected))

    for i in range(n):
        if not voiced_flag[i]: # if the recording is not voiced
            user[i] = math.nan
        if not similar(user[i], expected[i]):
            if not any(similar(user[j], expected[i]) for j in range(max(i - right_note_hop_window, 0), min(i + right_note_hop_window + 1, n))):
                ret.append(i)

    return ret