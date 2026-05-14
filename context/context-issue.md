## Issue

=============================================================================================================== FAILURES ================================================================================================================
_____________________________________________________________________________________________ test_chunk_ordering_preserves_original_order ______________________________________________________________________________________________

    def test_chunk_ordering_preserves_original_order() -> None:
        words = [f"word{i}" for i in range(30)]
        text = " ".join(words)
        result = chunk_text(text, max_tokens=5, overlap_tokens=0)
        rejoined = " ".join(chunk["text"] for chunk in result)
>       assert rejoined == text
E       AssertionError: assert 'word0 word1 ...word28 word29' == 'word0 word1 ...word28 word29'
E         
E         - word0 word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12 word13 word14 word15 word16 word17 word18 word19 word20 word21 word22 word23 word24 word25 word26 word27 word28 word29
E         ?                 ^                                                             ^^                                                                    ^^
E         + word0 word1 word 2 word3 word4 word5 word6 word 7 word8 word9 word10 word11 word 12 word13 word14 word15 word16 word 17 word18 word19 word20 word21 word 22 word23 w...
E         
E         ...Full output truncated (2 lines hidden), use '-vv' to show

tests/unit/services/test_chunking.py:34: AssertionError
======================================================================================================== short test summary info ========================================================================================================
FAILED tests/unit/services/test_chunking.py::test_chunk_ordering_preserves_original_order - AssertionError: assert 'word0 word1 ...word28 word29' == 'word0 word1 ...word28 word29'
===================================================================================================== 1 failed, 11 passed in 0.22s ======================================================================================================


