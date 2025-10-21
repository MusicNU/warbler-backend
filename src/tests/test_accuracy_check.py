from compare_pitch import accuracy_check

def test_accuracy_check():
    assert(accuracy_check([415.30, 19.45, 43.65, 43.65], [430.30, 19.45, 43.65, 43.65]) == 1)
        
test_accuracy_check()