import librosa, music21, math, numpy as np
from music21 import converter, tempo
from compare_pitch import accuracy_check
from typing import Final

DEFAULT_TEMPO: Final[int] = 120
"""default tempo for a score if no tempo is specified"""

REST_PITCH: Final[float] = float('nan')
"""pitch used to represent rest. A rest doesn't have a pitch, so it is set to impossible value nan"""

HOP_LENGTH: Final[int] = 512
"""hop length of samples corresponding to both the produced expected pitches and generated estimated fundamental frequencies""" 

RIGHT_NOTE_WINDOW: Final[float] = 1
"""window for the user to play the right note in seconds"""

def load_audio(audio_path: str) -> tuple[np.ndarray, int]:
    """Load audio file and it's sample rate"""
    """Returns time-series data and sample_rate of audio file"""
    y: np.ndarray
    sample_rate: int
    y, sample_rate = librosa.load(audio_path, sr=None)
    return y, sample_rate

def get_tempos(score: music21.stream.Score) -> list[tuple[float, int]]:
    """Get tempo in beats per second."""
    tempos = []
    for metronome_mark in score.flatten().getElementsByClass(tempo.MetronomeMark):
        tempos.append((metronome_mark.offset, metronome_mark.number))
        
    # if the tempo is not provided for the score, or the tempo is not provided until mid-way through the music
    if not tempos or tempos[0][0] > 0.0:
        tempos.insert(0, (0.0, DEFAULT_TEMPO))
        print("Using DEFAULT_TEMPO")
    return tempos

def find_expected_pitches(score: music21.stream.Score, tempos_list: list[tuple[float, str]], sample_rate: int, hop_length: int) -> list[float]:
    def extend_pitches(start: float, end: float, pitch: float, tempo: float):
        duration: float = end - start
        samples: int = int((duration / tempo * 60) * sample_rate / hop_length)
        expected_pitches.extend([pitch] * samples)

    expected_pitches: list[float] = []
    note_ptr, tempo_ptr = 0, 0
    cur_beat = 0.0

    # only consider the first part in the score, for now at least
    notes_and_rests = list(score.parts[0].recurse().notesAndRests)

    while note_ptr < len(notes_and_rests):
        note = notes_and_rests[note_ptr]

        note_length: float = note.duration.quarterLength
        next_note_change: float = cur_beat + note_length
        next_tempo_change: float = tempos_list[tempo_ptr + 1][0] if tempo_ptr < len(tempos_list) - 1 else float('inf')

        cur_tempo: int = tempos_list[tempo_ptr][1]
        cur_pitch: float = note.pitch.frequency if note.isNote else REST_PITCH # NOTE: IF IT'S A REST FREQUENCY IS SET TO nan

        extend_pitches(start=cur_beat, end=next_note_change, pitch=cur_pitch, tempo=cur_tempo)
        cur_beat = next_note_change # I belive the only case to watch is when note changes, as tempo only changes on note changes as well (at least in MuseScore)

        # increment next tempo if the tempo change occurs at next note
        if next_tempo_change == next_note_change:
            tempo_ptr += 1
        # always increment to next note
        note_ptr += 1
    
    return expected_pitches

def find_hop_window(sample_rate: int):
    """given any some sample rate, returns the number of hops that the user must play within to be considered "correct\""""
    seconds_per_hop = HOP_LENGTH / sample_rate
    return math.ceil(RIGHT_NOTE_WINDOW / seconds_per_hop)

def use_pyin():
    audio_path = ".\\test_files\\test2.wav"
    sheet_music_path = ".\\test_files\\test2.mxl"

    test_piano_path = ".\\test_files\\775495__tian_yueyao__piano-76.wav"

    score = converter.parse(sheet_music_path)
    print(f"score is ", score)

    y, sample_rate = load_audio(test_piano_path)

    f0: np.ndarray
    voiced_flag: np.ndarray 
    voiced_prob: np.ndarray 

    f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
    
    for i in range(0, len(f0), 4):
        # if voiced_flag[i]:
        print(f"This is the f0 here: {f0[i]}")
        print(f"This is the voiced_flag here: {voiced_flag[i]}")
        print(f"This is the voiced_probs here: {voiced_probs[i]}")

def printNotesInScore():
    audio_path = ".\\test_files\\test2.wav"
    sheet_music_path = ".\\test_files\\test2.mxl"

    score = converter.parse(sheet_music_path)
    for note in score.flatten().notesAndRests:
        if note.isNote:
            freq = note.pitch.frequency
            print(f"Note: {note.nameWithOctave}, Frequency: {freq} Hz")
        else:
            print(f"Rest, Frequency: {REST_PITCH} Hz")
        # print(note)
    
# integrate generating the exepcted pitches and comparing the audio to the expected pitches
def integration(): 
    audio_path = ".\\test_files\\test2.wav"         # USER'S recording as wav file
    y_sample_rate: tuple[np.ndarray, int] = load_audio(audio_path)         # get user recording's sample values and sample rate

    sheet_music_path = ".\\test_files\\test2.mxl"   # sheet music mxl
    score = converter.parse(sheet_music_path)  
    tempos_list: list[tuple[float, int]] = get_tempos(score)
    expected_pitches: list[float] = find_expected_pitches(score=score, tempos_list=tempos_list, sample_rate=y_sample_rate[1], hop_length=HOP_LENGTH)
    f0: np.ndarray = librosa.pyin(y_sample_rate[0], fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'), sr=y_sample_rate[1], hop_length=HOP_LENGTH)
    right_note_hop_window = find_hop_window(y_sample_rate[1])

    # print(f"the size of f0[0] or the frequencies estimated is {len(f0[0])}")
    # print(f"the size of expected_pitches is {len(expected_pitches)}")
    
    print(accuracy_check(f0[0], expected_pitches, right_note_hop_window))

def pitch_check(audio_path: str, sheet_music_path: str) -> None:
    """Given a path to the audio and sheet music, prints the number of times there's an error in playing"""

    y_sample_rate: tuple[np.ndarray, int] = load_audio(audio_path)         # get user recording's sample values and sample rate
    
    score = converter.parse(sheet_music_path)  
    tempos_list: list[tuple[float, int]] = get_tempos(score)
    expected_pitches: list[float] = find_expected_pitches(score=score, tempos_list=tempos_list, sample_rate=y_sample_rate[1], hop_length=HOP_LENGTH)
    f0, voiced_flag, voiced_prob = librosa.pyin(y_sample_rate[0], fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'), sr=y_sample_rate[1], hop_length=HOP_LENGTH)
    right_note_hop_window = find_hop_window(y_sample_rate[1])

    # the indices of user recording (sampled at hop_length intervals) where the wrong note was played
    wrong_i = accuracy_check(f0, expected_pitches, right_note_hop_window, voiced_flag, y_sample_rate[1], HOP_LENGTH)
    for i in wrong_i:
        actual_time = i * (HOP_LENGTH / y_sample_rate[1]) 
        print(f'Wrong note played at time {actual_time}')

def main():
    audio_path = ".\\test_files\\test7.wav"
    sheet_music_path = ".\\test_files\\test7.mxl"

    pitch_check(audio_path=audio_path, sheet_music_path=sheet_music_path)
            
if __name__ == "__main__":
    main()