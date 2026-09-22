from app.api.documents import split_text


def test_short_text_returns_single_chunk():
    chunks = split_text("This is a short sentence.")
    assert len(chunks) == 1
    assert chunks[0] == "This is a short sentence."


def test_empty_text_returns_no_chunks():
    assert split_text("") == []
    assert split_text("   ") == []


def test_long_text_is_split_into_multiple_chunks():
    long_text = "word " * 1000  # ~5000 chars, well over the 900-char chunk size
    chunks = split_text(long_text, size=900, overlap=120)
    assert len(chunks) > 1


def test_consecutive_chunks_overlap():
    long_text = "sentence number {}. ".format
    text = "".join(long_text(i) for i in range(200))
    chunks = split_text(text, size=900, overlap=120)
    assert len(chunks) > 1
    # the tail of one chunk should reappear at the start of the next,
    # since that's the whole point of overlap (context isn't lost at
    # a chunk boundary)
    tail_of_first = chunks[0][-30:]
    assert any(tail_of_first[:15] in chunk for chunk in chunks[1:])


def test_no_chunk_is_empty():
    long_text = "word " * 500
    chunks = split_text(long_text)
    assert all(chunk.strip() for chunk in chunks)
