def test_subtag(test_tag):
    test_tag.remove_subtag(2)
    test_tag.remove_subtag(2)

    test_tag.add_subtag(5)
    # repeated add should not add the subtag
    test_tag.add_subtag(5)
    assert test_tag.subtag_ids == [3, 4, 5]
